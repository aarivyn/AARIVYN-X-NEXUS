"""Conversion dispatcher: turns raw uploaded files into the NEXUS common
representation (a typed Record with embedded GeoJSON / raster / text payloads).

Bundles (shapefile sets, zips, KMZ) are resolved before conversion; files that
cannot be converted are stored raw and reported as representation=unsupported
rather than rejected, so the endpoint accepts the full inputs.txt spectrum.

Every record carries a `usage` describing what the data is FOR (e.g. road
network, existing utility lines, terrain). It is taken from the caller when
explicitly provided, otherwise inferred from the filename and file type; an
inferred value is always surfaced as a warning so it can be audited/overridden.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Optional

from .. import config, schemas, storage
from . import crs, detect, document, pointcloud, raster, tabular, vector

# source_type -> converter
_CONVERTERS = {
    "geojson": vector.from_geojson,
    "json": vector.from_json,
    "kml": vector.from_kml,
    "kmz": vector.from_kmz,
    "gpx": vector.from_gpx,
    "osm": vector.from_osm,
    "xml": vector.from_xml,
    "dxf": vector.from_dxf,
}

# source types accepted but stored raw (conversion needs external tooling)
_STORE_RAW = {
    "osm_pbf": "OSM PBF needs pyosmium/osmium; stored raw",
    "dwg": "DWG needs ODA File Converter; stored raw",
}

# rasters / point clouds / tabular / documents use their own signatures
_RASTER = {"geotiff": raster.from_geotiff, "ascii_grid": raster.from_ascii_grid,
           "image": raster.from_image, "mbtiles": raster.from_mbtiles}
_TABULAR = {"csv": tabular.from_csv, "xlsx": tabular.from_xlsx}
_DOCUMENT = {"pdf": document.from_pdf, "docx": document.from_docx}
_POINTCLOUD = {"las": pointcloud.from_pointcloud, "laz": pointcloud.from_pointcloud}


# --------------------------------------------------------------------------
# usage inference
# --------------------------------------------------------------------------

# Ordered: first matching keyword wins, so specific terms precede generic ones.
USAGE_KEYWORDS: list[tuple[str, str]] = [
    # base maps
    ("right-of-way", "utility_easement"),
    ("asbuilt", "utility_network"),
    ("as-built", "utility_network"),
    ("watermain", "utility_network"),
    ("water main", "utility_network"),
    ("groundwater", "groundwater_data"),
    ("road", "road_network"),
    ("rail", "railway_network"),
    ("topo", "topographic_map"),
    ("terrain", "terrain"),
    ("elevation", "terrain"),
    ("lidar", "terrain"),
    ("dem_", "terrain"),
    ("boundary", "administrative_boundary"),
    ("parcel", "administrative_boundary"),
    # utilities
    ("sewer", "utility_network"),
    ("utility", "utility_network"),
    ("gas_line", "utility_network"),
    ("gasline", "utility_network"),
    ("electrical", "utility_network"),
    ("electric", "utility_network"),
    ("telecom", "utility_network"),
    ("conduit", "utility_network"),
    ("easement", "utility_easement"),
    # imagery
    ("aerial", "aerial_imagery"),
    ("drone", "aerial_imagery"),
    ("ortho", "aerial_imagery"),
    ("satellite", "satellite_imagery"),
    # geological / environmental
    ("soil", "soil_data"),
    ("geotech", "geotechnical_report"),
    ("borehole", "geotechnical_report"),
    ("aquifer", "groundwater_data"),
    ("hydrology", "groundwater_data"),
    ("protected", "protected_zone"),
    ("sensitive", "protected_zone"),
    ("environmental", "protected_zone"),
    # water demand / supply
    ("population", "population_data"),
    ("household", "population_data"),
    ("census", "population_data"),
    ("source", "water_source_spec"),
    ("well", "water_source_spec"),
    ("spring", "water_source_spec"),
    ("capacity", "water_source_spec"),
    ("demand", "demand_projection"),
    ("projection", "demand_projection"),
    # field observations
    ("notes", "field_notes"),
    ("survey", "field_survey"),
    ("waypoint", "gps_waypoints"),
    ("track", "gps_waypoints"),
    # engineering / constraints
    ("pipe", "pipe_specs"),
    ("spec", "pipe_specs"),
    ("material", "pipe_specs"),
    ("catalog", "pipe_specs"),
    ("budget", "budget"),
    ("cost", "budget"),
    ("equipment", "equipment_inventory"),
    ("inventory", "equipment_inventory"),
    ("permit", "regulatory_permits"),
    ("regulatory", "regulatory_permits"),
    # weather
    ("weather", "weather_data"),
    ("climate", "weather_data"),
    ("precip", "weather_data"),
    ("rainfall", "weather_data"),
    ("map", "topographic_map"),
]

# Type-level defaults used when the filename gives no signal.
TYPE_USAGE_DEFAULTS: dict[str, str] = {
    "gpx": "gps_waypoints",
    "las": "terrain",
    "laz": "terrain",
    "asc": "terrain",
    "mbtiles": "base_map_tiles",
}


def resolve_usage(filename: str, stype: str, warnings: list[str],
                  explicit: Optional[str] = None) -> str:
    """Determine the record's usage: explicit > filename keyword > type default."""
    if explicit:
        return explicit
    low = filename.lower()
    for keyword, usage in USAGE_KEYWORDS:
        if keyword in low:
            warnings.append(
                f"usage inferred from filename: {usage!r} (override with usage= form field)")
            return usage
    if stype in TYPE_USAGE_DEFAULTS:
        usage = TYPE_USAGE_DEFAULTS[stype]
        warnings.append(
            f"usage inferred from file type {stype!r}: {usage!r} (override with usage= form field)")
        return usage
    return "general"


class ConversionError(Exception):
    pass


def _read_head(path: Path) -> bytes:
    with path.open("rb") as fh:
        return fh.read(256)


def convert_file(path: Path, category: str, source_crs: Optional[str],
                 name: Optional[str] = None, usage: Optional[str] = None) -> schemas.RecordMeta:
    """Convert a single stored file into a common-representation record."""
    head = _read_head(path)
    stype = detect.detect(str(path), head)
    warnings: list[str] = []
    src_crs = crs.parse_crs(source_crs, warnings) if source_crs else None
    usage = resolve_usage(name or path.name, stype, warnings, usage)

    # --- resolvable-but-raw types -------------------------------------
    if stype in _STORE_RAW:
        warnings.append(_STORE_RAW[stype])
        return _unsupported_record(path, stype, category, name, warnings, usage)

    if stype == "zip":
        return _convert_zip(path, category, src_crs, name, usage)

    if stype == "shapefile":
        return _shapefile_record(path, category, src_crs, name, usage)

    if stype not in _CONVERTERS and stype not in _RASTER and stype not in _TABULAR \
            and stype not in _DOCUMENT and stype not in _POINTCLOUD:
        warnings.append(f"unrecognized type {stype!r}; stored raw")
        return _unsupported_record(path, stype, category, name, warnings, usage)

    try:
        if stype in _CONVERTERS:
            return _vector_record(path, stype, category, src_crs, name, warnings, usage)
        if stype in _RASTER:
            result = _RASTER[stype](path, src_crs, warnings)
            return _build_record(path, stype, category, name, "raster", result, usage)
        if stype in _TABULAR:
            if stype == "csv":
                result = tabular.from_csv(path, None, src_crs, warnings)
            else:
                result = tabular.from_xlsx(path, src_crs, warnings)
            return _build_record(path, stype, category, name, "tabular", result, usage)
        if stype in _DOCUMENT:
            result = _DOCUMENT[stype](path, src_crs, warnings)
            return _build_record(path, stype, category, name, "document", result, usage)
        if stype in _POINTCLOUD:
            result = _POINTCLOUD[stype](path, src_crs, warnings)
            return _build_record(path, stype, category, name, "point_cloud", result, usage)
    except (ValueError, ConversionError) as e:
        warnings.append(f"conversion failed ({e}); stored raw")
        return _unsupported_record(path, stype, category, name, warnings, usage)
    except Exception as e:  # defensive: never let one file kill the request
        warnings.append(f"unexpected conversion error ({type(e).__name__}: {e}); stored raw")
        return _unsupported_record(path, stype, category, name, warnings, usage)

    raise ConversionError(f"no converter for {stype}")


# --------------------------------------------------------------------------
# vector path
# --------------------------------------------------------------------------

def _vector_record(path: Path, stype: str, category: str, src_crs: Optional[str],
                   name: Optional[str], warnings: list[str],
                   usage: str) -> schemas.RecordMeta:
    # reprojection happens inside the converter via source_crs; build transform
    # lazily so converters that don't accept it (geojson/json/xml) still work
    transform = crs.transformer_to_wgs84(src_crs) if src_crs else None
    converter = _CONVERTERS[stype]
    if stype == "geojson":
        fc, meta = vector.from_geojson(path, None, src_crs, warnings, transform)
    elif stype == "json":
        fc, meta = vector.from_json(path, None, src_crs, warnings)
    elif stype == "xml":
        fc, meta = vector.from_xml(path, None, src_crs, warnings)
    else:
        fc, meta = converter(path, None, src_crs, warnings, transform)

    # non-spatial JSON/XML -> document-style record
    if fc is None and meta.get("as_document"):
        doc = meta.get("document", {})
        data = {"format": stype, "content": doc if isinstance(doc, dict) else {"raw": str(doc)}}
        return _build_record(path, stype, category, name, "document",
                             {"data": data, "warnings": meta.get("warnings", warnings),
                              "source_crs": meta.get("source_crs"), "confidence": "low"},
                             usage)

    fc.setdefault("features", [])
    from .geoutil import bbox_of_geojson, geometry_types_of
    bbox = bbox_of_geojson(fc)
    gtypes = geometry_types_of(fc)
    if not fc["features"]:
        warnings.append("no features produced")

    # keep embedded GeoJSON within a sane size for API responses
    embedded = fc
    fc_bytes = len(json.dumps(fc))
    if fc_bytes > config.MAX_EMBEDDED_GEOJSON_BYTES:
        warnings.append(f"GeoJSON too large to embed ({fc_bytes} bytes); included feature summary only")
        embedded = {
            "type": "FeatureCollection",
            "features": [],
            "note": "payload stored on disk; fetch via /api/v1/maps/{id}/geojson",
            "feature_count": len(fc["features"]),
        }
        _store_geojson_payload(path.stem, fc)

    data = {
        "format": stype,
        "crs": "EPSG:4326",
        "geojson": embedded,
    }
    meta_warnings = meta.get("warnings", [])
    for w in meta_warnings:
        if w not in warnings:
            warnings.append(w)
    return schemas.RecordMeta(
        id=path.parent.name,
        name=name or path.name,
        category=category,
        usage=usage,
        source_type=stype,
        source_filename=path.name,
        representation="vector_geojson",
        source_crs=meta.get("source_crs") or src_crs,
        target_crs="EPSG:4326",
        bbox=bbox,
        feature_count=len(fc["features"]),
        geometry_types=gtypes,
        size_bytes=path.stat().st_size,
        confidence="high" if fc["features"] else "low",
        warnings=warnings,
        data=data,
    )


def _store_geojson_payload(stem: str, fc: dict) -> None:
    dest = config.CONVERTED_DIR / f"geojson_{stem}.json"
    dest.write_text(json.dumps(fc))


# --------------------------------------------------------------------------
# shared record assembly
# --------------------------------------------------------------------------

def _build_record(path: Path, stype: str, category: str, name: Optional[str],
                  representation: str, result: dict, usage: str) -> schemas.RecordMeta:
    return schemas.RecordMeta(
        id=path.parent.name,
        name=name or path.name,
        category=category,
        usage=usage,
        source_type=stype,
        source_filename=path.name,
        representation=representation,
        source_crs=result.get("source_crs"),
        target_crs="EPSG:4326",
        bbox=result.get("bbox"),
        feature_count=result.get("feature_count"),
        geometry_types=result.get("geometry_types", []),
        size_bytes=path.stat().st_size,
        confidence=result.get("confidence", "medium"),
        warnings=result.get("warnings", []),
        data=result.get("data", {}),
    )


def _unsupported_record(path: Path, stype: str, category: str, name: Optional[str],
                        warnings: list[str], usage: str) -> schemas.RecordMeta:
    return schemas.RecordMeta(
        id=path.parent.name,
        name=name or path.name,
        category=category,
        usage=usage,
        source_type=stype,
        source_filename=path.name,
        representation="unsupported",
        size_bytes=path.stat().st_size,
        confidence="low",
        warnings=warnings,
        data={"format": stype, "stored_file": str(path),
              "note": "file stored as-is; no converter in this build"},
    )


# --------------------------------------------------------------------------
# bundles: shapefile sets & zips
# --------------------------------------------------------------------------

def _convert_zip(path: Path, category: str, src_crs: Optional[str],
                 name: Optional[str], usage: str) -> schemas.RecordMeta:
    """A .zip is treated as a dataset bundle: convert contained files, return
    the primary record (first shapefile if any, else the most relevant file)."""
    extract_dir = path.parent / "bundle"
    extract_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(path) as zf:
        zf.extractall(extract_dir)
    files = [p for p in extract_dir.rglob("*") if p.is_file()]
    # guard against zip-slip: only files inside extract_dir
    files = [p for p in files if extract_dir in p.parents or p.parent == extract_dir]

    shp = next((p for p in files if p.suffix.lower() == ".shp"), None)
    if shp is not None:
        rec = _shapefile_record(shp, category, src_crs, name, usage)
        rec.id = path.parent.name
        return rec
    # fall back: convert the first recognized file
    for p in files:
        stype = detect.detect(p.name, _read_head(p))
        if stype not in ("unknown", "zip"):
            try:
                rec = convert_file(p, category, None, name, usage)
                rec.id = path.parent.name
                return rec
            except Exception:
                continue
    warnings = ["zip contained no convertible files"]
    return _unsupported_record(path, "zip", category, name, warnings, usage)


def _shapefile_record(shp: Path, category: str, src_crs: Optional[str],
                      name: Optional[str], usage: str) -> schemas.RecordMeta:
    stem = shp.with_suffix("")
    dbf = Path(f"{stem}.dbf") if Path(f"{stem}.dbf").exists() else None
    prj = Path(f"{stem}.prj") if Path(f"{stem}.prj").exists() else None
    shx = Path(f"{stem}.shx")
    warnings: list[str] = []

    if not shx.exists():
        warnings.append(
            "shapefile needs its .shx index (and ideally .dbf/.prj); "
            "upload the whole set as separate files or a .zip bundle")
        return _unsupported_record(shp, "shapefile", category, name, warnings, usage)

    parsed = crs.parse_crs(src_crs, warnings) if src_crs else None
    transform = crs.transformer_to_wgs84(parsed) if parsed else None
    try:
        fc, meta = vector.from_shapefile(shp, dbf, prj, parsed, warnings, transform)
    except Exception as e:
        warnings.append(f"shapefile read failed ({e}); stored raw")
        return _unsupported_record(shp, "shapefile", category, name, warnings, usage)
    from .geoutil import bbox_of_geojson, geometry_types_of
    bbox = bbox_of_geojson(fc)
    gtypes = geometry_types_of(fc)
    data = {"format": "shapefile", "crs": "EPSG:4326", "geojson": fc}
    return schemas.RecordMeta(
        id=shp.parent.name,
        name=name or shp.name,
        category=category,
        usage=usage,
        source_type="shapefile",
        source_filename=shp.name,
        representation="vector_geojson",
        source_crs=meta.get("source_crs") or parsed,
        target_crs="EPSG:4326",
        bbox=bbox,
        feature_count=len(fc["features"]),
        geometry_types=gtypes,
        size_bytes=shp.stat().st_size,
        confidence="high" if fc["features"] else "low",
        warnings=warnings,
        data=data,
    )


def shapefile_record_from_files(files: list[Path], category: str,
                                src_crs: Optional[str], name: Optional[str],
                                usage: Optional[str] = None) -> schemas.RecordMeta:
    """Assemble a shapefile record from separately uploaded .shp/.dbf/.prj files."""
    shp = next(p for p in files if p.suffix.lower() == ".shp")
    warnings: list[str] = []
    stype = "shapefile"
    usage = resolve_usage(name or shp.name, stype, warnings, usage)
    rec = _shapefile_record(shp, category, src_crs, name, usage)
    # carry the inference warning onto the record
    for w in warnings:
        if w not in rec.warnings:
            rec.warnings.append(w)
    return rec
