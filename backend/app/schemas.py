"""Pydantic schemas for the NEXUS ingest API."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

# Representations: the common output forms every ingested file is reduced to.
Representation = Literal[
    "vector_geojson",   # geometry data -> RFC 7946 GeoJSON in EPSG:4326
    "raster",           # gridded/imagery data -> normalized raster + metadata
    "point_cloud",      # LiDAR -> stats + preview + stored original
    "tabular",          # attribute tables -> rows + optional point features
    "document",         # text-bearing files -> extracted text
    "unsupported",      # stored as-is, conversion not possible in this build
]

# Source taxonomy from inputs.txt (map data categories).
Category = Literal[
    "base_maps", "utilities", "imagery", "geological",
    "water_demand", "field_observations", "engineering", "weather", "general",
]

CATEGORIES = {
    "base_maps", "utilities", "imagery", "geological",
    "water_demand", "field_observations", "engineering", "weather", "general",
}


class RecordMeta(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    category: Category = "general"
    usage: str = Field(
        "general",
        description="What the data is FOR (e.g. road_network, utility_network, "
                    "terrain). Explicit via the usage= form field, otherwise "
                    "inferred from filename/type and flagged in warnings.",
    )
    source_type: str                      # e.g. "shapefile", "geotiff", "csv"
    source_filename: str
    representation: Representation
    source_crs: Optional[str] = None
    target_crs: str = "EPSG:4326"
    bbox: Optional[list[float]] = None    # [minx, miny, maxx, maxy] in target CRS
    feature_count: Optional[int] = None
    geometry_types: list[str] = Field(default_factory=list)
    size_bytes: int
    confidence: Literal["high", "medium", "low"] = "medium"
    warnings: list[str] = Field(default_factory=list)
    converted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: dict[str, Any] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    records: list[RecordMeta]
    summary: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    supported_types: list[str]
