"""Simple feedback storage and run snapshot utilities."""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional


BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "feedback_runs")


def _ensure_dir() -> None:
    os.makedirs(BASE_DIR, exist_ok=True)


def save_run_snapshot(run_id: str, snapshot: Dict[str, Any]) -> str:
    _ensure_dir()
    path = os.path.join(BASE_DIR, f"{run_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
    return path


def new_run_id(prefix: Optional[str] = None) -> str:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    if prefix:
        return f"{prefix}-{ts}"
    return ts


def load_run_snapshot(run_id: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(BASE_DIR, f"{run_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


__all__ = ["save_run_snapshot", "load_run_snapshot", "new_run_id"]
