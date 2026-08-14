"""Geometry helpers shared by converters."""
from __future__ import annotations

import math
from typing import Any, Iterable


def ring_signed_area(ring: list[list[float]]) -> float:
    """Shoelace area; positive = clockwise (shapefile outer-ring convention)."""
    n = len(ring)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n - 1):
        x1, y1 = ring[i][:2]
        x2, y2 = ring[i + 1][:2]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def ring_contains(outer: list[list[float]], inner: list[list[float]]) -> bool:
    """Point-in-polygon test of inner's first vertex against outer ring."""
    x, y = inner[0][:2]
    inside = False
    n = len(outer)
    j = n - 1
    for i in range(n):
        xi, yi = outer[i][:2]
        xj, yj = outer[j][:2]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def rings_to_polygons(rings: list[list[list[float]]], warnings: list[str]) -> list[dict]:
    """Group shapefile-style rings (CW outer, CCW holes) into GeoJSON polygons."""
    if not rings:
        return []
    polys: list[list[list[list[float]]]] = []  # list of polygons; each = [outer, *holes]
    for ring in rings:
        if len(ring) < 4:
            continue
        area = ring_signed_area(ring)
        if area >= 0:  # clockwise -> outer ring
            polys.append([ring])
        else:
            if polys:
                polys[-1].append(ring)
            else:
                # hole before any outer ring: treat as degenerate outer
                polys.append([ring])
    out = []
    for poly in polys:
        outer = poly[0]
        holes = poly[1:]
        # sanity: a hole must actually sit inside its outer ring
        holes = [h for h in holes if ring_contains(outer, h)]
        if len(holes) > 1:
            # multiple holes: sort so any nested rings are attributed correctly
            holes.sort(key=lambda h: abs(ring_signed_area(h)), reverse=True)
        coords = [outer] + holes
        out.append({"type": "Polygon", "coordinates": coords})
    return out


def make_feature(geom: dict, props: dict | None = None) -> dict:
    return {"type": "Feature", "geometry": geom, "properties": props or {}}


def feature_collection(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}


def bbox_of_coords(coords: Iterable[list[float]]) -> list[float] | None:
    xs, ys = [], []
    for c in coords:
        if len(c) >= 2:
            xs.append(c[0])
            ys.append(c[1])
    if not xs:
        return None
    return [min(xs), min(ys), max(xs), max(ys)]


def bbox_of_geojson(obj: dict) -> list[float] | None:
    """Bounding box of any GeoJSON object (coordinate walk)."""
    coords: list[float] = []

    def walk(geom: dict) -> None:
        t = geom.get("type")
        if t == "GeometryCollection":
            for g in geom.get("geometries", []):
                walk(g)
            return
        c = geom.get("coordinates")
        if not isinstance(c, list):
            return
        flat(c)

    def flat(c: Any) -> None:
        if c and isinstance(c[0], (int, float)):
            coords.extend([c[0], c[1]])
        else:
            for item in c:
                flat(item)

    if obj.get("type") == "Feature":
        walk(obj.get("geometry") or {})
    elif obj.get("type") == "FeatureCollection":
        for f in obj.get("features", []):
            walk(f.get("geometry") or {})
    else:
        walk(obj)
    if not coords:
        return None
    xs = coords[0::2]
    ys = coords[1::2]
    return [min(xs), min(ys), max(xs), max(ys)]


def geometry_types_of(geojson: dict) -> list[str]:
    types: set[str] = set()
    features = geojson.get("features", []) if geojson.get("type") == "FeatureCollection" else (
        [geojson] if geojson.get("type") == "Feature" else []
    )
    for f in features:
        g = f.get("geometry") or {}
        t = g.get("type")
        if t == "GeometryCollection":
            types.update(gg.get("type", "") for gg in g.get("geometries", []))
        elif t:
            types.add(t)
    return sorted(types)


def arc_to_polyline(cx: float, cy: float, r: float, a0: float, a1: float,
                    segments: int = 48) -> list[list[float]]:
    """Approximate an arc/circle as a polyline of [x, y] pairs."""
    if a1 < a0:
        a1 += 2 * math.pi
    n = max(4, int(segments * (a1 - a0) / (2 * math.pi)))
    pts = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        pts.append([round(cx + r * math.cos(a), 6), round(cy + r * math.sin(a), 6)])
    return pts


def coerce_2d(coords: list[list[float]], warnings: list[str], keep_z: bool = False) -> list[list[float]]:
    """Strip Z/M from coordinate tuples; optionally keep Z in a side channel."""
    out = []
    for c in coords:
        if len(c) >= 2:
            out.append([c[0], c[1]])
        elif len(c) == 1:
            warnings.append("dropped 1-D coordinate")
    return out
