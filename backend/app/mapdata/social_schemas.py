"""Pydantic schemas for the social-groups / demographic data API.

Based on the taxonomy in promt.txt covering income-based groups,
employment status, gender, age, caste, area type, and religion.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


# ──────────────────────────────────────────────────────────────────────────────
# Enums matching the promt.txt taxonomy
# ──────────────────────────────────────────────────────────────────────────────

class IncomeGroup(str, Enum):
    BPL = "BPL"  # Below Poverty Line
    LIG = "LIG"  # Low Income Group
    MIG_I = "MIG-I"
    MIG_II = "MIG-II"
    MIG = "MIG"  # Middle Income Group (unsplit)
    HIG = "HIG"  # High Income Group
    EWS = "EWS"  # Economically Weaker Section


class EmploymentStatus(str, Enum):
    SALARIED_GOVT = "salaried_government"
    SALARIED_PRIVATE = "salaried_private"
    SELF_EMPLOYED = "self_employed"
    DAILY_WAGE = "daily_wage_labourer"
    UNEMPLOYED = "unemployed"
    STUDENT = "student"
    HOMEMAKER = "homemaker"
    RETIRED = "retired_pensioner"
    AGRICULTURAL = "agricultural_worker_farmer"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class CasteCategory(str, Enum):
    GENERAL = "general_unreserved"
    OBC = "obc"
    SC = "sc"
    ST = "st"
    EWS = "ews"


class AreaType(str, Enum):
    URBAN = "urban"
    RURAL = "rural"
    SEMI_URBAN = "semi_urban_peri_urban"


class Religion(str, Enum):
    HINDU = "hindu"
    MUSLIM = "muslim"
    CHRISTIAN = "christian"
    SIKH = "sikh"
    BUDDHIST = "buddhist"
    JAIN = "jain"
    OTHER = "other"


# ──────────────────────────────────────────────────────────────────────────────
# Request / Response models
# ──────────────────────────────────────────────────────────────────────────────

class SocialGroupProfile(BaseModel):
    """A single socio-demographic profile — any combination of the taxonomy fields."""
    income_group: IncomeGroup | None = Field(None, description="Income-based classification")
    employment_status: EmploymentStatus | None = Field(None, description="Employment status")
    gender: Gender | None = Field(None, description="Gender")
    age: int | None = Field(None, ge=0, le=150, description="Age in years")
    caste: CasteCategory | None = Field(None, description="Caste / social category")
    area_type: AreaType | None = Field(None, description="Area / residence type")
    religion: Religion | None = Field(None, description="Religion")


class SocialGroupCreate(BaseModel):
    """Request body for creating a social-group entry."""
    profiles: list[SocialGroupProfile] = Field(
        ..., min_length=1, description="One or more social-group profiles"
    )
    intensity: int = Field(
        ..., ge=1, le=10, description="Intensity on a scale of 1 to 10"
    )
    details: str = Field(
        "", description="Free-text details string describing the entry"
    )
    name: str | None = Field(None, description="Optional display name / label")

    @model_validator(mode="after")
    def _require_at_least_one_field_per_profile(self) -> "SocialGroupCreate":
        for i, profile in enumerate(self.profiles):
            filled = any(v is not None for v in profile.model_dump().values())
            if not filled:
                raise ValueError(
                    f"profiles[{i}] must contain at least one social-group field"
                )
        return self


class SocialGroupRecord(BaseModel):
    """The stored representation of a social-group entry."""
    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str | None = None
    profiles: list[SocialGroupProfile]
    intensity: int = Field(..., ge=1, le=10)
    details: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SocialGroupListResponse(BaseModel):
    """Wrapper for list responses."""
    count: int
    items: list[SocialGroupRecord]


# ──────────────────────────────────────────────────────────────────────────────
# Enum helper — expose all taxonomy values via the API
# ──────────────────────────────────────────────────────────────────────────────

class TaxonomyResponse(BaseModel):
    """All allowed values for each social-group axis."""
    income_groups: list[dict[str, str]]
    employment_statuses: list[dict[str, str]]
    genders: list[dict[str, str]]
    caste_categories: list[dict[str, str]]
    area_types: list[dict[str, str]]
    religions: list[dict[str, str]]
