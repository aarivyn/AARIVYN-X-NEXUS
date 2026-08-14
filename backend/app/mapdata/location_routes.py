"""Locations CRUD API routes.

Each location is identified by names only: state (required) and
optional district and city names (no coordinates). It also has an
intensity (1-10) and a free-text details string.

Endpoint summary
----------------
POST   /api/v1/locations       →  create one or many location entries
GET    /api/v1/locations       →  list all entries
GET    /api/v1/locations/{id}  →  get a single entry
PUT    /api/v1/locations/{id}  →  update an entry
DELETE /api/v1/locations/{id}  →  delete an entry
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException

from . import config
from .location_schemas import (
    LocationCreate,
    LocationListResponse,
    LocationRecord,
)

router = APIRouter(prefix="/api/v1/locations", tags=["locations"])

# Storage directory anchored under the existing DATA_DIR
DATA_DIR = config.DATA_DIR / "locations"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _file_for(record_id: str) -> Path:
    return DATA_DIR / f"{record_id}.json"


def _read_all() -> list[LocationRecord]:
    records: list[LocationRecord] = []
    for p in sorted(DATA_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text())
            records.append(LocationRecord(**data))
        except (json.JSONDecodeError, TypeError):
            continue
    return records


def _load_one(record_id: str) -> LocationRecord | None:
    path = _file_for(record_id)
    if not path.exists():
        return None
    try:
        return LocationRecord(**json.loads(path.read_text()))
    except (json.JSONDecodeError, TypeError):
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@router.post("", response_model=LocationRecord, status_code=201)
def create_location(body: LocationCreate) -> LocationRecord:
    """Create a location entry."""
    record = LocationRecord(
        name=body.name,
        state=body.state,
        district=body.district,
        city=body.city,
        intensity=body.intensity,
        details=body.details,
    )
    _file_for(record.id).write_text(record.model_dump_json(indent=2))
    return record


@router.get("", response_model=LocationListResponse)
def list_locations() -> LocationListResponse:
    """List all location entries."""
    items = _read_all()
    return LocationListResponse(count=len(items), items=items)


@router.get("/{record_id}", response_model=LocationRecord)
def get_location(record_id: str) -> LocationRecord:
    """Fetch a single location entry by id."""
    rec = _load_one(record_id)
    if rec is None:
        raise HTTPException(404, f"no location record {record_id}")
    return rec


@router.put("/{record_id}", response_model=LocationRecord)
def update_location(record_id: str, body: LocationCreate) -> LocationRecord:
    """Replace an existing location entry."""
    existing = _load_one(record_id)
    if existing is None:
        raise HTTPException(404, f"no location record {record_id}")

    updated = LocationRecord(
        id=record_id,
        name=body.name,
        state=body.state,
        district=body.district,
        city=body.city,
        intensity=body.intensity,
        details=body.details,
        created_at=existing.created_at,
        updated_at=datetime.now(timezone.utc),
    )
    _file_for(record_id).write_text(updated.model_dump_json(indent=2))
    return updated


@router.delete("/{record_id}", status_code=204)
def delete_location(record_id: str) -> None:
    """Delete a location entry."""
    path = _file_for(record_id)
    if not path.exists():
        raise HTTPException(404, f"no location record {record_id}")
    path.unlink()
