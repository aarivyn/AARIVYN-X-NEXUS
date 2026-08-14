"""Budget details API routes — singleton resource.

There is only ever one budget. Endpoints operate on the single resource.

Endpoint summary
----------------
GET    /api/v1/budget   →  get the current budget (404 if not set)
PUT    /api/v1/budget   →  create or replace the budget
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException

from . import config
from .budget_schemas import BudgetCreate, BudgetRecord

router = APIRouter(prefix="/api/v1/budget", tags=["budget"])

# There is exactly one budget, stored at this fixed path.
_BUDGET_FILE: Path = config.DATA_DIR / "budget.json"


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _load() -> BudgetRecord | None:
    if not _BUDGET_FILE.exists():
        return None
    try:
        return BudgetRecord(**json.loads(_BUDGET_FILE.read_text()))
    except (json.JSONDecodeError, TypeError):
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@router.get("", response_model=BudgetRecord)
def get_budget() -> BudgetRecord:
    """Return the current budget. 404 if it has not been set yet."""
    rec = _load()
    if rec is None:
        raise HTTPException(404, "no budget has been set")
    return rec


@router.put("", response_model=BudgetRecord)
def set_budget(body: BudgetCreate) -> BudgetRecord:
    """Create or fully replace the budget.

    To partially update individual fields, send the complete budget
    with the changed values alongside the unchanged ones.
    """
    existing = _load()
    now = datetime.now(timezone.utc)

    record = BudgetRecord(
        id=existing.id if existing else None,
        name=body.name,
        target_budget=body.target_budget,
        maximum_budget=body.maximum_budget,
        intensity=body.intensity,
        details=body.details,
        created_at=existing.created_at if existing else now,
        updated_at=now,
    )
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    _BUDGET_FILE.write_text(record.model_dump_json(indent=2))
    return record
