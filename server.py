"""Minimal FastAPI server exposing evaluation endpoints."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, Optional

from app.services import Evaluator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    screenId: str
    options: Optional[Dict[str, Any]] = None


class EvaluateRequest(BaseModel):
    prd: Dict[str, Any]
    tests: Dict[str, Any]
    screen: Optional[Dict[str, Any]] = None
    prefer_premium: Optional[bool] = False


@app.get("/api/tests")
def list_tests():
    return []


@app.post("/api/tests/generate")
def generate_tests(req: GenerateRequest):
    return {"status": "ok", "screenId": req.screenId, "test_cases": []}


@app.post("/api/tests/evaluate")
def evaluate(req: EvaluateRequest):
    try:
        evaluator = Evaluator.with_fallback()
        result = evaluator.evaluate(req.prd, req.tests, screen=req.screen, prefer_premium=bool(req.prefer_premium))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
