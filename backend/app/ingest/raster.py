"""Raster & imagery converters -> common representation.

Rasters keep their native pixel grid (no warping in this build) but are stored
as normalized GeoTIFF when they arrive as ASCII grid, and every record carries
native bounds + CRS + a WGS84 bbox. Plain photos are geotagged via EXIF GPS
when present.
"""
from __future__ import annotations

import json
import sqlite3
import shutil
from pathlib import Path
from typing import Optional

import numpy as np

from .. import config
from . import crs
from .geoutil import bbox_of_geojson, feature_collection, make_feature

try:
    import tifffile
    _HAS_TIFFFILE = True
except ImportError:  # pragma: no cover
    tifffile = None  # type: ignore
    _HAS_TIFFFILE = False

try:
    from PIL import Image, ExifTags
    _HAS_PIL = True
except ImportError:  # pragma: no cover
    Image = None  # type: ignore
    ExifTags = None  # type: ignore
    _HAS_PIL = False


# --------------------------------------------------------------------------
# GeoTIFF / TIFF
# --------------------------------------------------------------------------

def _geotiff_crs(tags: dict) -> Optional[str]:
    """Extract EPSG code from the GeoKeyDirectory tag (34735)."""
    gkd = tags.get(34735)
    if gkd is None:
        return None
    try:
        if isinstance(gkd, bytes):
            gkd = np.frombuffer(gkd, dtype="<H").tolist()
        gkd = list(gkd)
        if len(gkd) < 4:
            return None
        n_keys = gkd[3]
        for i in range(n_keys):
            off = 4 + i * 4
            if off + 3 >= len(gkd):
                break
            key_id, _, _, value = gkd[off:off + 4]
            if key_id == 3072 and value != 0:      # ProjectedCSTypeGeoKey
                return f"EPSG:{value}"
            if key_id == 2048 and value != 0:      # GeographicTypeGeoKey
                return f"EPSG:{value}"
    except Exception:
        return None
    return None


def _native_bounds(tags: dict, shape) -> Optional[list[float]]:
    scale = tags.get(33550)   # ModelPixelScale
    tie = tags.get(33922)     # ModelTiepoint
    if scale is None or tie is None:
        return None
    try:
        sx, sy = float(scale[0]), float(scale[1])
        i, j = float(tie[0]), float(tie[1])
        ox, oy = float(tie[3]), float(tie[4])
        rows, cols = shape[0], shape[1]
        x0 = ox - i * sx
        y_top = oy + j * sy
        return [x0, y_top - rows * sy, x0 + cols * sx, y_top]
    except Exception:
        return None


def from_geotiff(path: Path, src_crs: Optional[str], warnings: list[str]) -> dict:
    if not _HAS_TIFFFILE:
        raise ValueError("tifffile not installed; cannot read GeoTIFF")
    with tifffile.TiffFile(path) as tif:
        page = tif.pages[0]
        shape = page.shape
        dtype = page.dtype.name if page.dtype else None
        bits = page.bitspersample
        comp = page.compression.name if page.compression else None
        photometric = page.photometric.name if page.photometric else None
        tags = {t.code: t.value for t in page.tags.values()}
        crs_code = _geotiff_crs(tags)
        bounds = _native_bounds(tags, shape)
        n_bands = max(1, len(page.axes) - 2) if page.axes else 1

        stats = None
        if np.prod(shape) * np.dtype(dtype).itemsize <= config.MAX_RASTER_STATS_BYTES and shape:
            arr = page.asarray()
            if arr.ndim == 3:
                arr = arr[0]  # stats on first band
            finite = arr[np.isfinite(arr)]
            if finite.size:
                stats = {
                    "min": float(np.nanmin(finite)),
                    "max": float(np.nanmax(finite)),
                    "mean": float(np.nanmean(finite)),
                    "std": float(np.nanstd(finite)),
                }

    source_crs = src_crs or crs_code
    if source_crs:
        warnings.append(f"raster CRS: {source_crs}")
    else:
        warnings.append("no CRS found in GeoTIFF tags; bounds reported in raw pixel/model units")

    bbox_wgs84 = None
    if bounds and source_crs:
        bbox_wgs84 = crs.transform_bbox(bounds, source_crs)

    # normalize storage: keep a stable copy in the converted area
    dest = config.CONVERTED_DIR / f"raster_{path.stem}.tif"
    if not dest.exists():
        shutil.copy2(path, dest)

    data = {
        "format": "geotiff",
        "width": shape[1] if len(shape) >= 2 else None,
        "height": shape[0] if shape else None,
        "bands": n_bands,
        "dtype": dtype,
        "bits_per_sample": bits,
        "compression": comp,
        "photometric": photometric,
        "crs": source_crs,
        "bounds_native": bounds,
        "bounds_wgs84": bbox_wgs84,
        "stats": stats,
        "stored_file": str(dest),
    }
    return {"data": data, "bbox": bbox_wgs84, "source_crs": source_crs,
            "warnings": warnings, "confidence": "high" if source_crs else "medium"}


# --------------------------------------------------------------------------
# ESRI ASCII grid (.asc) -> normalized GeoTIFF
# --------------------------------------------------------------------------

def from_ascii_grid(path: Path, src_crs: Optional[str], warnings: list[str]) -> dict:
    if not _HAS_TIFFFILE:
        raise ValueError("tifffile not installed; cannot convert ASCII grid")
    header = {}
    with path.open() as fh:
        for _ in range(6):
            line = fh.readline()
            parts = line.split()
            if len(parts) == 2:
                header[parts[0].lower()] = parts[1]
    try:
        ncols = int(header["ncols"])
        nrows = int(header["nrows"])
        cellsize = float(header["cellsize"])
        nodata = float(header.get("nodata_value", "-9999"))
    except (KeyError, ValueError) as e:
        raise ValueError(f"invalid ESRI ASCII grid header: {e}") from e

    arr = np.loadtxt(path, skiprows=6, dtype=np.float32)
    if arr.shape != (nrows, ncols):
        warnings.append(f"grid shape {arr.shape} != header ({nrows},{ncols}); using array shape")

    # Determine extent (corner- or center-based origin)
    if "xllcorner" in header:
        x0 = float(header["xllcorner"])
        y0 = float(header["yllcorner"])
        top = y0 + nrows * cellsize
    elif "xllcenter" in header:
        x0 = float(header["xllcenter"]) - cellsize / 2
        y0 = float(header["yllcenter"]) - cellsize / 2
        top = y0 + nrows * cellsize
    else:
        x0, top = 0.0, float(nrows) * cellsize
        warnings.append("no corner/center origin in header; assumed (0,0)")

    bounds_native = [x0, top - nrows * cellsize, x0 + ncols * cellsize, top]

    # write normalized GeoTIFF with georeferencing tags
    dest = config.CONVERTED_DIR / f"raster_{path.stem}.tif"
    extratags = [
        (33550, "d", 3, (cellsize, cellsize, 0.0)),          # ModelPixelScale
        (33922, "d", 6, (0.0, 0.0, 0.0, x0, top, 0.0)),      # ModelTiepoint
    ]
    tifffile.imwrite(dest, arr, extratags=extratags, metadata=None)

    source_crs = src_crs
    if not source_crs:
        warnings.append("ASCII grid carries no CRS; assumed EPSG:4326 (verify!)")
        source_crs = "EPSG:4326"

    bbox_wgs84 = crs.transform_bbox(bounds_native, source_crs)
    finite = arr[np.isfinite(arr) & (arr != nodata)]
    stats = None
    if finite.size:
        stats = {"min": float(finite.min()), "max": float(finite.max()),
                 "mean": float(finite.mean()), "std": float(finite.std())}

    data = {
        "format": "geotiff",
        "width": ncols, "height": nrows, "bands": 1,
        "dtype": "float32", "nodata": nodata,
        "crs": source_crs,
        "bounds_native": bounds_native,
        "bounds_wgs84": bbox_wgs84,
        "stats": stats,
        "stored_file": str(dest),
        "source_format": "esri_ascii_grid",
    }
    return {"data": data, "bbox": bbox_wgs84, "source_crs": source_crs,
            "warnings": warnings, "confidence": "medium"}


# --------------------------------------------------------------------------
# Plain imagery (JPEG/PNG/JP2) with EXIF GPS geotagging
# --------------------------------------------------------------------------

def _dms_to_decimal(dms, ref: str) -> Optional[float]:
    if not dms or len(dms) != 3:
        return None

    def to_float(v) -> Optional[float]:
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, tuple) and len(v) == 2:  # rational (num, den)
            try:
                return float(v[0]) / float(v[1]) if float(v[1]) else None
            except (ValueError, ZeroDivisionError):
                return None
        try:
            return float(v)  # Fraction / str
        except (ValueError, TypeError):
            return None

    try:
        deg, minutes, secs = to_float(dms[0]), to_float(dms[1]), to_float(dms[2])
        if None in (deg, minutes, secs):
            return None
        val = deg + minutes / 60.0 + secs / 3600.0
        if ref in ("S", "W"):
            val = -val
        return val
    except Exception:
        return None


def from_image(path: Path, src_crs: Optional[str], warnings: list[str]) -> dict:
    if not _HAS_PIL:
        raise ValueError("Pillow not installed; cannot inspect image")
    with Image.open(path) as im:
        fmt = im.format
        width, height = im.size
        mode = im.mode
        dpi = None
        try:
            dpi_info = im.info.get("dpi")
            if dpi_info:
                dpi = float(dpi_info[0])
        except Exception:
            pass
        exif = im.getexif()
        gps_ifd = exif.get_ifd(0x8825) if hasattr(exif, "get_ifd") else {}

    geojson = None
    bbox = None
    if gps_ifd:
        lat = _dms_to_decimal(gps_ifd.get(2), gps_ifd.get(1, "N"))
        lon = _dms_to_decimal(gps_ifd.get(4), gps_ifd.get(3, "E"))
        if lat is not None and lon is not None:
            fc = feature_collection([make_feature(
                {"type": "Point", "coordinates": [lon, lat]},
                {"image": path.name, "source": "exif_gps"})])
            geojson = fc
            bbox = bbox_of_geojson(fc)
            warnings.append(f"geotagged from EXIF GPS: ({lat:.6f}, {lon:.6f})")
    else:
        warnings.append("no EXIF GPS; image stored as non-georeferenced raster")

    dest = config.CONVERTED_DIR / f"image_{path.stem}{path.suffix.lower()}"
    if not dest.exists():
        shutil.copy2(path, dest)

    data = {
        "format": fmt or path.suffix.lower().lstrip("."),
        "width": width, "height": height, "mode": mode,
        "dpi": dpi,
        "crs": "EPSG:4326" if geojson else None,
        "geotagged": geojson is not None,
        "stored_file": str(dest),
    }
    if geojson:
        data["geojson"] = geojson
        data["feature_count"] = 1
        data["geometry_types"] = ["Point"]
    return {"data": data, "bbox": bbox, "source_crs": src_crs,
            "warnings": warnings, "confidence": "high" if geojson else "low",
            "feature_count": 1 if geojson else None,
            "geometry_types": ["Point"] if geojson else []}


# --------------------------------------------------------------------------
# MBTiles (SQLite tile container)
# --------------------------------------------------------------------------

def from_mbtiles(path: Path, src_crs: Optional[str], warnings: list[str]) -> dict:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        meta = {}
        try:
            for row in conn.execute("SELECT name, value FROM metadata"):
                meta[row["name"]] = row["value"]
        except sqlite3.Error:
            warnings.append("no metadata table; MBTiles may be malformed")
        tile_count = 0
        try:
            tile_count = conn.execute("SELECT COUNT(*) FROM tiles").fetchone()[0]
        except sqlite3.Error:
            pass
        zoom_levels = []
        try:
            zoom_levels = [r[0] for r in conn.execute("SELECT DISTINCT zoom_level FROM tiles ORDER BY zoom_level")]
        except sqlite3.Error:
            pass
    finally:
        conn.close()

    bounds = None
    bbox_wgs84 = None
    if meta.get("bounds"):
        try:
            parts = [float(x) for x in str(meta["bounds"]).split(",")]
            if len(parts) == 4:
                bounds = parts
                bbox_wgs84 = parts  # MBTiles bounds are WGS84
        except ValueError:
            pass

    dest = config.CONVERTED_DIR / f"tiles_{path.stem}.mbtiles"
    if not dest.exists():
        shutil.copy2(path, dest)

    source_crs = src_crs or "EPSG:3857"  # MBTiles is web-mercator by spec
    data = {
        "format": "mbtiles",
        "name": meta.get("name"),
        "tile_format": meta.get("format"),
        "tile_count": tile_count,
        "zoom_levels": zoom_levels,
        "minzoom": meta.get("minzoom"),
        "maxzoom": meta.get("maxzoom"),
        "crs": source_crs,
        "bounds": bounds,
        "bounds_wgs84": bbox_wgs84,
        "stored_file": str(dest),
    }
    return {"data": data, "bbox": bbox_wgs84, "source_crs": source_crs,
            "warnings": warnings, "confidence": "high"}
