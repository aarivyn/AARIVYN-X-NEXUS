from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from schemas import EOLayerResponse
from services.eo_service import get_eo_layer
from services.aoi_validator import validate_aoi_bounds

router = APIRouter(prefix="/eo", tags=["Module 2: Earth Observation Ingestion"])

@router.get("/layers", response_model=EOLayerResponse)
def get_eo_layers(
    layer_type: str = Query("ndvi", description="ndvi | ndwi | groundwater"),
    min_lon: float = Query(81.1),
    min_lat: float = Query(24.4),
    max_lon: float = Query(81.5),
    max_lat: float = Query(24.8)
):
    bbox = [min_lon, min_lat, max_lon, max_lat]
    
    # Priority 3: AOI Bounds & Resource Protection Validation
    validate_aoi_bounds(bbox)
    
    if layer_type.lower() not in ["ndvi", "ndwi", "groundwater"]:
        raise HTTPException(status_code=400, detail="Unsupported layer type. Choose ndvi, ndwi, or groundwater.")
        
    return get_eo_layer(bbox=bbox, layer_type=layer_type)
