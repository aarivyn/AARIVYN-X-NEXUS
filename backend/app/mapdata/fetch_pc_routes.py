"""Planetary Computer data-fetch API route.

Takes a set of stored location ids (see the locations API) plus a date
window and pulls signed STAC items from the Planetary Computer for every
relevant layer (imagery, terrain, land use, surface water, rainfall) that
intersects each location's AOI polygon.

Endpoint summary
----------------
POST /api/v1/fetch-pc   →  fetch PC data (all layers) for the requested locations
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .fetch_pc_schemas import FetchPCRequest, FetchPCResponse, LocationResult

# Reuse the locations store's load helpers so this endpoint reads from the
# *saved* locations (the caller only supplies ids, never location data again).
from .location_routes import _load_one as _load_location

# Import the Planetary Computer layer set so layers are handled internally
# (the caller never has to know or specify which layers exist).
try:
    from .fetch_pc import fetch_all_layers  # type: ignore
except ImportError:  # pragma: no cover - pystac-client/planetary-computer not installed
    fetch_all_layers = None


router = APIRouter(prefix="/api/v1/fetch-pc", tags=["fetch-pc"])


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────


@router.post("", response_model=FetchPCResponse)
def fetch_pc_data(body: FetchPCRequest) -> FetchPCResponse:
    """Fetch Planetary Computer data for one or more stored locations.

    The caller supplies only stored location ids (from the locations API)
    plus a date window. The location's already-saved state/district/city
    names are loaded from the locations store and resolved to a GeoJSON AOI
    polygon internally (via Nominatim) before querying the STAC API.
    """
    if fetch_all_layers is None:
        raise HTTPException(
            503,
            "Planetary Computer stack is not installed "
            "(pip install pystac-client planetary-computer shapely)",
        )

    # Validate location ids up front for a clear error response.
    locations = []
    for loc_id in body.location_ids:
        rec = _load_location(loc_id)
        if rec is None:
            raise HTTPException(404, f"no location record {loc_id}")
        locations.append((loc_id, rec))

    results: list[LocationResult] = []
    for loc_id, rec in locations:
        district = rec.district
        city = rec.city
        state = rec.state

        if not district:
            results.append(
                LocationResult(
                    location_id=loc_id,
                    name=rec.name,
                    state=state or "",
                    district="",
                    city=city,
                    layers={"error": "location has no district name", "collection_id": None},
                )
            )
            continue

        layers = fetch_all_layers(city, district, body.start_date, body.end_date, state=state)

        results.append(
            LocationResult(
                location_id=loc_id,
                name=rec.name,
                state=state or "",
                district=district,
                city=city,
                layers=layers,
            )
        )

    return FetchPCResponse(locations=results)
