"""Tabular data converters (CSV, XLSX) -> rows + optional point features.

Spatialization heuristic: columns whose names look like latitude/longitude are
turned into GeoJSON Point features; a WKT-like 'geometry' column is parsed for
POINT/LINESTRING/POLYGON. Files with no spatial columns become attribute-only
records (confidence low) so no information is silently dropped.
"""
from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Optional

from .geoutil import feature_collection, make_feature

LAT_KEYS = re.compile(r"^(lat|latitude|y_coord|north|northing|y)$", re.I)
LON_KEYS = re.compile(r"^(lon|lng|long|longitude|x_coord|east|easting|x)$", re.I)
WKT_POINT = re.compile(r"^\s*POINT\s*\(\s*([-+0-9.eE]+)\s+([-+0-9.eE]+)", re.I)
WKT_LINE = re.compile(r"^\s*LINESTRING\s*\((.*)\)\s*$", re.I)
WKT_POLY = re.compile(r"^\s*POLYGON\s*\((.*)\)\s*$", re.I)


def _clean(v) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _find_spatial_columns(columns: list[str]) -> tuple[Optional[int], Optional[int], Optional[int]]:
    lat_i = lon_i = wkt_i = None
    for i, c in enumerate(columns):
        cc = str(c).strip()
        if LAT_KEYS.match(cc) and lat_i is None:
            lat_i = i
        elif LON_KEYS.match(cc) and lon_i is None:
            lon_i = i
        elif cc.lower() in ("geometry", "geom", "wkt", "the_geom") and wkt_i is None:
            wkt_i = i
    return lat_i, lon_i, wkt_i


def _parse_wkt(wkt: str):
    wkt = wkt.strip()
    m = WKT_POINT.match(wkt)
    if m:
        return {"type": "Point", "coordinates": [float(m.group(1)), float(m.group(2))]}
    m = WKT_LINE.match(wkt)
    if m:
        pts = _wkt_coords(m.group(1))
        if len(pts) >= 2:
            return {"type": "LineString", "coordinates": pts}
    m = WKT_POLY.match(wkt)
    if m:
        rings = [r.strip() for r in _split_rings(m.group(1))]
        coords = []
        for ring in rings:
            pts = _wkt_coords(ring)
            if len(pts) >= 4:
                coords.append(pts)
        if coords:
            return {"type": "Polygon", "coordinates": coords}
    return None


def _split_rings(inner: str) -> list[str]:
    """Split a POLYGON body into rings (handles nested parens simply)."""
    rings, depth, cur = [], 0, []
    for ch in inner:
        if ch == "(":
            depth += 1
            if depth == 1:
                cur = []
        elif ch == ")":
            depth -= 1
            if depth == 0:
                rings.append("".join(cur))
        else:
            cur.append(ch)
    return rings


def _wkt_coords(body: str) -> list[list[float]]:
    pts = []
    for m in re.finditer(r"([-+0-9.eE]+)\s+([-+0-9.eE]+)", body):
        pts.append([float(m.group(1)), float(m.group(2))])
    return pts


def _rows_to_record(rows: list[dict], columns: list[str], source_name: str,
                    warnings: list[str], src_crs: Optional[str]):
    lat_i, lon_i, wkt_i = _find_spatial_columns(columns)
    features = []
    spatial = False

    for row in rows:
        geom = None
        if lat_i is not None and lon_i is not None:
            try:
                lat = float(row[columns[lat_i]])
                lon = float(row[columns[lon_i]])
                geom = {"type": "Point", "coordinates": [lon, lat]}
                spatial = True
            except (ValueError, TypeError, KeyError):
                pass
        if geom is None and wkt_i is not None:
            wkt = _clean(row.get(columns[wkt_i]))
            if wkt:
                g = _parse_wkt(wkt)
                if g:
                    geom = g
                    spatial = True
        if geom is not None:
            features.append(make_feature(geom, row))

    data = {
        "format": source_name,
        "columns": columns,
        "row_count": len(rows),
        "spatial_columns_detected": spatial,
        "geojson": feature_collection(features) if spatial else None,
    }
    bbox = None
    if spatial:
        from .geoutil import bbox_of_geojson
        bbox = bbox_of_geojson(data["geojson"])

    confidence = "high"
    if not spatial:
        confidence = "low"
        warnings.append("no lat/lon or WKT geometry columns found; stored as attribute table only")
    elif lat_i is not None and lon_i is not None:
        warnings.append(f"geocoded {len(features)}/{len(rows)} rows from "
                        f"{columns[lat_i]!r}/{columns[lon_i]!r}")

    return {
        "data": data, "bbox": bbox, "source_crs": src_crs, "warnings": warnings,
        "confidence": confidence,
        "feature_count": len(features) if spatial else None,
        "geometry_types": ["Point"] if spatial else [],
    }


def from_csv(path: Path, data: Optional[bytes], src_crs: Optional[str],
             warnings: list[str]) -> dict:
    raw = data.decode("utf-8", errors="replace") if data is not None else path.read_text(encoding="utf-8", errors="replace")
    # dialect sniffing: tolerate ; and tab separators, skip comment/blank lines
    sample = raw[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(io.StringIO(raw), dialect)
    rows: list[dict] = []
    columns: list[str] = []
    for r in reader:
        if not r or (r[0].strip().startswith("#") and not columns):
            continue
        if not columns:
            columns = [c.strip() for c in r]
            continue
        if len(r) < len(columns):
            r = r + [""] * (len(columns) - len(r))
        rows.append({c: _clean(v) for c, v in zip(columns, r[:len(columns)])})
        if len(rows) >= 200_000:
            warnings.append("CSV truncated at 200,000 rows")
            break
    return _rows_to_record(rows, columns, "csv", warnings, src_crs)


def from_xlsx(path: Path, src_crs: Optional[str], warnings: list[str]) -> dict:
    try:
        import openpyxl
    except ImportError as e:  # pragma: no cover
        raise ValueError("openpyxl not installed; cannot read .xlsx") from e

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows: list[dict] = []
    columns: list[str] = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            columns = [str(c).strip() if c is not None else f"col_{j}" for j, c in enumerate(row)]
            continue
        if row is None:
            continue
        rows.append({c: _clean(v) for c, v in zip(columns, row)})
        if len(rows) >= 100_000:
            warnings.append("XLSX truncated at 100,000 rows")
            break
    wb.close()
    if not columns:
        raise ValueError("XLSX contains no header row")
    return _rows_to_record(rows, columns, "xlsx", warnings, src_crs)
