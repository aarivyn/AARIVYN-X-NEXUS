"""CRS handling: source-CRS detection and reprojection to EPSG:4326.

Uses pyproj when available. Degrades gracefully: if pyproj is missing or the
source CRS is unknown, coordinates are passed through unchanged and a warning
is recorded (confidence dropped by the caller).
"""
from __future__ import annotations

from typing import Optional

try:
    from pyproj import CRS, Transformer
    _HAS_PYPROJ = True
except ImportError:  # pragma: no cover
    CRS = None  # type: ignore
    Transformer = None  # type: ignore
    _HAS_PYPROJ = False

WGS84 = "EPSG:4326"


def has_pyproj() -> bool:
    return _HAS_PYPROJ


def parse_crs(source: Optional[str], warnings: list[str]) -> Optional[str]:
    """Validate/normalize a user-supplied or file-supplied CRS string.

    Returns a normalized CRS string (e.g. 'EPSG:32633') or None when unknown.
    """
    if not source or not _HAS_PYPROJ:
        return None
    try:
        return CRS.from_user_input(source).to_string()
    except Exception:
        warnings.append(f"could not parse source CRS {source!r}; assuming EPSG:4326")
        return None


def transformer_to_wgs84(source_crs: str):
    """Return a callable f(x, y) -> (lon, lat) or None if not possible."""
    if not _HAS_PYPROJ:
        return None
    try:
        t = Transformer.from_crs(source_crs, WGS84, always_xy=True)
        return t.transform
    except Exception:
        return None


def transform_coords(coords: list[list[float]], transform) -> list[list[float]]:
    if transform is None:
        return coords
    out = []
    for x, y in coords:
        try:
            lon, lat = transform(x, y)
            out.append([lon, lat])
        except Exception:
            out.append([x, y])
    return out


def transform_bbox(bbox: list[float], source_crs: str) -> list[float] | None:
    """Transform a [minx, miny, maxx, maxy] bbox by transforming its corners."""
    t = transformer_to_wgs84(source_crs)
    if t is None:
        return None
    corners = [(bbox[0], bbox[1]), (bbox[2], bbox[1]), (bbox[2], bbox[3]), (bbox[0], bbox[3])]
    pts = transform_coords(corners, t)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [min(xs), min(ys), max(xs), max(ys)]
