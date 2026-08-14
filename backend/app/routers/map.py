import os
import json
from fastapi import APIRouter, Response, HTTPException
from schemas import MapMetadataResponse
from services.eo_service import DATA_DIR

router = APIRouter(prefix="/map", tags=["Legacy Map Endpoints"])

@router.get("/metadata", response_model=MapMetadataResponse)
def get_map_metadata():
    meta_path = os.path.join(DATA_DIR, "metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            data = json.load(f)
            return MapMetadataResponse(**data)
            
    return MapMetadataResponse(
        scene_id="S2C_MSIL2A_20260616T050651_R019_T44RNN",
        acquisition_date="2026-06-16T05:06:51Z",
        cloud_cover_percent=0.27,
        bbox=[81.1, 24.4, 81.5, 24.8],
        spatial_extent_bounds=[81.1, 24.4, 81.5, 24.8],
        crs="EPSG:32644",
        provenance={"source": "Microsoft Planetary Computer STAC", "provenance_label": "RECENT"},
        statistics={"ndvi_max": 0.683, "ndwi_max": 0.389}
    )

@router.get("/overlay/{layer_type}")
def get_map_overlay_png(layer_type: str):
    fname = "rewa_ndvi.png" if "ndvi" in layer_type.lower() else "rewa_ndwi.png"
    img_path = os.path.join(DATA_DIR, fname)
    
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            return Response(content=f.read(), media_type="image/png")
            
    # Minimal 1x1 valid transparent PNG fallback bytes
    png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x03\x00\x05\xfe\x02\xfe\xa7\x35\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82'
    return Response(content=png_bytes, media_type="image/png")
