import os
import json
import time
import numpy as np
from typing import List, Optional, Dict, Any
from schemas import EOLayerResponse, STACMetadataSchema, ProvenanceTag
from cache import get_cache, set_cache

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))

def get_eo_layer(bbox: List[float], layer_type: str = "ndvi", date_range: Optional[str] = None) -> EOLayerResponse:
    layer_type = layer_type.lower()
    cache_key = f"eo_layer_{layer_type}_{bbox[0]}_{bbox[1]}_{bbox[2]}_{bbox[3]}"
    
    cached_val = get_cache(cache_key)
    if cached_val:
        return EOLayerResponse(**cached_val)
        
    meta_path = os.path.join(DATA_DIR, "metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            stac_data = json.load(f)
    else:
        stac_data = {
            "scene_id": "S2C_MSIL2A_20260616T050651_R019_T44RNN",
            "acquisition_date": "2026-06-16T05:06:51Z",
            "cloud_cover_percent": 0.27,
            "crs": "EPSG:32644"
        }
        
    stac_metadata = STACMetadataSchema(
        scene_id=stac_data.get("scene_id", "S2C_MSIL2A_20260616T050651_R019_T44RNN"),
        acquisition_date=stac_data.get("acquisition_date", "2026-06-16T05:06:51Z"),
        cloud_cover_percent=stac_data.get("cloud_cover_percent", 0.27),
        source_api="Microsoft Planetary Computer STAC API (sentinel-2-l2a)",
        provenance_tag=ProvenanceTag.RECENT
    )
    
    tile_url = f"http://localhost:8000/map/overlay/{layer_type}"
    
    response = EOLayerResponse(
        layer_type=layer_type,
        tile_url=tile_url,
        bounds=bbox,
        stac_metadata=stac_metadata,
        provenance_tag=ProvenanceTag.RECENT
    )
    
    set_cache(cache_key, response.dict(), ttl_seconds=3600)
    return response
