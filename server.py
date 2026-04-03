"""FastAPI server exposing endpoints for Figma fetch/cache and test generation."""

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, Optional, List
import json
import asyncio

from app.services.figma_client import FigmaClient
from app.services.cache_manager import CacheManager
from app.services.test_generator import TestGenerator
from app.services.feedback_manager import save_run_snapshot, new_run_id, load_run_snapshot
from app.models.database import TestCaseType
from app.services import Evaluator
from app.services.document_parser import DocumentParser
from app.services.prd_analyzer import analyze_prd
from fastapi import UploadFile, File, Form, Request, Body
import tempfile
import os
import re


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


cache_manager = CacheManager()


class FigmaFetchRequest(BaseModel):
    fileUrlOrId: str
    token: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class FigmaFetchResponse(BaseModel):
    cacheId: str
    fileId: str
    screensCount: int


class AnalyzeRequest(BaseModel):
    cacheId: str
    prdText: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class GenerateRequest(BaseModel):
    cacheId: str
    screenId: str
    testType: Optional[str] = "functional"
    testCount: Optional[int] = 5
    prefer_premium: Optional[bool] = False
    prdText: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    generateAll: Optional[bool] = False


@app.post("/api/figma/fetch-cache", response_model=FigmaFetchResponse)
def figma_fetch_cache(req: FigmaFetchRequest):
    """Fetch Figma file, extract screens and cache them. Returns cacheId==fileId."""
    try:
        client = FigmaClient(access_token=req.token)
        file_id = client.extract_file_id(req.fileUrlOrId)
        screens = asyncio.run(client.extract_screens(file_id))

        # Convert to serializable dicts
        serial = {"screens": [s.model_dump() for s in screens]}
        cache_manager.save(file_id, serial, file_name=file_id)

        return FigmaFetchResponse(cacheId=file_id, fileId=file_id, screensCount=len(screens))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/figma/cache")
def list_cached_files():
    """List cached Figma files (metadata)."""
    return cache_manager.list_cached_files()


@app.get("/api/figma/cache/{cache_id}")
def get_cached_file(cache_id: str):
    """Return cached file data for a given cache id (file id)."""
    data = cache_manager.load(cache_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Cache not found")
    return {"cacheId": cache_id, "data": data}


@app.delete("/api/figma/cache/{cache_id}")
def delete_cached_file(cache_id: str):
    """Delete a cached file and its metadata."""
    deleted = cache_manager.delete(cache_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cache not found")
    return {"cacheId": cache_id, "status": "deleted"}


@app.post("/api/tests/generate")
async def generate_tests(request: Request, req: Optional[GenerateRequest] = Body(None)):
    """Generate test cases for the specified screen from cached data.

    Request must provide `cacheId` (the figma file id used as cache key) and `screenId` (figma node id).
    """
    try:
        # Support both typed JSON body (via `GenerateRequest`) and multipart/form-data
        content_type = request.headers.get('content-type', '')
        payload = {}
        prd_text = None
        options = {}

        if req is not None:
            payload = req.dict()
            prd_text = req.prdText
            options = req.options or {}
        else:
            if 'application/json' in content_type:
                body = await request.json()
                payload = body
                prd_text = body.get('prdText') or body.get('prd_text')
                options = body.get('options', {}) or {}
            else:
                form = await request.form()
                payload = {k: form.get(k) for k in form.keys()}
                prd_text = form.get('prdText') or form.get('prd_text')
                options = {}
                # Handle uploaded PRD file
                prd_file = form.get('prdFile') if 'prdFile' in form else None
                if prd_file:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(prd_file.filename)[1]) as tmp:
                        tmp.write(await prd_file.read())
                        tmp_path = tmp.name
                    try:
                        parser = DocumentParser()
                        parsed = parser.parse_file(tmp_path)
                        prd_text = parsed.get('full_text')
                        options['requirements_parsed'] = parser.extract_requirements(parsed)
                    finally:
                        try:
                            os.unlink(tmp_path)
                        except Exception:
                            pass

        cache_id = payload.get('cacheId') or payload.get('cache_id')
        screen_id = payload.get('screenId') or payload.get('screen_id')
        test_type_raw = payload.get('testType') or payload.get('test_type')
        test_count = int(payload.get('testCount') or payload.get('test_count') or 5)
        prefer_premium = bool(payload.get('prefer_premium') or payload.get('preferPremium') or False)

        # If generateAll flag is set, screenId is optional. Require cacheId always.
        generate_all_flag = bool(payload.get('generateAll') or payload.get('generate_all') or False)

        if not cache_id:
            raise HTTPException(status_code=400, detail="cacheId is required")
        if not generate_all_flag and not screen_id:
            raise HTTPException(status_code=400, detail="screenId is required when not generating for all screens")

        # Attempt to load cache (use earlier sanitize logic)
        cached = None
        tried_ids = []
        if isinstance(cache_id, str):
            tried_ids.append(cache_id)
            m = re.match(r"^([A-Za-z0-9_-]+)", cache_id)
            if m:
                short = m.group(1)
                if short not in tried_ids:
                    tried_ids.append(short)
        for cid in tried_ids:
            try:
                cached = cache_manager.load(cid)
            except Exception:
                cached = None
            if cached is not None:
                cache_id = cid
                break

        if not cached:
            # try metadata matches
            for meta in cache_manager.list_cached_files():
                fid = meta.get('file_id', '')
                if fid and (cache_id in fid or fid in cache_id or fid.startswith(cache_id) or cache_id.startswith(fid)):
                    try:
                        cached = cache_manager.load(fid)
                    except Exception:
                        cached = None
                    if cached is not None:
                        cache_id = fid
                        break

        if not cached:
            raise HTTPException(status_code=404, detail="Cache not found")

        screens = cached.get('screens', [])

        # Map test type
        try:
            ttype = TestCaseType(test_type_raw)
        except Exception:
            ttype = TestCaseType.FUNCTIONAL

        # Prepare PRD context and requirements
        parsed_requirements = options.get('requirements_parsed') if isinstance(options, dict) else None
        if prd_text and parsed_requirements is None:
            try:
                prd_signals = analyze_prd(prd_text)
                # lightweight parse of requirements
                parser = DocumentParser()
                parsed = parser.parse_text(prd_text)
                parsed_requirements = parser.extract_requirements(parsed)
            except Exception:
                parsed_requirements = []

        # Initialize generator
        try:
            generator = TestGenerator()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TestGenerator initialization failed: {e}")

        # batch flag already computed earlier

        run_id = new_run_id(prefix="run")
        screens_results = []
        total_tests = 0
        errors = []

        if generate_all_flag:
            for scr in screens:
                try:
                    # Normalize to dict
                    if hasattr(scr, 'model_dump'):
                        screen_obj = scr.model_dump()
                    elif hasattr(scr, 'dict'):
                        screen_obj = scr.dict()
                    else:
                        screen_obj = scr

                    sid = screen_obj.get('node_id') or screen_obj.get('id') or 'unknown'
                    sname = screen_obj.get('name') or 'Unnamed'

                    tests = generator.generate_test_cases(
                        screen=screen_obj,
                        test_type=ttype,
                        requirements=parsed_requirements or [],
                        test_count=test_count,
                        prd_context=prd_text,
                    )

                    screens_results.append({"screen_id": sid, "screen_name": sname, "testCount": len(tests), "tests": tests})
                    total_tests += len(tests)
                except Exception as ge:
                    errors.append({"screen": screen_obj.get('name') if isinstance(screen_obj, dict) else str(scr), "error": str(ge)})
                    continue
        else:
            # Single screen flow
            if not screen_id:
                raise HTTPException(status_code=400, detail="screenId is required when not generating for all screens")

            # Flexible lookup: try node_id/id, then exact name, substring name, numeric match
            screen = None
            for s in screens:
                nid = s.get('node_id') or s.get('id') or ''
                name = s.get('name') or ''
                if not nid and not name:
                    continue
                if screen_id == nid or screen_id == s.get('id'):
                    screen = s
                    break
                if isinstance(name, str) and name == screen_id:
                    screen = s
                    break
                if isinstance(name, str) and screen_id in name:
                    screen = s
                    break
                # numeric fuzzy match (e.g., '011' vs '11')
                try:
                    if str(int(screen_id)) == str(int(name)):
                        screen = s
                        break
                except Exception:
                    pass
            if not screen:
                raise HTTPException(status_code=404, detail="Screen not found in cache")

            if hasattr(screen, 'model_dump'):
                screen_obj = screen.model_dump()
            elif hasattr(screen, 'dict'):
                screen_obj = screen.dict()
            else:
                screen_obj = screen

            try:
                tests = generator.generate_test_cases(
                    screen=screen_obj,
                    test_type=ttype,
                    requirements=parsed_requirements or [],
                    test_count=test_count,
                    prd_context=prd_text,
                )
                screens_results.append({"screen_id": screen_id, "screen_name": screen_obj.get('name'), "testCount": len(tests), "tests": tests})
                total_tests = len(tests)
            except Exception as ge:
                raise HTTPException(status_code=500, detail=str(ge))

        # Persist aggregated run snapshot
        snapshot = {"run_id": run_id, "cache_id": cache_id, "screens": screens_results, "errors": errors}
        try:
            save_run_snapshot(run_id, snapshot)
        except Exception:
            pass

        return {"runId": run_id, "totalTestCount": total_tests, "screens": screens_results, "errors": errors}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tests/runs")
def list_test_runs():
    """List saved test run snapshots from disk."""
    import os
    from app.services.feedback_manager import BASE_DIR

    runs = []
    if os.path.exists(BASE_DIR):
        for fname in os.listdir(BASE_DIR):
            if fname.endswith('.json'):
                runs.append(fname.replace('.json', ''))
    return {"runs": runs}


@app.get("/api/tests/runs/{run_id}")
def get_test_run(run_id: str):
    snap = load_run_snapshot(run_id)
    if not snap:
        raise HTTPException(status_code=404, detail="Run not found")
    return snap


@app.get("/api/tests/runs/{run_id}/download")
def download_test_run(run_id: str):
    snap = load_run_snapshot(run_id)
    if not snap:
        raise HTTPException(status_code=404, detail="Run not found")
    return Response(content=json.dumps(snap, default=str, ensure_ascii=False), media_type="application/json")


@app.post("/api/tests/evaluate")
def evaluate(req: Dict[str, Any]):
    try:
        evaluator = Evaluator.with_fallback()
        result = evaluator.evaluate(req.get('prd', {}), req.get('tests', {}), screen=req.get('screen'), prefer_premium=bool(req.get('prefer_premium', False)))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze")
async def analyze(request: Request, analyze_payload: Optional[AnalyzeRequest] = Body(None)):
    """Analyze cached Figma JSON and optional PRD (text or uploaded file).

    Accepts either JSON body: { "cacheId": "<file_id>", "prdText": "...", "options": { ... } }
    or multipart form with `cacheId` and an uploaded `prdFile`.
    Returns filtered screens and metrics.
    """
    content_type = request.headers.get('content-type', '')
    cache_id = None
    prd_text = None
    apply_filtering = True
    options = {}

    if 'application/json' in content_type:
        body = await request.json()
        cache_id = body.get('cacheId') or body.get('cache_id')
        prd_text = body.get('prdText') or body.get('prd_text')
        options = body.get('options', {}) or {}
        if not isinstance(options, dict):
            options = {}
        apply_filtering = bool(options.get('applyFiltering', True))
    else:
        form = await request.form()
        cache_id = form.get('cacheId') or form.get('cache_id')
        prd_text = form.get('prdText') or form.get('prd_text')
        # uploaded file
        prd_file = form.get('prdFile') if 'prdFile' in form else None
        if prd_file:
            # Save to temp file and parse
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(prd_file.filename)[1]) as tmp:
                tmp.write(await prd_file.read())
                tmp_path = tmp.name
            try:
                parser = DocumentParser()
                parsed = parser.parse_file(tmp_path)
                prd_text = parsed.get('full_text')
                # also include parsed requirements
                options['requirements_parsed'] = parser.extract_requirements(parsed)
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        try:
            apply_filtering = bool(form.get('applyFiltering', 'true').lower() in ['true', '1', 'yes'])
        except Exception:
            apply_filtering = True
    # First, prefer the typed body if provided (this populates Swagger UI)
    if analyze_payload is not None:
        cache_id = analyze_payload.cacheId
        prd_text = analyze_payload.prdText
        options = analyze_payload.options or {}
        if not isinstance(options, dict):
            options = {}
        apply_filtering = bool(options.get('applyFiltering', True))
    else:
        # Fallback to interpreting raw JSON or multipart form data
        if 'application/json' in content_type:
            body = await request.json()
            cache_id = body.get('cacheId') or body.get('cache_id')
            prd_text = body.get('prdText') or body.get('prd_text')
            options = body.get('options', {}) or {}
            if not isinstance(options, dict):
                options = {}
            apply_filtering = bool(options.get('applyFiltering', True))
        else:
            form = await request.form()
            cache_id = form.get('cacheId') or form.get('cache_id')
            prd_text = form.get('prdText') or form.get('prd_text')
            prd_file = form.get('prdFile') if 'prdFile' in form else None
            if prd_file:
                # Save to temp file and parse
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(prd_file.filename)[1]) as tmp:
                    tmp.write(await prd_file.read())
                    tmp_path = tmp.name
                try:
                    parser = DocumentParser()
                    parsed = parser.parse_file(tmp_path)
                    prd_text = parsed.get('full_text')
                    # also include parsed requirements
                    options['requirements_parsed'] = parser.extract_requirements(parsed)
                finally:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
            try:
                apply_filtering = bool(form.get('applyFiltering', 'true').lower() in ['true', '1', 'yes'])
            except Exception:
                apply_filtering = True

    if not cache_id:
        raise HTTPException(status_code=400, detail="cacheId is required")

    cached = None
    tried_ids = []
    if isinstance(cache_id, str):
        tried_ids.append(cache_id)
        # try extracting leading alphanumeric id (common Figma file ids)
        m = re.match(r"^([A-Za-z0-9_-]+)", cache_id)
        if m:
            short = m.group(1)
            if short not in tried_ids:
                tried_ids.append(short)
    for cid in tried_ids:
        try:
            cached = cache_manager.load(cid)
        except Exception:
            cached = None
        if cached is not None:
            cache_id = cid
            break

    if not cached:
        raise HTTPException(status_code=404, detail="Cache not found")

    raw_screens = cached.get('screens', [])

    # PRD analysis
    prd_signals = {}
    parsed_requirements = options.get('requirements_parsed', None)
    if prd_text:
        prd_signals = analyze_prd(prd_text)
        # if requirements not already parsed, run lightweight parsing
        if parsed_requirements is None:
            try:
                parser = DocumentParser()
                parsed = parser.parse_text(prd_text)
                parsed_requirements = parser.extract_requirements(parsed)
            except Exception:
                parsed_requirements = []

    # Apply filtering using FigmaClient logic
    filtered_screens = []
    total_before = 0
    total_after = 0

    if apply_filtering:
        for screen in raw_screens:
            comps = screen.get('components', []) if isinstance(screen, dict) else []
            total_before += len(comps)
            temp_client = FigmaClient(access_token="dummy", prd_signals=prd_signals)
            try:
                filtered_components = temp_client._filter_components_by_relevance(comps)
            except Exception:
                filtered_components = comps
            filtered = screen.copy() if isinstance(screen, dict) else screen
            if isinstance(filtered, dict):
                filtered['components'] = filtered_components
            filtered_screens.append(filtered)
            total_after += len(filtered_components)
    else:
        filtered_screens = raw_screens
        total_before = sum(len(s.get('components', []) or []) for s in raw_screens)
        total_after = total_before

    filter_rate = ((total_before - total_after) / total_before * 100) if total_before > 0 else 0.0

    response = {
        'cacheId': cache_id,
        'screensProcessed': len(raw_screens),
        'totalComponentsBefore': total_before,
        'totalComponentsAfter': total_after,
        'filterRate': round(filter_rate, 2),
        'screens': filtered_screens,
        'requirements': parsed_requirements or []
    }

    return response
