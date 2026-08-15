# NEXUS — Decision Intelligence Platform for Rural Development Planning

> A Smart optimization intelligence engine for water shortage and rural infrastructure planning, combining satellite/geospatial data, research evidence, and multi-objective optimization to help government officials, NGOs, and CSR teams design and compare intervention plans under real-world constraints.

## Team

**Team Name : ** AARIVYN
**Team Lead : ** Sumit Pandey
**Members:**

Alhamda Iqbal Sadiq

Kanika Kaushal

Koshin H Hegde

**Institute : IIT Madras** 

## Problem

Government officials in rural India often have on-ground knowledge of water-shortage-affected areas — population, urgency, and available resources 
but lack a way to combine this with satellite imagery, GIS data, and research evidence to plan interventions. 
Existing platforms like ISRO Bhuvan provide raw geospatial data and visualization, but decision-makers still have to manually connect data sources, check feasibility, 
and compare intervention options under a fixed budget — a slow, effort-heavy process.

## Solution

NEXUS takes in a problem statement, affected region, target population, budget, timeline, and constraints, and:

1. **Analyzes ground conditions** using satellite imagery and environmental data (rainfall, water bodies, soil, terrain, land use, roads, population).
2. **Surfaces evidence** via a Research & Evidence layer — relevant papers, government reports, schemes, and past projects.
3. **Identifies feasible interventions** (rainwater harvesting, watershed restoration, groundwater recharge, wastewater treatment, etc.) filtered by location, budget, resources, and timeline.
4. **Optimizes trade-offs** using **NSGA-II** (multi-objective genetic algorithm) across cost, impact, risk, time, coverage, and equity to generate multiple Pareto-optimal plans instead of a single recommendation.
5. **Supports human decision-making** by letting officials compare trade-offs, review evidence, and select a final plan — with monitoring support post-implementation for re-evaluation.

### Core Flow

Input → Analyze → Identify Gap → Find & Optimize Solutions → Compare → Human Decision


## Key Features

- **Multi-format geospatial ingestion** — supports vector (GeoJSON, Shapefile, KML/KMZ, DXF), raster (GeoTIFF, JPG, PNG, JP2, MBTiles), point cloud (LAS/LAZ), tabular (CSV, XLSX), and document (PDF, DOCX, JSON, XML) inputs, auto-detected and tagged by use case (road/rail networks, utilities, terrain, soil, groundwater, population, budget, permits, etc.)
- **NSGA-II based optimization engine** for Pareto-optimal, multi-objective intervention planning
- **Structured intake pipeline**: Extract → Detect Irregularities → Define Desired State → Generate & Optimize Plans → Compare & Decide
- **Interactive map workspace** with location registry, area intelligence, and multi-role views (Community, NGO, CSR, Research modes)
- **Visual outputs**: Pareto charts, plan radar comparisons, trajectory/impact charts, and exportable PDF reports with budget breakdowns and contradiction detection

## Tech Stack

**Backend**
- FastAPI, Uvicorn, Pydantic, SQLAlchemy, PostgreSQL (psycopg2), Redis
- pymoo (NSGA-II optimization), NumPy, Shapely
- pystac-client + planetary-computer (satellite/EO data)
- Geospatial ingest: pyshp, pyproj, ezdxf, laspy/lazrs, tifffile, openpyxl, pypdf

**Frontend**
- Next.js 14, React 18, TypeScript
- MapLibre GL (interactive maps), Recharts (data viz), Zustand (state), Tailwind CSS, Framer Motion

## Repository Structure

├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI entry point
│   │   ├── models.py, schemas.py, optimizer.py
│   │   ├── database.py, config.py, cache.py
│   │   ├── mapdata/           # Geospatial data ingestion & map API (vector, raster, tabular, point cloud, docs)
│   │   ├── services/          # Business logic (EO/satellite, optimization, water, feasibility, auth, graph)
│   │   ├── routers/           # API route definitions (nexus, optimize, monitoring, feasibility, etc.)
│   │   └── data/               # Local storage (uploads, converted files, locations, social groups)
│   ├── tests/                 # Test suite
│   ├── API.md
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── app/                # Next.js pages & role-based routes (CSR, NGO, Research, Community)
    │   ├── components/
    │   │   ├── shell/           # App shell (TopBar, PipelineRail, Workspace)
    │   │   ├── map/             # Interactive map components
    │   │   ├── charts/          # Pareto, Radar, Trajectory charts
    │   │   ├── network/         # Role-based mode views
    │   │   ├── stages/          # Pipeline stages (Intake → Detect → Gap → Optimize → Decide → Monitor)
    │   │   └── ui/              # Shared UI primitives
    │   └── lib/                 # State management & API clients
    ├── package.json
    └── next.config.mjs          # Problem statement, input schema & system design document


## Data Inputs Supported

| Category                      |                               Examples                      |                   Formats                     |
|-------------------------------|-------------------------------------------------------------|-----------------------------------------------|
| Base maps / cartographic      | Topographic maps, road/rail networks, admin boundaries, DEM | Shapefile, GeoJSON, KML/KMZ, GeoTIFF, LAS/LAZ |
| Existing infrastructure       | Water/sewer, gas, electrical, telecom as-builts             | Shapefile, GeoJSON, DXF/DWG, scanned PDF      |
| Imagery                       | Aerial/drone, satellite, ground-level site photos           | JPEG, PNG, TIFF, GeoTIFF, JP2                 |
| Geological / environmental    | Soil, geotechnical reports, groundwater, protected zones    | Shapefile, GeoJSON, CSV, PDF                  |
| Water demand / supply         | Population, water source specs, demand projections          | CSV, XLSX, PDF                                |
| Field observations            | Field notes, survey forms, GPS waypoints                    | JPEG/PNG/PDF, CSV, GPX, KML                   |

## Pipeline Stages

1. **Structure Inputs** — extract region, problem, population, budget, timeline, constraints; fetch satellite + environmental data; flag missing/contradictory info
2. **Analyze Region** — identify problems and severity from ground-condition data
3. **Define Desired State** — determine ideal target condition and the current-vs-desired gap
4. **Generate & Optimize Solutions** — retrieve and filter candidate interventions; run NSGA-II to produce feasible action plans
5. **Compare & Decide** — compare plans on cost, impact, risk, time, and coverage; user selects final plan and generates an implementation report

## Business Model

NEXUS is designed as a **B2G/B2B decision-intelligence platform** for government departments, CSR teams, and NGOs managing development budgets, with potential revenue streams including institutional SaaS licensing, project-based optimization, and recurring satellite-based monitoring. The platform architecture is designed to scale beyond water management into agriculture, climate, energy, disaster resilience, and urban development.
