"""LiDAR point cloud converter (LAS/LAZ).

Produces header stats (point count, bounds, CRS when declared) plus a small
random GeoJSON point preview for downstream use; the original file is kept for
full-resolution processing. Degrades to a stored-raw record when laspy is
unavailable.
"""
from __future__ import annotations

import random
import shutil
from pathlib import Path
from typing import Optional

from .. import config
from . import crs
from .geoutil import feature_collection, make_feature

try:
    import laspy
    _HAS_LASPY = True
except ImportError:  # pragma: no cover
    laspy = None  # type: ignore
    _HAS_LASPY = False


def from_pointcloud(path: Path, src_crs: Optional[str], warnings: list[str]) -> dict:
    if not _HAS_LASPY:
        warnings.append("laspy not installed; stored raw without conversion")
        data = {"format": path.suffix.lower().lstrip("."), "point_count": None,
                "stored_file": str(path), "converted": False}
        return {"data": data, "source_crs": src_crs, "warnings": warnings,
                "confidence": "low"}

    try:
        las = laspy.read(str(path))
        header = las.header
        point_count = header.point_count
        bounds = None
        if point_count:
            x = las.x
            y = las.y
            bounds = [float(x.min()), float(y.min()), float(x.max()), float(y.max())]

        # CRS: from laspy VLR (WKT or GeoTIFF keys) when present
        declared = None
        try:
            if las.vlrs:
                for vlr in las.vlrs:
                    if vlr.user_id == "LASF_Projection":
                        declared = str(vlr.parsed_body)[:200]
        except Exception:
            declared = None
        source_crs = src_crs or declared
        if source_crs and source_crs.startswith("EPSG"):
            warnings.append(f"point cloud CRS: {source_crs}")
        elif source_crs and not src_crs:
            warnings.append(f"point cloud CRS metadata (unparsed): {source_crs[:80]}")

        # random preview subset
        preview: list[dict] = []
        n_preview = min(point_count, config.POINTCLOUD_PREVIEW_POINTS)
        if point_count > 0:
            idx = random.sample(range(point_count), n_preview)
            for i in idx:
                preview.append(make_feature(
                    {"type": "Point", "coordinates": [float(x[i]), float(y[i])]},
                    {"z": float(las.z[i]), "intensity": int(las.intensity[i]) if hasattr(las, "intensity") else None}))

        bbox_wgs84 = None
        if bounds and source_crs and source_crs.startswith("EPSG"):
            bbox_wgs84 = crs.transform_bbox(bounds, source_crs)
        elif bounds:
            bbox_wgs84 = bounds  # unknown CRS: report raw

        dest = config.CONVERTED_DIR / f"points_{path.stem}{path.suffix.lower()}"
        if not dest.exists():
            shutil.copy2(path, dest)

        data = {
            "format": path.suffix.lower().lstrip("."),
            "point_count": point_count,
            "bounds": bounds,
            "bounds_wgs84": bbox_wgs84,
            "crs": source_crs,
            "preview_feature_count": len(preview),
            "preview": feature_collection(preview),
            "stored_file": str(dest),
        }
        return {"data": data, "bbox": bbox_wgs84, "source_crs": source_crs,
                "warnings": warnings, "confidence": "high",
                "feature_count": point_count, "geometry_types": ["Point"]}
    except Exception as e:
        warnings.append(f"point cloud parse failed ({e}); stored raw")
        data = {"format": path.suffix.lower().lstrip("."), "point_count": None,
                "stored_file": str(path), "converted": False}
        return {"data": data, "source_crs": src_crs, "warnings": warnings,
                "confidence": "low"}
