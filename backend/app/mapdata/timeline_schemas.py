"""Pydantic schemas for the timeline API.

Based on promt.txt: urgency (1-10), expected duration,
deadline, and free-text details.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# Request / Response models
# ──────────────────────────────────────────────────────────────────────────────

class TimelineCreate(BaseModel):
    """Request body for creating/updating the timeline."""
    urgency: int = Field(
        ..., ge=1, le=10, description="Urgency on a scale of 1 to 10"
    )
    expected_duration: str = Field(
        ..., description="Expected duration (e.g. '3 months', '2 weeks')"
    )
    deadline: date = Field(
        ..., description="Deadline date (YYYY-MM-DD)"
    )
    details: str = Field(
        "", description="Free-text details"
    )
    name: str | None = Field(None, description="Optional display name / label")


class TimelineRecord(BaseModel):
    """The stored representation of the (singleton) timeline."""
    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str | None = None
    urgency: int = Field(..., ge=1, le=10)
    expected_duration: str
    deadline: date
    details: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))



