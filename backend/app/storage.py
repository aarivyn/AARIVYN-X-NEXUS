"""Persistent storage for uploaded files and converted records."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import config

SUPPORTED_EXTENSIONS = {
    # vectors
    "geojson", "json", "shp", "shx", "dbf", "prj", "kml", "kmz", "gpx",
    "osm", "xml", "pbf", "dxf", "dwg",
    # rasters / imagery
    "tif", "tiff", "asc", "mbtiles", "jpg", "jpeg", "png", "jp2",
    # point clouds
    "las", "laz",
    # tabular
    "csv", "xlsx",
    # documents
    "pdf", "docx",
    # bundles
    "zip",
}


def save_upload(record_id: str, filename: str, content: bytes) -> Path:
    """Persist a raw uploaded file under data/uploads/<record_id>/."""
    safe_name = Path(filename).name
    dest = config.UPLOAD_DIR / record_id / safe_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    return dest


def save_record(record: dict) -> Path:
    """Persist a converted record as JSON under data/converted/<id>.json."""
    dest = config.CONVERTED_DIR / f"{record['id']}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(record, default=str, indent=2))
    return dest


def read_record(record_id: str) -> dict | None:
    path = config.CONVERTED_DIR / f"{record_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def list_records() -> list[dict]:
    out = []
    for p in sorted(config.CONVERTED_DIR.glob("*.json")):
        try:
            out.append(json.loads(p.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return out


def delete_record(record_id: str) -> bool:
    removed = False
    for p in (config.CONVERTED_DIR / f"{record_id}.json", config.UPLOAD_DIR / record_id):
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            removed = True
    return removed
