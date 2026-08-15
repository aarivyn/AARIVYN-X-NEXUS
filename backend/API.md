# NEXUS — Community Development Intelligence API

**Version:** `2.0.0`
**Base URL:** `http://localhost:8000` (development)
**Interactive docs:** `/docs` (Swagger UI) · `/redoc` (ReDoc) · `/openapi.json`

NEXUS is a geospatial decision-intelligence platform for community development
planning. It ingests Earth-observation data, detects water-development problems,
filters intervention feasibility, and runs NSGA-II multi-objective portfolio
optimization, returning explainable, audit-ready results.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Global Conventions](#global-conventions)
4. [Monitoring & Telemetry](#monitoring--telemetry)
5. [Module 1 — Auth & Onboarding](#module-1--auth--onboarding)
6. [Module 2 — Earth Observation](#module-2--earth-observation-ingestion)
7. [Module 3 — Water Intelligence & Context](#module-3--water-intelligence-engine)
8. [Module 4 — Intervention Knowledge Graph](#module-4--intervention-knowledge-graph)
9. [Module 5 — Feasibility Filter](#module-5--feasibility-filter-engine)
10. [Module 6 — NSGA-II Optimizer](#module-6--nsga-ii-multi-objective-optimizer)
11. [Module 7 — Portfolios, Implementation Plan & Provenance](#module-7--portfolios--implementation-plan--provenance)
12. [Master Orchestration Pipeline](#master-orchestration-pipeline)
13. [Map Data Ingest](#map-data-ingest-api)
14. [Budget, Locations, Social Groups & Timeline](#budget-locations-social-groups--timeline)
15. [Legacy Endpoints](#legacy-endpoints)
16. [Error Handling](#error-handling)
17. [Testing](#testing)

---

## Quick Start

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the server (falls back to SQLite + in-memory cache when
# Postgres/Redis are unavailable — no external services required for dev).
uvicorn app.main:app --reload --port 8000
```

Verify with:

```bash
curl http://localhost:8000/health
```

---

## Architecture Overview

The platform is organized as a pipeline of "modules", each exposing a
dedicated FastAPI `APIRouter`:

| Module | Router prefix | Purpose |
|--------|---------------|---------|
| Monitoring | `/health`, `/ready`, `/api/v1/system/status` | Liveness, readiness, telemetry |
| 1 — Auth & Onboarding | `/auth`, `/workspace` | Persona registration + workspace context |
| 2 — Earth Observation | `/eo` | STAC/EO layer retrieval |
| 3 — Water Intelligence | `/water`, `/context` | Indicators, signals, problem detection |
| 4 — Knowledge Graph | `/graph` | Intervention graph traversal |
| 5 — Feasibility | `/feasibility` | Multi-stage constraint filtering |
| 6 — Optimizer | `/optimize` | NSGA-II portfolio optimization |
| 7 — Portfolios | `/portfolio`, `/provenance` | Plans + explainability audit |
| Master Pipeline | `/nexus` | End-to-end background orchestration |
| Map Data Ingest | `/api/v1/maps`, `/api/v1/budget`, `/api/v1/locations`, `/api/v1/social`, `/api/v1/timeline` | File ingest + site-data CRUD |

The master pipeline (`POST /api/v1/nexus/analyze`) chains **Modules 2 → 7**
end-to-end as a background job that can be polled.

**Data sources & fallbacks.** The EO layer queries the Microsoft Planetary
Computer STAC API (`sentinel-2-l2a`, `landsat-c2-l2`) with a cached-metadata
fallback and an offline `MockEOProvider` for tests. Postgres/PostGIS is used
when reachable, with a local SQLite fallback; Redis is replaced by an in-memory
cache when unavailable.

---

## Global Conventions

- **Content type:** requests and responses are `application/json` (except file
  uploads which are `multipart/form-data`, and `/map/overlay/{layer_type}` which
  returns `image/png`).
- **Bounding boxes** are always `bbox = [min_lon, min_lat, max_lon, max_lat]`
  (WGS84 / EPSG:4326).
- **Currencies** are expressed in **INR** (`budget_limit_inr`, `cost_inr`).
- **Dates/times** use ISO-8601 (e.g. `2026-06-16T05:06:51Z`).
- **IDs** are opaque strings (e.g. `INT-001`, `PORTFOLIO_1`, `job-<12-hex>`).
- Several legacy endpoints are mounted both with and without the `/api/v1`
  prefix (see the route reference below).

### AOI validation

Any endpoint that accepts a `bbox` validates it against configured resource
limits: maximum width (200 km), height (200 km), area (25,000 km²), and
estimated raster pixels (250M). Violations return `400` with a structured
`AOI_LIMIT_EXCEEDED` error.

### Ingested site-data precedence (Modules 2–7)

Data submitted through the **Map Data Ingest API** (budget, locations,
social groups, and timeline) is consumed by the decision pipeline, *not*
merely stored. When present, it overrides the equivalent request parameters
and defaults across Modules 2–7:

- **Budget** (`/api/v1/budget`) — the singleton's `target_budget` becomes the
  feasibility/optimization budget cap and `maximum_budget` the hard ceiling,
  taking precedence over `budget_limit_inr` in any request.
- **Timeline** (`/api/v1/timeline`) — `expected_duration` and `deadline`
  derive the effective `time_horizon_months` (the tighter of duration or
  deadline-to-now wins when shorter than the request/default horizon);
  `urgency` is surfaced in provenance and does not stretch the horizon.
- **Social groups** (`/api/v1/social`) — demographic profiles inform
  affected-village estimates (Module 3), intervention applicability and
  discovery context (Module 4), portfolio provenance (Module 6), and
  implementation-plan monitoring indicators (Module 7).
- **Locations** (`/api/v1/locations`) — used as a community-unit fallback for
  signal counts and surfaced in result payloads.

When no site data has been ingested, modules fall back to request-provided or
default values (non-breaking); the job result's `site_data` section reports
exactly which ingested values were applied.

---

## Monitoring & Telemetry

### `GET /health`

Liveness probe.

```json
{"status":"ok","service":"NEXUS Core Engine","uptime_seconds":123.4}
```

### `GET /ready`

Readiness probe. Reports backend store status.

```json
{"status":"ready","database":"sqlite_fallback_active",
 "redis":"in_memory_fallback","background_workers":"active_multithreaded_pool"}
```

`database` is `postgresql_postgis_connected` or `sqlite_fallback_active`;
`redis` is `connected` or `in_memory_fallback`.

### `GET /api/v1/system/status`

Detailed subsystem telemetry.

```json
{
  "status": "healthy",
  "api_status": "ONLINE (Latency <5ms)",
  "database_status": "SQLITE_FALLBACK_ACTIVE",
  "eo_provider_status": "MICROSOFT_PLANETARY_COMPUTER_STAC_LIVE",
  "intelligence_engine_status": "WATER_INTELLIGENCE_MODULE_ACTIVE",
  "optimizer_status": "PYMOO_NSGA2_SOLVER_READY",
  "background_worker_status": "ASYNC_THREAD_POOL_WORKER_ACTIVE",
  "timestamp": "2026-08-14T00:00:00Z",
  "application_version": "2.0.0"
}
```

---

## Module 1 — Auth & Onboarding

### `POST /auth/register`

Register a user. *(In-memory user store — demo implementation.)*

Request:

```json
{"email":"officer@mp.gov.in","password":"secret","name":"District Officer"}
```

Response:

```json
{"status":"registered","user_id":1,"email":"officer@mp.gov.in"}
```

Returns `400` if the email is already registered.

### `POST /auth/login`

Request:

```json
{"email":"officer@mp.gov.in","password":"secret"}
```

Response:

```json
{"status":"authenticated","access_token":"mock_bearer_token_for_officer@mp.gov.in",
 "user_id":1,"persona":"GOVERNMENT"}
```

### `GET /auth/me`

Returns the current (mock) user profile:

```json
{"id":1,"email":"officer@mp.gov.in","name":"District Officer — Rewa",
 "persona":"GOVERNMENT","organization":"Madhya Pradesh Water Resources Dept",
 "jurisdiction":"Rewa District"}
```

### `POST /auth/onboarding`

Resolves a **workspace context** for a given persona. The request's
`persona` selects which sub-payload is used:

| `persona` | Payload field | Required highlights |
|-----------|---------------|---------------------|
| `GOVERNMENT` | `government` | `organization`, `department_agency`, `admin_level`, `role` |
| `CSR_FUNDER` | `csr_funder` (or `csr`) | `organization`, `focus_areas`, `target_geography`, optional budget |
| `NGO` | `ngo` | `organization`, `operating_regions`, `focus_areas`, `implementation_capacity` |
| `STUDENT` | `student` | `name`, `institution`, `region_of_interest` |
| `RESEARCHER` | `researcher` | `name`, `institution`, `region_of_interest` |
| `COMMUNITY` | `community` | `problem_category`, optional location |

Example request:

```json
{
  "persona": "GOVERNMENT",
  "government": {
    "organization": "MPWRD",
    "department_agency": "Water Resources",
    "admin_level": "District",
    "role": "District Officer",
    "target_district": "Rewa"
  }
}
```

Response (`WorkspaceContextResponse`):

```json
{
  "user_id": 1,
  "persona": "GOVERNMENT",
  "geography_name": "Rewa District (District - District Officer)",
  "bbox": [81.1, 24.4, 81.5, 24.8],
  "center": [24.6, 81.3],
  "zoom": 10,
  "permission_scope": {"persona":"GOVERNMENT","read_map":true,"run_optimization":true,
    "view_provenance":true,"admin_level":"District","role":"District Officer"}
}
```

### `GET /workspace/current`

Returns the workspace context for a given `persona` query parameter
(default `GOVERNMENT`):

```bash
GET /workspace/current?persona=NGO
```

---

## Module 2 — Earth Observation Ingestion

### `GET /eo/layers`

Returns an EO layer (NDVI, NDWI, or a groundwater proxy) with STAC metadata.

Query parameters:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `layer_type` | string | `ndvi` | `ndvi` · `ndwi` · `groundwater` |
| `min_lon` | float | `81.1` | |
| `min_lat` | float | `24.4` | |
| `max_lon` | float | `81.5` | |
| `max_lat` | float | `24.8` | |

Example:

```bash
GET /eo/layers?layer_type=ndwi
```

Response (`EOLayerResponse`):

```json
{
  "layer_type":"ndwi",
  "tile_url":"http://localhost:8000/map/overlay/ndwi",
  "bounds":[81.1,24.4,81.5,24.8],
  "stac_metadata":{"scene_id":"...","acquisition_date":"...",
    "cloud_cover_percent":0.27,"source_api":"...","provenance_tag":"RECENT"},
  "provenance_tag":"RECENT"
}
```

Unsupported layer types return `400`; invalid/oversized bboxes return `400`
(`AOI_LIMIT_EXCEEDED`).

---

## Module 3 — Water Intelligence Engine

### `POST /water/analyze` (also `POST /api/v1/water/analyze`)

Core water-intelligence endpoint. Request (`WaterAnalyzeRequest`; all fields
optional):

```json
{
  "geography_id": "rewa",
  "bbox": [81.1, 24.4, 81.5, 24.8],
  "date_range_start": "2026-01-01",
  "date_range_end": "2026-08-01",
  "data_sources": ["Sentinel-2","Sentinel-1","Landsat"],
  "budget_inr": 200000000.0,
  "time_horizon_months": 36,
  "risk_tolerance": "MEDIUM"
}
```

Response (`WaterAnalyzeResponse`):

```json
{
  "geography_id": "rewa",
  "water_indicators": [ { "indicator_name":"NDVI","value":0.683,
      "unit":"dimensionless","source":"Sentinel-2 L2A (Bands 8 & 4)",
      "measurement_type":"proxy","direct_measurement":false,
      "confidence":0.96,"limitations":"...","pedigree":"MODELLED_SATELLITE_PROXY",
      "disclaimer":"Vegetation condition proxy index"} ],
  "detected_signals": [ { "id":"SIG-WATER-001","domain":"Water",
      "severity":"ELEVATED","affected_villages_count":18,
      "provenance_tag":"MODELLED_SATELLITE_PROXY","direct_measurement":false } ],
  "problem_categories": ["water_stress","surface_water_change",
      "vegetation_water_stress","pollution_context_indicators"],
  "evidence_used": [ { "citation":"...","type":"Remote Sensing STAC API",
      "confidence":0.95,"direct_measurement":false } ],
  "relevant_observations": [ { "satellite":"Sentinel-2","processing_status":"..." } ],
  "confidence_metadata": { "overall_confidence":"HIGH (STAC Proxy Verified)", "..." }
}
```

> **Honesty notes:** all signals and indicators are explicitly marked as
> spectral **proxies** (`direct_measurement: false`). Groundwater depth and
> chemical contamination are *not* directly measured.

### `GET /context/{geography_id}/signals`

Returns derived indicators + problem signals for a geography (currently
returns a fixed, demonstration payload):

```bash
GET /context/rewa/signals
```

```json
{
  "geography_id":"rewa",
  "water_stress_index":0.74,
  "vegetation_condition_index":0.68,
  "flood_risk_score":0.32,
  "groundwater_drawdown_rate_m_yr":-1.2,
  "signals": [ ... ]
}
```

---

## Module 4 — Intervention Knowledge Graph

### `GET /graph/interventions`

Lists intervention cards, optionally filtered by `domain`
(default `Water`).

```bash
GET /graph/interventions?domain=Agriculture
```

Returns `List<InterventionCardSchema>`. Each card:

```json
{
  "id":"INT-001",
  "name":"Rooftop Rainwater Harvesting Units",
  "domain":"Water",
  "category":"Rainwater Harvesting",
  "cost_inr":2500000,
  "water_security_score":78.5,
  "sdg_alignments":["6.1","6.2"],
  "jobs_created":14,
  "implementation_time_months":6,
  "technology_maturity_lvl":9,
  "risk_level":"LOW",
  "dependencies":[],
  "compatible_with":["INT-002","INT-003"]
}
```

### `GET /graph/chains/{intervention_id}`

Traverses the intervention graph from a root node (recursive CTE simulation).

```bash
GET /graph/chains/INT-ALGAE-01?max_depth=5
```

`max_depth` ∈ `[1, 10]`, default `5`. Response (`GraphChainSchema`):

```json
{
  "root_intervention_id":"INT-ALGAE-01",
  "max_depth":5,
  "path_nodes":[ ... ],
  "edges":[ { "source_id":"...","target_id":"...","edge_type":"ADDRESSES" } ]
}
```

### `POST /graph/discover`

Discovers reachable interventions for a detected problem.

```json
{"detected_problem":"Untreated wastewater discharge",
 "geography_id":"rewa","max_depth":5}
```

Response:

```json
{"status":"discovered","detected_problem":"...","geography_id":"rewa",
 "reachable_interventions_count":4,"chain_graph":{ ... }}
```

---

## Module 5 — Feasibility Filter Engine

### `POST /feasibility/filter`

Runs the 4-stage filter (geographic, budget, time, risk) over the intervention
dataset.

Request (`FeasibilityFilterRequest`):

```json
{
  "candidate_intervention_ids": [],
  "geography_id": "rewa",
  "budget_limit_inr": 200000000.0,
  "time_horizon_months": 36,
  "max_risk_level": "HIGH"
}
```

Response (`FeasibilityFilterResponse`):

```json
{
  "total_candidates": 15,
  "viable_candidates_count": 15,
  "viable_interventions": [ ... ],
  "filter_matrix": [
    { "intervention_id":"INT-001","intervention_name":"...",
      "passed_all":true,"geographic_filter_pass":true,
      "budget_filter_pass":true,"time_filter_pass":true,
      "risk_filter_pass":true,"failure_reasons":[] }
  ]
}
```

---

## Module 6 — NSGA-II Multi-Objective Optimizer

### `POST /optimize/run` (also `POST /api/v1/optimize/run`)

Runs the 4-objective genetic optimizer (`cost` ↓, `water security` ↑,
`jobs` ↑, `SDG alignment` ↑) with a budget constraint.

Request (`OptimizeRunRequest`):

```json
{
  "geography_id": "rewa",
  "budget_limit_inr": 200000000.0,
  "time_horizon_months": 36,
  "objective_weights": null
}
```

Response (`OptimizeRunResponse`):

```json
{
  "status": "success",
  "budget_inr": 200000000.0,
  "pareto_solutions_count": 39,
  "portfolios": [
    {
      "id":"PORTFOLIO_1",
      "name":"Portfolio A — Maximum Water Impact",
      "focus":"Prioritizes high-scoring water retention infrastructure",
      "total_cost_inr": 199500000.0,
      "cost_crores": 19.95,
      "water_security_score": 830.0,
      "jobs_created": 890,
      "sdg_alignments":["6.1","6.2", ...],
      "sdg_count":7,
      "intervention_count":11,
      "interventions":[ ... ],
      "co_benefits":[ ... ],
      "applicable_conditions":{"target_district":"Rewa","budget_cap_crores":20.0},
      "provenance":{"method":"pymoo NSGA-II Multi-Objective Genetic Algorithm",
        "provenance_tag":"SYNTHETIC-MODELED",
        "confidence":"Pareto Non-Dominated Frontier Solved"}
    }
  ]
}
```

Empty (zero-intervention) solutions are filtered out of the Pareto front so
every returned portfolio is actionable.

---

## Module 7 — Portfolios, Implementation Plan & Provenance

### `GET /portfolio/pareto` (also `GET /api/v1/portfolio/pareto`)

Returns the default Pareto-optimal portfolio set.

```json
{"status":"success","portfolios":[ ... ]}
```

### `POST /portfolio/{portfolio_id}/implementation-plan`

Generates a phased implementation plan for a portfolio (falls back to the
first portfolio if the ID is unknown).

```bash
POST /portfolio/PORTFOLIO_1/implementation-plan
```

Response (`ImplementationPlanResponse`):

```json
{
  "portfolio_id":"PORTFOLIO_1",
  "portfolio_name":"Portfolio A — Maximum Water Impact",
  "total_cost_inr":199500000.0,
  "total_duration_months": 24,
  "stakeholder_allocation": {
    "Government (Panchayati Raj & Water Resources Dept)": 120000000.0,
    "CSR / Philanthropic Grant": 40000000.0,
    "NGO / Community Water Users Association": 39500000.0
  },
  "intervention_sequence": [
    {"phase":1,"phase_name":"Phase 1: ...","intervention_id":"INT-001",
     "intervention_name":"...","duration_months":6,"estimated_cost_inr":2500000,
     "responsible_stakeholder":"Government (...)", "dependencies":[],
     "key_milestones":[ ... ]}
  ],
  "monitoring_indicators":[ ... ],
  "created_at":"2026-08-14T00:00:00Z"
}
```

### `GET /provenance/{portfolio_id}`

Returns the explainability/audit trail for a portfolio.

```bash
GET /provenance/PORTFOLIO_1
```

Highlights of `ProvenanceAuditSchema`:

- `optimizer_engine`, `objective_weights_applied`
- `feasibility_filter_audit` — per-stage pass/reject counts
- `knowledge_graph_chain_sources`, `earth_observation_scene_ids`
- `satellite_stac_provenance`, `confidence_score`

---

## Master Orchestration Pipeline

### `POST /nexus/analyze` (also `POST /api/v1/nexus/analyze`)

Submits an end-to-end pipeline job. Request (`NexusAnalyzeRequest`):

```json
{
  "geography_id": "rewa",
  "bbox": [81.1, 24.4, 81.5, 24.8],
  "date_range_start": "2024-01-01",
  "date_range_end": "2026-08-01",
  "data_sources": ["Sentinel-2","Sentinel-1","Landsat"],
  "budget_limit_inr": 200000000.0,
  "time_horizon_months": 36,
  "max_risk_level": "HIGH"
}
```

Immediate response (`NexusJobStatusResponse`):

```json
{"job_id":"job-1a2b3c4d5e6f","status":"PROCESSING",
 "progress_percent":5,"stage":"Stage 0/7: Initializing Pipeline & Background Worker",
 "created_at":"...","updated_at":"...","error_message":null,"result":null}
```

The pipeline runs in a background thread and progresses through 7 stages:
EO acquisition → signals → graph discovery → feasibility → optimization →
implementation plan → telemetry.

### `GET /nexus/jobs/{job_id}` (also `/api/v1/nexus/jobs/{job_id}`)

Polls job status. `status` moves `PROCESSING → COMPLETED` (or `FAILED`).
When done, `progress_percent=100` and `result` contains the full payload:

```json
{
  "job_id":"job-1a2b3c4d5e6f",
  "status":"COMPLETED",
  "progress_percent":100,
  "stage":"Stage 7/7: Master Pipeline Complete",
  "result": {
    "orchestration_id":"job-1a2b3c4d5e6f",
    "geography_id":"rewa",
    "earth_observation": { "observations_count":2, "indicators":[...], "confidence":{...} },
    "water_intelligence": { "detected_signals":[...], "problem_categories":[...],
                            "evidence":[...] },
    "intervention_graph": { "discovered_nodes_count":7, "discovered_edges_count":8 },
    "feasibility": { "total_candidates":15, "viable_candidates_count":15,
                     "filter_matrix":[...] },
    "optimization": { "pareto_solutions_count":39, "top_portfolios":[...],
                      "no_solution_reason":null },
    "implementation_plan": { ... },
    "provenance": { "orchestration_engine":"NEXUS Master Pipeline Orchestrator v2.0", ... }
  }
}
```

Unknown job IDs return `404`.

---

## Map Data Ingest API

Prefixed `/api/v1/maps`. Supports vector (`geojson`, `shp`, `kml`, `dxf`, …),
raster (`tif`, `png`, …), point-cloud (`las`, `laz`), tabular (`csv`, `xlsx`),
document (`pdf`, `docx`), and bundle (`zip`) uploads.

### `GET /api/v1/maps/health`

```json
{"status":"ok","service":"nexus-ingest","version":"0.1.0",
 "supported_types":["geojson","shp","tif","las","csv","pdf", ...]}
```

### `POST /api/v1/maps`

Multipart upload. Form fields: `category` (one of `base_maps`, `utilities`,
`imagery`, `geological`, `water_demand`, `field_observations`, `engineering`,
`weather`, `general`), optional `name`, `source_crs`, `usage`. Files are
grouped (shapefile sets merge into one record) and converted.

```bash
curl -F "files=@village.geojson" -F "category=base_maps" \
     http://localhost:8000/api/v1/maps
```

Response: `201` with `UploadResponse`:

```json
{
  "records":[
    {"id":"73f9...","name":"village.geojson","category":"base_maps",
     "source_type":"geojson","source_filename":"village.geojson",
     "representation":"vector_geojson","target_crs":"EPSG:4326",
     "feature_count":1,"size_bytes":123,"confidence":"high"}
  ],
  "summary":{"uploaded":1,"records":1,"representations":["vector_geojson"],"errors":[]}
}
```

### `GET /api/v1/maps`

Lists records (heavy payloads trimmed). Returns `List<RecordMeta>`.

### `GET /api/v1/maps/{record_id}`

Single record. `404` if missing.

### `GET /api/v1/maps/{record_id}/geojson`

Returns the embedded GeoJSON payload (if the record has one).

### `DELETE /api/v1/maps/{record_id}`

Deletes the record and its upload files. `204` on success, `404` if missing.

---

## Budget, Locations, Social Groups & Timeline

### Budget — `GET`/`PUT /api/v1/budget`

Singleton resource (exactly one budget).

- `GET` → `404` until set; otherwise the `BudgetRecord`.
- `PUT` → create/replace. Body (`BudgetCreate`):

```json
{"target_budget":100000000,"maximum_budget":150000000,
 "intensity":7,"details":"Rewa water program","name":"Q3 budget"}
```

Validation: `maximum_budget >= target_budget`; `intensity` ∈ `[1,10]`;
budget amounts > 0.

### Locations — `/api/v1/locations`

Full CRUD, identified by names (no coordinates).

- `POST /api/v1/locations` — create (`LocationCreate`):
  ```json
  {"state":"Madhya Pradesh","district":"Rewa","city":"Rewa",
   "intensity":5,"details":"test","name":"Optional label"}
  ```
- `GET /api/v1/locations` — list (`LocationListResponse{count, items}`)
- `GET /api/v1/locations/{record_id}` — single record
- `PUT /api/v1/locations/{record_id}` — replace
- `DELETE /api/v1/locations/{record_id}` — `204`

### Social Groups — `/api/v1/social`

- `GET /api/v1/social/taxonomy` — lists all enum values (income groups,
  employment statuses, genders, caste categories, area types, religions).
- `POST /api/v1/social/groups` — create. Body (`SocialGroupCreate`):
  ```json
  {"name":"Village A","intensity":4,"details":"test",
   "profiles":[{"gender":"male","income_group":"BPL"}]}
  ```
- `GET /api/v1/social/groups` — list
- `GET/PUT/DELETE /api/v1/social/groups/{record_id}`

### Timeline — `GET`/`PUT /api/v1/timeline`

Singleton resource.

```json
{"urgency":9,"expected_duration":"6 months","deadline":"2027-06-30",
 "details":"Monsoon deadline","name":"Monsoon timeline"}
```

`urgency` ∈ `[1,10]`; `deadline` is `YYYY-MM-DD`.

---

## Legacy Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/interventions/` | Alias for the intervention dataset |
| `GET` | `/map/metadata` | Static STAC map metadata for the Rewa scene |
| `GET` | `/map/overlay/{layer_type}` | Returns a PNG tile (`ndvi`/`ndwi`) |

---

## Error Handling

- **`400 Bad Request`** — input validation failures (including `AOI_LIMIT_EXCEEDED`
  for oversized/invalid bboxes). Body:
  ```json
  {"error":"Bad Request Input Validation Failure","message":"...","path":"/..."}
  ```
- **`404 Not Found`** — unknown jobs/records/resources.
- **`405 Method Not Allowed`** — wrong HTTP verb.
- **`413`** — uploaded file exceeds the size cap (2 GiB default).
- **`422 Unprocessable Entity`** — Pydantic schema validation errors
  (e.g. invalid enum value, `intensity > 10`).
- **`500 Internal Server Error`** — unexpected failures; the global handler
  returns a structured JSON envelope rather than a bare traceback.

---

## Testing

A full test suite lives in `tests/` (65 tests, `pytest` + `httpx`),
covering every endpoint group above. It uses an offline `MockEOProvider`
and an isolated temp data directory so the suite runs without Postgres,
Redis, the Planetary Computer STAC API, or network access.

```bash
cd backend
source .venv/bin/activate
pytest                 # run everything
pytest tests/test_nexus.py   # master pipeline + route registry
```

---

## Full Route Reference

| Method | Path | Summary |
|--------|------|---------|
| GET | `/` | Service root / status |
| GET | `/health` | Liveness |
| GET | `/ready` | Readiness |
| GET | `/api/v1/system/status` | Subsystem telemetry |
| POST | `/auth/register` | Register user |
| POST | `/auth/login` | Login |
| GET | `/auth/me` | Current user |
| POST | `/auth/onboarding` | Persona workspace onboarding |
| GET | `/workspace/current` | Current workspace context |
| GET | `/eo/layers` | EO layer + STAC metadata |
| POST | `/water/analyze` | Water intelligence (also `/api/v1/...`) |
| GET | `/context/{geography_id}/signals` | Problem signals |
| GET | `/graph/interventions` | Interventions (by domain) |
| GET | `/graph/chains/{intervention_id}` | Graph chain |
| POST | `/graph/discover` | Discover reachable interventions |
| POST | `/feasibility/filter` | Feasibility filtering |
| POST | `/optimize/run` | NSGA-II optimization (also `/api/v1/...`) |
| GET | `/portfolio/pareto` | Pareto portfolios (also `/api/v1/...`) |
| POST | `/portfolio/{portfolio_id}/implementation-plan` | Plan generator (also `/api/v1/...`) |
| GET | `/provenance/{portfolio_id}` | Explainability audit |
| POST | `/nexus/analyze` | Master pipeline submit (also `/api/v1/...`) |
| GET | `/nexus/jobs/{job_id}` | Job status poll (also `/api/v1/...`) |
| GET/POST/DELETE | `/api/v1/maps` | Ingest records |
| GET | `/api/v1/maps/health` | Ingest health |
| GET | `/api/v1/maps/{record_id}` | Ingest record |
| GET | `/api/v1/maps/{record_id}/geojson` | Ingest GeoJSON |
| DELETE | `/api/v1/maps/{record_id}` | Delete ingest record |
| GET/PUT | `/api/v1/budget` | Singleton budget |
| GET/POST | `/api/v1/locations` | Locations list/create |
| GET/PUT/DELETE | `/api/v1/locations/{record_id}` | Location item |
| GET | `/api/v1/social/taxonomy` | Social taxonomy |
| GET/POST | `/api/v1/social/groups` | Social groups list/create |
| GET/PUT/DELETE | `/api/v1/social/groups/{record_id}` | Social group item |
| GET/PUT | `/api/v1/timeline` | Singleton timeline |
| GET | `/interventions/` | Legacy interventions |
| GET | `/map/metadata` | Legacy map metadata |
| GET | `/map/overlay/{layer_type}` | Legacy PNG overlay |
