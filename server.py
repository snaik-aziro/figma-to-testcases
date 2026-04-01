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
def generate_tests(req: GenerateRequest):
    """Generate test cases for the specified screen from cached data.

    Request must provide `cacheId` (the figma file id used as cache key) and `screenId` (figma node id).
    """
    try:
        cached = cache_manager.load(req.cacheId)
        if not cached:
            raise HTTPException(status_code=404, detail="Cache not found")

        screens = cached.get("screens", [])
        screen = next((s for s in screens if s.get("node_id") == req.screenId or s.get("node_id") == req.screenId), None)
        if not screen:
            raise HTTPException(status_code=404, detail="Screen not found in cache")

        # Map test type
        try:
            ttype = TestCaseType(req.testType)
        except Exception:
            ttype = TestCaseType.FUNCTIONAL

        generator = TestGenerator()
        tests = generator.generate_test_cases(screen, test_type=ttype, test_count=int(req.testCount))

        # Persist run snapshot for download/listing
        run_id = new_run_id(prefix="run")
        snapshot = {"run_id": run_id, "cache_id": req.cacheId, "screen_id": req.screenId, "tests": tests}
        save_run_snapshot(run_id, snapshot)

        return {"runId": run_id, "testCount": len(tests), "tests": tests}
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
