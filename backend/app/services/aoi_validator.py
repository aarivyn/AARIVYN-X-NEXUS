import math
from typing import List, Dict, Any
from fastapi import HTTPException
from config import settings

def validate_aoi_bounds(bbox: List[float]) -> Dict[str, Any]:
    """
    Validates bounding box coordinates and calculates geographic extent & estimated raster pixels.
    Rejects requests exceeding configured resource limits with HTTP 400 Bad Request.
    """
    if len(bbox) != 4:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "AOI_LIMIT_EXCEEDED",
                "message": "Invalid bounding box format. Must specify 4 numbers: [min_lon, min_lat, max_lon, max_lat].",
                "provided_bbox": bbox
            }
        )
    
    min_lon, min_lat, max_lon, max_lat = bbox
    
    if min_lon >= max_lon or min_lat >= max_lat:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "AOI_LIMIT_EXCEEDED",
                "message": "Invalid bounding box orientation. min_lon/min_lat must be less than max_lon/max_lat.",
                "provided_bbox": bbox
            }
        )

    # Approximate width and height in km (at equator: 1 deg ~ 111 km)
    lat_mid = math.radians((min_lat + max_lat) / 2.0)
    width_km = abs(max_lon - min_lon) * 111.0 * math.cos(lat_mid)
    height_km = abs(max_lat - min_lat) * 111.0
    area_km2 = width_km * height_km

    # Estimate 10m Sentinel-2 pixel count (10m pixel = 100 sq.m = 1e-4 sq.km)
    pixel_estimate = int(area_km2 / 1e-4)

    # Check against configured limits
    if width_km > settings.NEXUS_MAX_AOI_WIDTH_KM:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "AOI_LIMIT_EXCEEDED",
                "message": f"Requested AOI width ({width_km:.1f} km) exceeds maximum limit ({settings.NEXUS_MAX_AOI_WIDTH_KM} km).",
                "limits": {
                    "max_width_km": settings.NEXUS_MAX_AOI_WIDTH_KM,
                    "requested_width_km": round(width_km, 1)
                }
            }
        )

    if height_km > settings.NEXUS_MAX_AOI_HEIGHT_KM:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "AOI_LIMIT_EXCEEDED",
                "message": f"Requested AOI height ({height_km:.1f} km) exceeds maximum limit ({settings.NEXUS_MAX_AOI_HEIGHT_KM} km).",
                "limits": {
                    "max_height_km": settings.NEXUS_MAX_AOI_HEIGHT_KM,
                    "requested_height_km": round(height_km, 1)
                }
            }
        )

    if area_km2 > settings.NEXUS_MAX_AOI_AREA_KM2:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "AOI_LIMIT_EXCEEDED",
                "message": f"Requested AOI area ({area_km2:.1f} sq.km) exceeds maximum limit ({settings.NEXUS_MAX_AOI_AREA_KM2} sq.km).",
                "limits": {
                    "max_area_km2": settings.NEXUS_MAX_AOI_AREA_KM2,
                    "requested_area_km2": round(area_km2, 1)
                }
            }
        )

    if pixel_estimate > settings.NEXUS_MAX_RASTER_PIXELS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "AOI_LIMIT_EXCEEDED",
                "message": f"Estimated raster pixel allocation ({pixel_estimate:,}) exceeds maximum limit ({settings.NEXUS_MAX_RASTER_PIXELS:,} pixels).",
                "limits": {
                    "max_raster_pixels": settings.NEXUS_MAX_RASTER_PIXELS,
                    "requested_raster_pixels": pixel_estimate
                }
            }
        )

    return {
        "width_km": round(width_km, 2),
        "height_km": round(height_km, 2),
        "area_km2": round(area_km2, 2),
        "pixel_estimate": pixel_estimate
    }
