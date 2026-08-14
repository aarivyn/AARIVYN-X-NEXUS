"""Vector data converters -> common representation (RFC 7946 GeoJSON, EPSG:4326).

Each converter returns (geojson: dict, meta: dict) where meta carries
source_crs, warnings, and any representation-specific extras. All coordinate
streams pass through `reproject` so output is always lon/lat WGS84.
"""
from __future__ import annotations

import json
import math
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Callable, Optional

from . import crs
from .geoutil import (
    arc_to_polyline,
    bbox_of_geojson,
    coerce_2d,
    feature_collection,
    geometry_types_of,
    make_feature,
    rings_to_polygons,
)
from .geoutil import ring_signed_area

KML_NS = "{http://www.opengis.net/kml/2.2}"
GPX_NS = "{http://www.topografix.com/GPX/1/1}"
OSM_NS = "{http://openstreetmap.org/osm/0.6}"

CoordTransform = Optional[Callable[[float, float], tuple[float, float]]]


# --------------------------------------------------------------------------
# shared plumbing
# --------------------------------------------------------------------------

def reproject(features: list[dict], transform: CoordTransform) -> list[dict]:
    """Rewrite every coordinate in a feature list through `transform`."""
    if transform is None:
        return features
    for f in features:
        _walk_geometry(f.get("geometry"), transform)
    return features


def _walk_geometry(geom, transform: CoordTransform) -> None:
    if not geom or not isinstance(geom, dict):
        return
    t = geom.get("type")
    if t == "GeometryCollection":
        for g in geom.get("geometries", []):
            _walk_geometry(g, transform)
        return
    coords = geom.get("coordinates")
    if not isinstance(coords, list):
        return

    def conv(pt: list) -> list:
        try:
            lon, lat = transform(pt[0], pt[1])
            return [lon, lat] + pt[2:]
        except Exception:
            return pt

    if t == "Point":
        geom["coordinates"] = conv(coords)
    elif t in ("LineString", "MultiPoint"):
        geom["coordinates"] = [conv(c) for c in coords]
    elif t == "MultiLineString":
        geom["coordinates"] = [[conv(c) for c in part] for part in coords]
    elif t == "Polygon":
        geom["coordinates"] = [[conv(c) for c in ring] for ring in coords]
    elif t == "MultiPolygon":
        geom["coordinates"] = [
            [[conv(c) for c in ring] for ring in poly] for poly in coords
        ]


def _coerce_rings(rings: list[list[list[float]]], warnings: list[str]) -> list[list[list[float]]]:
    """Normalize ring coordinates to 2-D [x, y] pairs."""
    return [coerce_2d(ring, warnings) for ring in rings]


# --------------------------------------------------------------------------
# GeoJSON / JSON
# --------------------------------------------------------------------------

def from_geojson(path: Path, data: Optional[bytes], source_crs: Optional[str],
                 warnings: list[str], transform: CoordTransform):
    raw = data.decode("utf-8", errors="replace") if data is not None else path.read_text(encoding="utf-8", errors="replace")
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        warnings.append(f"invalid GeoJSON: {e}")
        raise ValueError(f"invalid GeoJSON: {e}")

    gtype = obj.get("type")
    if gtype == "FeatureCollection":
        features = obj.get("features", [])
        for f in features:
            f.setdefault("properties", {})
        fc = obj
    elif gtype == "Feature":
        fc = {"type": "FeatureCollection", "features": [obj]}
    elif gtype in ("Point", "LineString", "Polygon", "MultiPoint", "MultiLineString",
                   "MultiPolygon", "GeometryCollection"):
        fc = {"type": "FeatureCollection", "features": [make_feature(obj, {})]}
    else:
        warnings.append(f"JSON is not GeoJSON (type={gtype!r}); stored as generic document")
        return None, {"warnings": warnings, "source_crs": source_crs, "as_document": True}

    fc.setdefault("features", [])
    # apply declared CRS if any (legacy "crs" member or per-feature)
    declared = obj.get("crs") or (obj.get("properties") or {}).get("crs")
    if declared and source_crs is None:
        try:
            c = declared.get("properties", {}).get("name", "")
            if c:
                source_crs = c.split(":", 1)[-1] if ":" in c else c
        except AttributeError:
            pass
    if source_crs and source_crs.upper() != "EPSG:4326":
        t = crs.transformer_to_wgs84(source_crs)
        if t is not None:
            reproject(fc["features"], t)
            warnings.append(f"reprojected from {source_crs} to EPSG:4326")
    return fc, {"warnings": warnings, "source_crs": source_crs}


def from_json(path: Path, data: Optional[bytes], source_crs: Optional[str],
              warnings: list[str]):
    """Bare .json: try GeoJSON first, otherwise tabular/document fallback."""
    fc, meta = from_geojson(path, data, source_crs, warnings, None)
    if fc is not None:
        return fc, meta
    # Not spatial: return the raw object so the caller stores it as attributes.
    raw = data.decode("utf-8", errors="replace") if data is not None else path.read_text(encoding="utf-8", errors="replace")
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        obj = {"raw_text": raw[:100_000]}
    return None, {"as_document": True, "document": obj, "warnings": warnings, "source_crs": source_crs}


# --------------------------------------------------------------------------
# Shapefile (pure-python pyshp)
# --------------------------------------------------------------------------

def from_shapefile(shp_path: Path, dbf_path: Optional[Path], prj_path: Optional[Path],
                   source_crs: Optional[str], warnings: list[str],
                   transform: CoordTransform):
    import shapefile as pyshp  # pyshp

    if dbf_path is not None and dbf_path.exists():
        reader = pyshp.Reader(shp=str(shp_path), dbf=str(dbf_path))
    else:
        reader = pyshp.Reader(shp=str(shp_path))
        warnings.append("no .dbf attribute table supplied; attributes omitted")

    # .prj file carries the authoritative source CRS
    if prj_path is not None and prj_path.exists() and source_crs is None:
        prj_text = prj_path.read_text(errors="replace").strip()
        parsed = crs.parse_crs(prj_text, warnings)
        if parsed:
            source_crs = parsed
            warnings.append(f"source CRS from .prj: {source_crs}")
            if transform is None:
                transform = crs.transformer_to_wgs84(source_crs)

    features: list[dict] = []
    shape_type = None
    try:
        for srec in reader.iterShapeRecords():
            shp = srec.shape
            rec = srec.record.as_dict() if srec.record else {}
            shape_type = shp.shapeType
            geom = _shapefile_geometry(shp, warnings)
            if geom is not None:
                features.append(make_feature(geom, rec))
    except Exception as e:  # pyshp raises various errors on malformed files
        warnings.append(f"shapefile read failed: {e}")
        raise ValueError(f"shapefile read failed: {e}") from e
    finally:
        reader.close()

    if not features:
        warnings.append("shapefile contained no parseable geometries")

    fc = feature_collection(features)
    reproject(fc["features"], transform)
    if transform is not None:
        warnings.append(f"reprojected from {source_crs} to EPSG:4326")
    return fc, {"warnings": warnings, "source_crs": source_crs, "shape_type": shape_type}


def _shapefile_geometry(shp, warnings: list[str]) -> Optional[dict]:
    import shapefile as pyshp

    st = shp.shapeType
    if st is None:
        return None
    base = st % 10 if st not in (0, 31) else st  # strip Z/M bit flags (2D=0..5)
    if base == 1:  # point
        pts = [[shp.points[0][0], shp.points[0][1]]] if shp.points else []
        if not pts:
            return None
        return {"type": "Point", "coordinates": pts[0]}
    if base == 3:  # polyline
        parts = _split_parts(shp)
        if len(parts) == 1:
            return {"type": "LineString", "coordinates": parts[0]}
        return {"type": "MultiLineString", "coordinates": parts}
    if base == 5:  # polygon
        rings = _split_parts(shp)
        rings = _coerce_rings(rings, warnings)
        polys = rings_to_polygons(rings, warnings)
        if len(polys) == 1:
            return polys[0]
        return {"type": "MultiPolygon", "coordinates": [p["coordinates"] for p in polys]}
    if base in (11, 13, 15, 21, 23, 25, 31):  # point/polyline/polygon with Z or M
        warnings.append(f"shape type {st} (Z/M) reduced to 2-D")
        return _shapefile_geometry(_strip_z(shp), warnings)
    warnings.append(f"unsupported shape type {st}; skipped")
    return None


def _split_parts(shp) -> list[list[list[float]]]:
    pts = [[p[0], p[1]] for p in shp.points]
    if not getattr(shp, "parts", None) or len(shp.parts) <= 1:
        return [pts] if pts else []
    parts = []
    idxs = list(shp.parts) + [len(pts)]
    for i in range(len(idxs) - 1):
        part = pts[idxs[i]:idxs[i + 1]]
        if part:
            parts.append(part)
    return parts


def _strip_z(shp):
    import shapefile as pyshp
    s = pyshp.Shape(shp.shapeType)
    s.points = [(p[0], p[1]) for p in shp.points]
    s.parts = list(shp.parts)
    return s


# --------------------------------------------------------------------------
# KML / KMZ
# --------------------------------------------------------------------------

def from_kml(path: Path, data: Optional[bytes], source_crs: Optional[str],
             warnings: list[str], transform: CoordTransform):
    raw = data.decode("utf-8", errors="replace") if data is not None else path.read_text(encoding="utf-8", errors="replace")
    # strip xmlns so ElementTree tags match the KML_NS constant regardless of version
    raw = re.sub(r'xmlns="[^"]*"', "", raw, count=1)
    root = ET.fromstring(raw)
    features: list[dict] = []
    for pm in root.iter("Placemark"):
        props = {}
        name_el = pm.find("name")
        desc_el = pm.find("description")
        if name_el is not None and name_el.text:
            props["name"] = name_el.text.strip()
        if desc_el is not None and desc_el.text:
            props["description"] = desc_el.text.strip()
        for el in pm:
            tag = el.tag.split("}")[-1]
            if tag in ("name", "description"):
                continue
            props[f"kml_{tag}"] = el.text.strip() if el.text else ""
        geom = _kml_geometry(pm, warnings)
        if geom is not None:
            features.append(make_feature(geom, props))
    if not features:
        warnings.append("no Placemark geometries found in KML")
    fc = feature_collection(features)
    reproject(fc["features"], transform)
    return fc, {"warnings": warnings, "source_crs": source_crs}


def _kml_geometry(pm, warnings: list[str]) -> Optional[dict]:
    def coord_str(el) -> list[list[float]]:
        txt = (el.text or "").strip()
        pts = []
        for tok in re.split(r"[\s]+", txt):
            parts = tok.split(",")
            if len(parts) >= 2:
                try:
                    pts.append([float(parts[0]), float(parts[1])])
                except ValueError:
                    continue
        return pts

    for g in pm.iter():
        tag = g.tag.split("}")[-1]
        if tag == "Point":
            c = g.find("coordinates")
            pts = coord_str(c) if c is not None else []
            if pts:
                return {"type": "Point", "coordinates": pts[0]}
        elif tag == "LineString":
            c = g.find("coordinates")
            pts = coord_str(c) if c is not None else []
            if len(pts) >= 2:
                return {"type": "LineString", "coordinates": pts}
        elif tag == "Polygon":
            outer = g.find("outerBoundaryIs/LinearRing/coordinates")
            inner = [h.find("LinearRing/coordinates") for h in g.findall("innerBoundaryIs")]
            rings = []
            if outer is not None:
                o = coord_str(outer)
                if len(o) >= 4:
                    rings.append(o)
            for h in inner:
                if h is not None:
                    i = coord_str(h)
                    if len(i) >= 4:
                        rings.append(i)
            if rings:
                polys = rings_to_polygons(rings, warnings)
                if len(polys) == 1:
                    return polys[0]
                return {"type": "MultiPolygon", "coordinates": [p["coordinates"] for p in polys]}
        elif tag == "MultiGeometry":
            subs = [_kml_geometry(g, warnings) for g in g]
            subs = [s for s in subs if s]
            if subs:
                return {"type": "GeometryCollection", "geometries": subs}
    return None


def from_kmz(path: Path, data: Optional[bytes], source_crs: Optional[str],
             warnings: list[str], transform: CoordTransform):
    with zipfile.ZipFile(path) as zf:
        kml_name = next((n for n in zf.namelist() if n.lower().endswith(".kml")), None)
        if kml_name is None:
            raise ValueError("KMZ contains no .kml file")
        kml_bytes = zf.read(kml_name)
    tmp = path.with_suffix(".kml")
    tmp.write_bytes(kml_bytes)
    try:
        return from_kml(tmp, None, source_crs, warnings, transform)
    finally:
        tmp.unlink(missing_ok=True)


# --------------------------------------------------------------------------
# GPX
# --------------------------------------------------------------------------

def from_gpx(path: Path, data: Optional[bytes], source_crs: Optional[str],
             warnings: list[str], transform: CoordTransform):
    raw = data.decode("utf-8", errors="replace") if data is not None else path.read_text(encoding="utf-8", errors="replace")
    root = ET.fromstring(raw)
    features: list[dict] = []

    def pt_el(el) -> Optional[list[float]]:
        lat = el.get("lat")
        lon = el.get("lon")
        if lat is None or lon is None:
            return None
        try:
            return [float(lon), float(lat)]
        except ValueError:
            return None

    def props_of(el) -> dict:
        props = {}
        for child in el:
            tag = child.tag.split("}")[-1]
            if child.text and child.text.strip():
                props[tag] = child.text.strip()
        return props

    for wpt in root.iter(f"{GPX_NS}wpt"):
        p = pt_el(wpt)
        if p:
            features.append(make_feature({"type": "Point", "coordinates": p}, props_of(wpt)))

    for trk in root.iter(f"{GPX_NS}trk"):
        name = (trk.find(f"{GPX_NS}name").text if trk.find(f"{GPX_NS}name") is not None else None)
        for seg in trk.iter(f"{GPX_NS}trkseg"):
            pts = [pt_el(t) for t in seg.findall(f"{GPX_NS}trkpt")]
            pts = [p for p in pts if p]
            if len(pts) >= 2:
                props = {"name": name} if name else {}
                features.append(make_feature({"type": "LineString", "coordinates": pts}, props))

    for rte in root.iter(f"{GPX_NS}rte"):
        pts = [pt_el(t) for t in rte.findall(f"{GPX_NS}rtept")]
        pts = [p for p in pts if p]
        if len(pts) >= 2:
            features.append(make_feature({"type": "LineString", "coordinates": pts}, {}))

    if not features:
        warnings.append("no waypoints/tracks/routes found in GPX")
    fc = feature_collection(features)
    reproject(fc["features"], transform)
    return fc, {"warnings": warnings, "source_crs": source_crs}


# --------------------------------------------------------------------------
# OSM XML / generic XML
# --------------------------------------------------------------------------

def from_osm(path: Path, data: Optional[bytes], source_crs: Optional[str],
             warnings: list[str], transform: CoordTransform):
    raw = data.decode("utf-8", errors="replace") if data is not None else path.read_text(encoding="utf-8", errors="replace")
    root = ET.fromstring(raw)
    nodes: dict[str, list[float]] = {}
    features: list[dict] = []

    for node in root.iter("node"):
        nid = node.get("id")
        lat, lon = node.get("lat"), node.get("lon")
        if nid and lat and lon:
            nodes[nid] = [float(lon), float(lat)]
            tags = {t.get("k"): t.get("v") for t in node.findall("tag") if t.get("k")}
            features.append(make_feature({"type": "Point", "coordinates": nodes[nid]}, tags or {}))

    def coords_of(nd_refs: list[str]) -> list[list[float]]:
        pts = [nodes[r] for r in nd_refs if r in nodes]
        return pts

    for way in root.iter("way"):
        nds = [nd.get("ref") for nd in way.findall("nd")]
        pts = coords_of(nds)
        if len(pts) < 2:
            continue
        tags = {t.get("k"): t.get("v") for t in way.findall("tag") if t.get("k")}
        closed = pts[0][:2] == pts[-1][:2]
        if closed and len(pts) >= 4:
            features.append(make_feature({"type": "Polygon", "coordinates": [pts]}, tags))
        else:
            features.append(make_feature({"type": "LineString", "coordinates": pts}, tags))

    if not features:
        warnings.append("no nodes/ways found in OSM data")
    fc = feature_collection(features)
    reproject(fc["features"], transform)
    return fc, {"warnings": warnings, "source_crs": source_crs}


# --------------------------------------------------------------------------
# DXF (CAD)
# --------------------------------------------------------------------------

def from_dxf(path: Path, data: Optional[bytes], source_crs: Optional[str],
             warnings: list[str], transform: CoordTransform):
    import ezdxf

    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    features: list[dict] = []
    units = doc.units
    if units and units != "Unknown":
        warnings.append(f"DXF drawing units: {units}; coordinates treated as-is (verify CRS)")

    for e in msp:
        t = e.dxftype()
        try:
            if t == "POINT":
                p = e.dxf.location
                features.append(make_feature({"type": "Point", "coordinates": [p.x, p.y]}, {}))
            elif t == "LINE":
                s, e2 = e.dxf.start, e.dxf.end
                features.append(make_feature({"type": "LineString", "coordinates": [[s.x, s.y], [e2.x, e2.y]]}, {}))
            elif t in ("LWPOLYLINE", "POLYLINE"):
                pts = [[p[0], p[1]] for p in e.get_points()]
                if e.closed and len(pts) >= 3:
                    pts.append(pts[0])
                    features.append(make_feature({"type": "Polygon", "coordinates": [pts]}, {}))
                elif len(pts) >= 2:
                    features.append(make_feature({"type": "LineString", "coordinates": pts}, {}))
            elif t == "CIRCLE":
                c = e.dxf.center
                pts = arc_to_polyline(c.x, c.y, e.dxf.radius, 0, 2 * math.pi)
                pts.append(pts[0])
                features.append(make_feature({"type": "Polygon", "coordinates": [pts]}, {}))
            elif t == "ARC":
                c = e.dxf.center
                a0, a1 = math.radians(e.dxf.start_angle), math.radians(e.dxf.end_angle)
                pts = arc_to_polyline(c.x, c.y, e.dxf.radius, a0, a1)
                if len(pts) >= 2:
                    features.append(make_feature({"type": "LineString", "coordinates": pts}, {}))
            elif t == "TEXT":
                p = e.dxf.insert
                features.append(make_feature(
                    {"type": "Point", "coordinates": [p.x, p.y]},
                    {"label": e.dxf.text, "layer": e.dxf.layer}))
            elif t == "INSERT":
                warnings.append(f"block INSERT {e.dxf.name!r} not exploded; skipped (run EXPLODE in CAD)")
        except Exception as exc:  # skip bad entities, keep going
            warnings.append(f"skipped {t} entity: {exc}")

    if not features:
        warnings.append("no supported entities found in DXF")
    fc = feature_collection(features)
    reproject(fc["features"], transform)
    if source_crs is None:
        warnings.append("DXF carries no CRS; assumed EPSG:4326 (verify!)")
    return fc, {"warnings": warnings, "source_crs": source_crs}


# --------------------------------------------------------------------------
# Generic XML fallback
# --------------------------------------------------------------------------

def from_xml(path: Path, data: Optional[bytes], source_crs: Optional[str],
             warnings: list[str]):
    raw = data.decode("utf-8", errors="replace") if data is not None else path.read_text(encoding="utf-8", errors="replace")
    warnings.append("unrecognized XML; stored as raw document")
    return None, {"as_document": True, "document": {"raw_text": raw[:100_000]},
                  "warnings": warnings, "source_crs": source_crs}
