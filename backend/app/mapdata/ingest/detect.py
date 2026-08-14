"""File-type detection: extension hints crossed with magic-byte signatures.

Returns a `SourceType` string used by the conversion dispatcher. Detection is
defence-in-depth: extension alone decides only when the signature is ambiguous
or unavailable; known magic bytes always win.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

MAGIC_PDF = b"%PDF"
MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
MAGIC_JPEG = b"\xff\xd8\xff"
MAGIC_TIFF_LE = b"II*\x00"
MAGIC_TIFF_BE = b"MM\x00*"
MAGIC_ZIP = b"PK\x03\x04"
MAGIC_SQLITE = b"SQLite format 3\x00"
MAGIC_GZIP = b"\x1f\x8b"
MAGIC_JP2 = b"\x00\x00\x00\x0cjP  \r\n\x87\n"

EXT_TO_TYPE = {
    ".geojson": "geojson",
    ".json": "json",
    ".shp": "shapefile", ".shx": "shapefile", ".dbf": "shapefile",
    ".prj": "shapefile",
    ".kml": "kml",
    ".kmz": "kmz",
    ".gpx": "gpx",
    ".osm": "osm",
    ".xml": "xml",
    ".pbf": "osm_pbf",
    ".dxf": "dxf",
    ".dwg": "dwg",
    ".tif": "geotiff", ".tiff": "geotiff",
    ".asc": "ascii_grid",
    ".mbtiles": "mbtiles",
    ".jpg": "image", ".jpeg": "image",
    ".png": "image",
    ".jp2": "image",
    ".las": "las", ".laz": "laz",
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".pdf": "pdf",
    ".docx": "docx",
    ".zip": "zip",
}

# ASCII-grid files carry no magic; a .asc that looks like ESRI ASCII wins.
# GeoJSON/JSON/KML/GPX/OSM are text; sniff their content below.


def detect(filename: str, head: bytes, ext: str | None = None) -> str:
    ext = (ext or Path(filename).suffix).lower()
    head = head[:64]

    # Binary magic bytes first (unambiguous).
    if head.startswith(MAGIC_PDF):
        return "pdf"
    if head.startswith(MAGIC_PNG):
        return "image"
    if head.startswith(MAGIC_JPEG):
        return "image"
    if head.startswith(MAGIC_TIFF_LE) or head.startswith(MAGIC_TIFF_BE):
        return "geotiff"
    if head.startswith(MAGIC_SQLITE):
        # sqlite container: MBTiles has a metadata table -> mbtiles
        return "mbtiles" if ext == ".mbtiles" else "sqlite"
    if head.startswith(MAGIC_ZIP):
        return _sniff_zip(filename)
    if head.startswith(MAGIC_GZIP):
        # compressed LAZ point clouds are gzip-based
        return "laz" if ext == ".laz" else "unknown"
    if head.startswith(MAGIC_JP2):
        return "image"

    # Text formats: sniff first non-whitespace bytes.
    stripped = head.lstrip(b"\xef\xbb\xbf \t\r\n")  # allow UTF-8 BOM
    if stripped.startswith(b"{") or stripped.startswith(b"["):
        return _sniff_json(filename, ext)
    if stripped.startswith(b"<"):
        return _sniff_xml(filename, head)

    # Fall back to extension for remaining text-ish types.
    if ext in EXT_TO_TYPE:
        return EXT_TO_TYPE[ext]
    if ext == ".asc":
        return "ascii_grid"
    return "unknown"


def _sniff_zip(filename: str) -> str:
    """Peek inside a zip to tell KMZ / DOCX / XLSX / generic bundle apart."""
    name = filename.lower()
    try:
        with zipfile.ZipFile(filename) as zf:
            names = [n.lower() for n in zf.namelist()]
    except zipfile.BadZipFile:
        return "unknown"
    if any(n.endswith(".kml") for n in names):
        return "kmz"
    if any(n.startswith("word/") for n in names):
        return "docx"
    if any(n.endswith(".shp") for n in names):
        return "zip"
    if name.endswith(".kmz"):
        return "kmz"
    if name.endswith(".xlsx") or any(n.startswith("xl/") for n in names):
        return "xlsx"
    if name.endswith(".docx"):
        return "docx"
    return "zip"


def _sniff_json(filename: str, ext: str | None) -> str:
    # .geojson is explicit; a bare .json could still be GeoJSON (API pulls).
    return "geojson" if ext == ".geojson" else "json"


def _sniff_xml(filename: str, head: bytes) -> str:
    low = head.lower()
    if b"<kml" in low or b"openGIS" in low.replace(b" ", b""):
        return "kml"
    if b"gpx" in low:
        return "gpx"
    if b"<osm" in low or b"<osmchange" in low:
        return "osm"
    if b"<?xml" in low or b"<" in low:
        return "xml"
    return "unknown"
