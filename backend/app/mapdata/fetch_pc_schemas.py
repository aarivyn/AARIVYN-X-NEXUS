"""Pydantic schemas for the Planetary Computer data-fetch API.

A request references one or more stored locations (by id) plus a date
window, and the response carries the signed STAC items returned by
``mapdata.fetch_pc.fetch_all_layers`` organised per location and per layer.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────────────────────────────────────────────────────
# Date normalization
# ──────────────────────────────────────────────────────────────────────────────

# Accepted input formats. Both ``YYYY-MM-DD`` (ISO 8601) and ``DD.MM.YYYY``
# (European order, as sent by some clients) are supported. Dates are
# normalized to ISO 8601 (``YYYY-MM-DD``) because the STAC API only accepts
# RFC 3339 datetime strings.
_DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y")


def _normalize_date(value: str) -> str:
    """Parse a date string into ISO 8601 form, or raise a clear ValueError."""
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(
        f"invalid date {value!r}: expected YYYY-MM-DD or DD.MM.YYYY"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Request / Response models
# ──────────────────────────────────────────────────────────────────────────────

class FetchPCRequest(BaseModel):
    """Request body for fetching Planetary Computer data for stored locations."""
    location_ids: list[str] = Field(
        ..., min_length=1, description="IDs of stored location records to fetch data for"
    )
    start_date: str = Field(
        ..., description="Start date (YYYY-MM-DD or DD.MM.YYYY) of the data window"
    )
    end_date: str = Field(
        ..., description="End date (YYYY-MM-DD or DD.MM.YYYY) of the data window"
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def _validate_date(cls, value: str) -> str:
        return _normalize_date(value)


class LocationResult(BaseModel):
    """Per-location fetch outcome."""
    location_id: str
    name: str | None = None
    state: str
    district: str
    city: str | None = None
    # layer_name -> list of signed STAC item dicts, or an error dict like
    # {"error": ..., "collection_id": ...} when a layer fetch failed.
    layers: dict[str, Any]


class FetchPCResponse(BaseModel):
    """Response wrapping results for every requested location."""
    id: str = Field(default_factory=lambda: uuid4().hex)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    locations: list[LocationResult]
