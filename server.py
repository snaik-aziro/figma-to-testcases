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
