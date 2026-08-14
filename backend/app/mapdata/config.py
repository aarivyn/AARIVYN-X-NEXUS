"""NEXUS ingest service configuration."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("NEXUS_DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
CONVERTED_DIR = DATA_DIR / "converted"

# Safety limits
MAX_UPLOAD_BYTES = int(os.environ.get("NEXUS_MAX_UPLOAD_BYTES", 2 * 1024**3))  # 2 GiB
MAX_EMBEDDED_GEOJSON_BYTES = int(os.environ.get("NEXUS_MAX_EMBEDDED_GEOJSON", 50 * 1024**2))  # 50 MB
MAX_EMBEDDED_TEXT_BYTES = int(os.environ.get("NEXUS_MAX_EMBEDDED_TEXT", 200 * 1024))  # 200 KB
MAX_RASTER_STATS_BYTES = 150 * 1024**2  # read pixel array for stats only below this
POINTCLOUD_PREVIEW_POINTS = 5_000
POINTCLOUD_STATS_CAP = 2_000_000  # read at most this many points for bounds/stats


def ensure_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    CONVERTED_DIR.mkdir(parents=True, exist_ok=True)
