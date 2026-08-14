import os
import sys

# Ensure backend/app directory is in sys.path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from config import settings

# Import all core & master router modules
from routers import (
    auth, workspace, eo, context, graph,
    feasibility, optimize, provenance, water_intelligence,
    portfolio, interventions, map, monitoring, nexus
)

# Map/site-data ingest module (merged in from the nexus-main ingest service):
# file ingest (/api/v1/maps), budget, locations, social groups, timeline.
import mapdata

# Initialize database tables
try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

app = FastAPI(
    title="NEXUS — Community Development Intelligence API",
    description="Production-ready geospatial decision-intelligence platform observing Earth data, detecting water development problems, filtering intervention feasibility, and running NSGA-II multi-objective optimization.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Priority 5: Configurable CORS Hardening
cors_origins = settings.CORS_ALLOWED_ORIGINS
allow_all_origins = "*" in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if not allow_all_origins else ["*"],
    allow_credentials=not allow_all_origins, # Do not allow credentials if wildcard origin is specified
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handler for Graceful Failure Handling & Useful Error Messages
@app.exception_handler(ValueError)
def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Bad Request Input Validation Failure",
            "message": str(exc),
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "NEXUS API encountered an unexpected issue. Input and processing parameters have been logged.",
            "detail": str(exc),
            "path": request.url.path
        }
    )

# Health & Telemetry
app.include_router(monitoring.router)

# Master Orchestration Pipeline
app.include_router(nexus.router)
app.include_router(nexus.router, prefix="/api/v1")

# Core V1 & Module Routers
app.include_router(auth.router)
app.include_router(workspace.router)
app.include_router(eo.router)
app.include_router(water_intelligence.router)
app.include_router(water_intelligence.router, prefix="/api/v1")
app.include_router(context.router)
app.include_router(graph.router)
app.include_router(feasibility.router)
app.include_router(optimize.router)
app.include_router(optimize.router, prefix="/api/v1")
app.include_router(provenance.router)
app.include_router(portfolio.router)
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(interventions.router)
app.include_router(map.router)

# Map/site-data ingest module
for r in mapdata.ALL_ROUTERS:
    app.include_router(r)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "NEXUS Community Development Intelligence Backend",
        "version": "2.0.0",
        "documentation": "/docs",
        "master_pipeline_endpoint": "/api/v1/nexus/analyze"
    }
