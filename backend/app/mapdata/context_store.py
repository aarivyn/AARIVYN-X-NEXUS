"""Shared accessor for ingested site-data (budget, locations, social groups,
timeline).

Modules 2-7 read the data submitted through the Map Data Ingest API
(`/api/v1/budget`, `/api/v1/social/groups`, `/api/v1/locations`,
`/api/v1/timeline`) via these helpers instead of relying purely on
request parameters or hard-coded defaults.

Every getter is non-breaking: when the corresponding JSON file does not exist
yet (i.e. nothing has been ingested), it returns `None` so callers can fall
back to request-provided or default values. This keeps the pipeline usable
before any ingest has happened.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Optional

from . import config
from .budget_schemas import BudgetRecord
from .location_schemas import LocationRecord
from .social_schemas import SocialGroupRecord
from .timeline_schemas import TimelineRecord

# Fixed singleton paths (must match budget_routes.py / timeline_routes.py).
_BUDGET_FILE: Path = config.DATA_DIR / "budget.json"
_TIMELINE_FILE: Path = config.DATA_DIR / "timeline.json"
_SOCIAL_DIR: Path = config.DATA_DIR / "social_groups"
_LOCATIONS_DIR: Path = config.DATA_DIR / "locations"


def _read_json(path: Path) -> Optional[dict[str, Any]]:
    """Best-effort JSON read; returns None on any failure (missing, corrupt)."""
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text())
    except (json.JSONDecodeError, TypeError, OSError):
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Budget
# ──────────────────────────────────────────────────────────────────────────────

def get_budget() -> Optional[BudgetRecord]:
    """The ingested budget singleton, or None if it has not been set."""
    data = _read_json(_BUDGET_FILE)
    if data is None:
        return None
    try:
        return BudgetRecord(**data)
    except (TypeError, ValueError):
        return None


def resolve_budget_limit(
    request_value: Optional[float],
    *,
    default: float = 200_000_000.0,
    use_maximum: bool = False,
) -> float:
    """Resolve the budget cap for feasibility / optimization.

    Precedence (ingested data wins):
      1. Ingested budget singleton -- `maximum_budget` when `use_maximum` is
         True, otherwise `target_budget`.
      2. The request-provided value.
      3. `default`.
    """
    budget = get_budget()
    if budget is not None:
        return float(budget.maximum_budget if use_maximum else budget.target_budget)
    if request_value is not None:
        return float(request_value)
    return float(default)


def get_budget_hard_ceiling() -> Optional[float]:
    """The ingested `maximum_budget`, or None if nothing has been ingested."""
    budget = get_budget()
    return float(budget.maximum_budget) if budget is not None else None


# ──────────────────────────────────────────────────────────────────────────────
# Timeline
# ──────────────────────────────────────────────────────────────────────────────

def get_timeline() -> Optional[TimelineRecord]:
    """The ingested timeline singleton, or None if it has not been set."""
    data = _read_json(_TIMELINE_FILE)
    if data is None:
        return None
    try:
        return TimelineRecord(**data)
    except (TypeError, ValueError):
        return None


_DURATION_TOKEN = re.compile(r"(\d+(?:\.\d+)?)\s*(month|week|year|day)s?", re.I)
_MONTHS_PER_UNIT = {"day": 1 / 30.0, "week": 1 / 4.345, "month": 1.0, "year": 12.0}


def _duration_to_months(text: str) -> Optional[float]:
    """Parse a human duration string like '6 months' into months."""
    if not text:
        return None
    total = 0.0
    found = False
    for match in _DURATION_TOKEN.finditer(text):
        value = float(match.group(1))
        unit = match.group(2).lower()
        total += value * _MONTHS_PER_UNIT[unit]
        found = True
    return total if found else None


def _deadline_to_months(deadline: Optional[date], today: Optional[date] = None) -> Optional[float]:
    """Months between today and the deadline; None if the deadline is absent."""
    if deadline is None:
        return None
    today = today or date.today()
    return max((deadline - today).days / 30.0, 0.0)


def resolve_time_horizon_months(
    request_value: Optional[int],
    *,
    default: int = 36,
) -> int:
    """Resolve a time horizon in months for feasibility / optimization.

    Precedence when data has been ingested:
      1. Deadline-derived months (only when the deadline is sooner than the
         requested/default horizon, i.e. it actually constrains).
      2. Duration-derived months from `expected_duration`.
      3. Request-provided / default value.

    Timeline `urgency` never stretches the horizon; a higher urgency only
    means the work must fit within what is already available.
    """
    timeline = get_timeline()
    if timeline is None:
        return int(request_value) if request_value is not None else int(default)

    baseline = float(request_value) if request_value is not None else float(default)

    deadline_months = _deadline_to_months(timeline.deadline)
    if deadline_months is not None and deadline_months > 0 and deadline_months < baseline:
        return max(int(round(deadline_months)), 1)

    duration_months = _duration_to_months(timeline.expected_duration)
    if duration_months is not None and duration_months > 0 and duration_months < baseline:
        return max(int(round(duration_months)), 1)

    return int(round(baseline)) if request_value is not None else int(default)


# ──────────────────────────────────────────────────────────────────────────────
# Social groups
# ──────────────────────────────────────────────────────────────────────────────

def get_social_groups() -> list[SocialGroupRecord]:
    """All ingested social-group records (empty when none have been created)."""
    records: list[SocialGroupRecord] = []
    if not _SOCIAL_DIR.exists():
        return records
    for path in sorted(_SOCIAL_DIR.glob("*.json")):
        data = _read_json(path)
        if data is None:
            continue
        try:
            records.append(SocialGroupRecord(**data))
        except (TypeError, ValueError):
            continue
    return records


def get_social_summary() -> Optional[dict[str, Any]]:
    """A compact demographic summary used by modules 2-7.

    Returns None when no social-group data has been ingested so callers can
    omit the section entirely (graceful fallback). When data is present the
    summary includes group count, cumulative intensity, area-type presence,
    and beneficiary-profile composition.
    """
    groups = get_social_groups()
    if not groups:
        return None

    profile_count = sum(len(g.profiles) for g in groups)
    area_types: dict[str, int] = {}
    income_groups: dict[str, int] = {}
    genders: dict[str, int] = {}
    for group in groups:
        for profile in group.profiles:
            if profile.area_type is not None:
                key = profile.area_type.value
                area_types[key] = area_types.get(key, 0) + 1
            if profile.income_group is not None:
                key = profile.income_group.value
                income_groups[key] = income_groups.get(key, 0) + 1
            if profile.gender is not None:
                key = profile.gender.value
                genders[key] = genders.get(key, 0) + 1

    return {
        "group_count": len(groups),
        "profile_count": profile_count,
        "cumulative_intensity": sum(g.intensity for g in groups),
        "area_types": area_types,
        "income_groups": income_groups,
        "genders": genders,
        "names": [g.name for g in groups if g.name],
    }


def has_rural_service_area() -> bool:
    """True when a social group has a rural/semi-urban `area_type` profile."""
    area_types = (get_social_summary() or {}).get("area_types") or {}
    return bool(area_types.get("rural") or area_types.get("semi_urban_peri_urban"))


# ──────────────────────────────────────────────────────────────────────────────
# Locations
# ──────────────────────────────────────────────────────────────────────────────

def get_locations() -> list[LocationRecord]:
    """All ingested location records (empty when none have been created)."""
    records: list[LocationRecord] = []
    if not _LOCATIONS_DIR.exists():
        return records
    for path in sorted(_LOCATIONS_DIR.glob("*.json")):
        data = _read_json(path)
        if data is None:
            continue
        try:
            records.append(LocationRecord(**data))
        except (TypeError, ValueError):
            continue
    return records


# ──────────────────────────────────────────────────────────────────────────────
# JSON-serializable snapshots (for embedding into result payloads)
# ──────────────────────────────────────────────────────────────────────────────

def budget_snapshot() -> Optional[dict[str, Any]]:
    budget = get_budget()
    if budget is None:
        return None
    return budget.model_dump(mode="json")


def timeline_snapshot() -> Optional[dict[str, Any]]:
    timeline = get_timeline()
    if timeline is None:
        return None
    return timeline.model_dump(mode="json")


def locations_snapshot() -> list[dict[str, Any]]:
    return [loc.model_dump(mode="json") for loc in get_locations()]
