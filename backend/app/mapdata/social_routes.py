"""Social-groups CRUD API routes.

Endpoint summary
----------------
GET    /api/v1/social/taxonomy     →  list all allowed enum values
POST   /api/v1/social/groups       →  create one or many social-group entries
GET    /api/v1/social/groups       →  list all entries
GET    /api/v1/social/groups/{id}  →  get a single entry
PUT    /api/v1/social/groups/{id}  →  update an entry
DELETE /api/v1/social/groups/{id}  →  delete an entry
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException

from . import config
from .social_schemas import (
    AreaType,
    CasteCategory,
    EmploymentStatus,
    Gender,
    IncomeGroup,
    Religion,
    SocialGroupCreate,
    SocialGroupListResponse,
    SocialGroupProfile,
    SocialGroupRecord,
    TaxonomyResponse,
)

router = APIRouter(prefix="/api/v1/social", tags=["social-groups"])

# Storage directory anchored under the existing DATA_DIR
DATA_DIR = config.DATA_DIR / "social_groups"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _file_for(record_id: str) -> Path:
    return DATA_DIR / f"{record_id}.json"


def _read_all() -> list[SocialGroupRecord]:
    records: list[SocialGroupRecord] = []
    for p in sorted(DATA_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text())
            records.append(SocialGroupRecord(**data))
        except (json.JSONDecodeError, TypeError):
            continue
    return records


def _load_one(record_id: str) -> SocialGroupRecord | None:
    path = _file_for(record_id)
    if not path.exists():
        return None
    try:
        return SocialGroupRecord(**json.loads(path.read_text()))
    except (json.JSONDecodeError, TypeError):
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/taxonomy", response_model=TaxonomyResponse)
def get_taxonomy() -> TaxonomyResponse:
    """Return every allowed value for the social-group categorical axes."""
    def _pairs(enum_cls: type) -> list[dict[str, str]]:
        return [
            {"key": e.value, "label": e.name.replace("_", " ").title()}
            for e in enum_cls
        ]

    return TaxonomyResponse(
        income_groups=_pairs(IncomeGroup),
        employment_statuses=_pairs(EmploymentStatus),
        genders=_pairs(Gender),
        caste_categories=_pairs(CasteCategory),
        area_types=_pairs(AreaType),
        religions=_pairs(Religion),
    )


@router.post("/groups", response_model=SocialGroupRecord, status_code=201)
def create_social_group(body: SocialGroupCreate) -> SocialGroupRecord:
    """Create a social-group entry from one or more profiles."""
    record = SocialGroupRecord(
        name=body.name,
        profiles=[SocialGroupProfile(**p.model_dump()) for p in body.profiles],
        intensity=body.intensity,
        details=body.details,
    )
    _file_for(record.id).write_text(record.model_dump_json(indent=2))
    return record


@router.get("/groups", response_model=SocialGroupListResponse)
def list_social_groups() -> SocialGroupListResponse:
    """List all social-group entries."""
    items = _read_all()
    return SocialGroupListResponse(count=len(items), items=items)


@router.get("/groups/{record_id}", response_model=SocialGroupRecord)
def get_social_group(record_id: str) -> SocialGroupRecord:
    """Fetch a single social-group entry by id."""
    rec = _load_one(record_id)
    if rec is None:
        raise HTTPException(404, f"no social-group record {record_id}")
    return rec


@router.put("/groups/{record_id}", response_model=SocialGroupRecord)
def update_social_group(record_id: str, body: SocialGroupCreate) -> SocialGroupRecord:
    """Replace an existing social-group entry."""
    existing = _load_one(record_id)
    if existing is None:
        raise HTTPException(404, f"no social-group record {record_id}")

    updated = SocialGroupRecord(
        id=record_id,
        name=body.name,
        profiles=[SocialGroupProfile(**p.model_dump()) for p in body.profiles],
        intensity=body.intensity,
        details=body.details,
        created_at=existing.created_at,
        updated_at=datetime.now(timezone.utc),
    )
    _file_for(record_id).write_text(updated.model_dump_json(indent=2))
    return updated


@router.delete("/groups/{record_id}", status_code=204)
def delete_social_group(record_id: str) -> None:
    """Delete a social-group entry."""
    path = _file_for(record_id)
    if not path.exists():
        raise HTTPException(404, f"no social-group record {record_id}")
    path.unlink()
