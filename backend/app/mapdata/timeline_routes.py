"""Timeline API routes — singleton resource.

There is only ever one timeline. Endpoints operate on the single resource.

Endpoint summary
----------------
GET    /api/v1/timeline   →  get the current timeline (404 if not set)
PUT    /api/v1/timeline   →  create or replace the timeline
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException

from . import config
from .timeline_schemas import TimelineCreate, TimelineRecord

router = APIRouter(prefix="/api/v1/timeline", tags=["timeline"])

# There is exactly one timeline, stored at this fixed path.
_TIMELINE_FILE: Path = config.DATA_DIR / "timeline.json"


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _load() -> TimelineRecord | None:
    if not _TIMELINE_FILE.exists():
        return None
    try:
        return TimelineRecord(**json.loads(_TIMELINE_FILE.read_text()))
    except (json.JSONDecodeError, TypeError):
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@router.get("", response_model=TimelineRecord)
def get_timeline() -> TimelineRecord:
    """Return the current timeline. 404 if it has not been set yet."""
    rec = _load()
    if rec is None:
        raise HTTPException(404, "no timeline has been set")
    return rec


@router.put("", response_model=TimelineRecord)
def set_timeline(body: TimelineCreate) -> TimelineRecord:
    """Create or fully replace the timeline."""
    existing = _load()
    now = datetime.now(timezone.utc)

    record = TimelineRecord(
        name=body.name,
        urgency=body.urgency,
        expected_duration=body.expected_duration,
        deadline=body.deadline,
        details=body.details,
        created_at=existing.created_at if existing else now,
        updated_at=now,
    )
    if existing is not None:
        record.id = existing.id
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    _TIMELINE_FILE.write_text(record.model_dump_json(indent=2))
    return record
