"""Map/site-data ingest module (formerly the standalone nexus-main service).

Exposes ALL_ROUTERS -- every APIRouter this module contributes to the master
NEXUS app: file ingest (/api/v1/maps), budget, locations, social groups,
timeline.
"""
from __future__ import annotations

from .maps_routes import router as maps_router
from .budget_routes import router as budget_router
from .location_routes import router as location_router
from .social_routes import router as social_router
from .timeline_routes import router as timeline_router
from .fetch_pc_routes import router as fetch_pc_router

ALL_ROUTERS = [
    maps_router,
    budget_router,
    location_router,
    social_router,
    timeline_router,
    fetch_pc_router,
]
