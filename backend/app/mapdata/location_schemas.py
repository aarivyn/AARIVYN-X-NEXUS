"""Pydantic schemas for the locations API.

Each location is identified by names only: a required state name and
optional district and city names (no coordinates). It also carries an
intensity rating on a 1-10 scale and a free-text details string.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# Request / Response models
# ──────────────────────────────────────────────────────────────────────────────

class LocationCreate(BaseModel):
    """Request body for creating a location entry."""
    state: str = Field(
        ..., min_length=1, description="Name of the state (required)"
    )
    district: str = Field(
        ..., min_length=1, description="Name of the district (required)"
    )
    city: str | None = Field(
        None, description="Name of the city (optional)"
    )
    intensity: int = Field(
        ..., ge=1, le=10, description="Intensity on a scale of 1 to 10"
    )
    details: str = Field(
        "", description="Free-text details describing the location"
    )
    name: str | None = Field(None, description="Optional display name / label")


class LocationRecord(BaseModel):
    """The stored representation of a location entry."""
    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str | None = None
    state: str
    district: str
    city: str | None = None
    intensity: int = Field(..., ge=1, le=10)
    details: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LocationListResponse(BaseModel):
    """Wrapper for list responses."""
    count: int
    items: list[LocationRecord]
