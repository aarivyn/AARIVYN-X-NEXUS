"""Pydantic schemas for the budget details API.

Based on the taxonomy in promt.txt covering target budget, maximum
budget, intensity (1-10 scale), and free-text details.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator
# ──────────────────────────────────────────────────────────────────────────────
# Request / Response models
# ──────────────────────────────────────────────────────────────────────────────

class BudgetCreate(BaseModel):
    """Request body for creating a budget entry."""
    target_budget: float = Field(
        ..., gt=0, description="Target budget amount (must be > 0)"
    )
    maximum_budget: float = Field(
        ..., gt=0, description="Maximum budget amount (must be > 0)"
    )
    intensity: int = Field(
        ..., ge=1, le=10, description="Intensity on a scale of 1 to 10"
    )
    details: str = Field(
        "", description="Free-text details describing the budget entry"
    )
    name: str | None = Field(None, description="Optional display name / label")

    @model_validator(mode="after")
    def _maximum_must_be_gte_target(self) -> "BudgetCreate":
        if self.maximum_budget < self.target_budget:
            raise ValueError(
                f"maximum_budget ({self.maximum_budget}) must be "
                f">= target_budget ({self.target_budget})"
            )
        return self


class BudgetRecord(BaseModel):
    """The stored representation of the (singleton) budget."""
    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str | None = None
    target_budget: float = Field(..., gt=0)
    maximum_budget: float = Field(..., gt=0)
    intensity: int = Field(..., ge=1, le=10)
    details: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))



