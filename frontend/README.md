# NEXUS — Frontend

A map-first command centre for the NEXUS geospatial decision-intelligence
backend. Built for a district officer who has a problem, a budget and a
deadline, and needs to defend the plan they choose.

```
OBSERVE → DETECT → UNDERSTAND → INTERVENTIONS → OPTIMIZE → DECIDE → MONITOR
```

## Running it

```bash
cp .env.example .env.local     # set NEXT_PUBLIC_API_URL
npm install
npm run dev                    # http://localhost:3000
```

The FastAPI backend must be running:

```bash
cd backend && uvicorn app.main:app --reload --port 8000
```

No map API key is required — the default basemap uses OpenStreetMap raster
tiles, desaturated at runtime. Set `NEXT_PUBLIC_MAP_STYLE_URL` to use a vector
style instead.

## Stack

Next.js 14 (App Router) · TypeScript · Tailwind · MapLibre GL · Recharts ·
Framer Motion · Zustand.

## One thing the brief got wrong

The brief describes locations as holding a GeoJSON polygon. They do not.
`app/mapdata/location_schemas.py` defines a location as:

```
id · name? · state · district · city? · intensity (1–10) · details · created_at · updated_at
```

Names only, no geometry. So the registry does full CRUD on those fields, and
polygons are resolved *from* the names via the same Nominatim service the
backend uses internally (`app/mapdata/name_to_geojson.py`), through
`src/lib/api/geocode.ts` — throttled and cached to respect the public
geocoder's rate limit.

Free-hand polygon drawing is kept separate: it defines the analysis bounding
box sent to `/api/v1/nexus/analyze`. It is *not* persisted as a location,
because there is no field to persist it into. When the backend gains a
geometry column, `geocode.ts` is the single file to change.

## Roles — the NEXUS Network

`/` is a role-selection screen: **How will you use NEXUS?** Five answers, each
leading to a different set of tools over the same map, the same location
registry and the same evidence.

| Role | Job | Route |
|---|---|---|
| Government / Decision Maker | Plan & decide | `/workspace` |
| NGO / Implementation Partner | Implement & contribute | `/network/ngo` |
| CSR / Funding Partner | Fund & monitor impact | `/network/csr` |
| Student / Researcher | Explore & use data | `/network/research` |
| Community | Report & verify | `/network/community` |

The government workflow is untouched — the Network modes are a separate layer
that never mixes into it. Each role gets its own accent colour, its own tab
set, and a mode banner naming its one job. `NetworkShell` supplies the shared
chrome; `MapDock` is the identical component the government workspace uses, so
a report filed by a community member shows up on the officer's map immediately.

### Roles run on the backend's real persona system

`app/schemas.py` already defines `PersonaType` and typed onboarding payloads
for every one of these roles, and `auth_service.resolve_workspace_context`
returns a different geography scope and permission set per persona. So each
mode's profile form posts the exact payload its persona expects:

| Role | Endpoint | Payload |
|---|---|---|
| NGO | `POST /auth/onboarding` | `ngo` — organization, operating_regions, communities_served, focus_areas, implementation_capacity |
| CSR | `POST /auth/onboarding` | `csr_funder` — organization, funding_program, available_budget_inr, focus_areas, target_geography, time_horizon_years |
| Researcher / Student | `POST /auth/onboarding` | `researcher` / `student` — name, institution, region_of_interest |
| Community | `POST /auth/onboarding` | `community` — location_name, problem_category |

Every mode also resolves `GET /workspace/current?persona=` on entry, and the
returned `geography_name` is shown in the mode banner.

### What each role reads

- **NGO** — `GET /graph/interventions` for opportunities, ranked by overlap
  with the profile's expertise; `GET /api/v1/locations` for where the need is.
- **CSR** — `GET /api/v1/portfolio/pareto` for verified projects, with the same
  Pareto scatter and comparison radar the government workspace uses. Projects
  above the funding envelope are marked, not hidden.
- **Research** — `GET /api/v1/maps` for the ingested dataset catalogue, with
  real GeoJSON download links for vector layers; `GET /context/{id}/signals`
  for abnormalities and derived indices. A methodology tab explains the
  provenance tags, because most indicators are spectral proxies and citing one
  as a ground measurement would be wrong.
- **Community** — reports file to `POST /api/v1/locations` (severity maps onto
  `intensity`, the account maps onto `details`), then resolve to a polygon and
  appear on the shared map straight away.

### Participation actions have no backend yet

`src/lib/api/network.ts` defines the contract for interest registration,
funding commitment and community feedback. All three throw `NotConnectedError`
and the UI says so at the point of action — the record is kept in session and
labelled unsaved rather than reported as filed. Same pattern as
`monitoring.ts` and `decisions.ts`.

## Backend endpoints in use

| Stage | Endpoint |
|---|---|
| Registry (all stages) | `GET/POST /api/v1/locations`, `GET/PUT/DELETE /api/v1/locations/{id}` |
| Detect | `POST /api/v1/nexus/analyze`, `GET /api/v1/nexus/jobs/{id}` |
| Gap | `GET /context/{geography_id}/signals` |
| Interventions | `GET /graph/interventions`, `POST /feasibility/filter` |
| Optimize | `POST /api/v1/optimize/run` |
| Decide | `POST /api/v1/portfolio/{id}/implementation-plan`, `GET /provenance/{id}` |
| Status bar | `GET /api/v1/system/status` |

## Not yet connected

Two service modules define the contract for endpoints the backend does not
have, so the UI can say so plainly instead of showing a plausible number:

- `src/lib/api/monitoring.ts` — actual outcome readings, re-optimization trigger
- `src/lib/api/decisions.ts` — persisting an approval record

Each throws `NotConnectedError`. Wiring them up means replacing the function
bodies with `api(...)` calls; no calling component changes.

## The provenance rule

Every number on screen is colour-coded by where it came from, and the key sits
permanently in the left rail:

| | |
|---|---|
| **You entered** — pale blue `#C7D6EA` | the officer's own input |
| **Observed** — cyan `#4CC9E8` | measured or satellite-derived |
| **NEXUS analysis** — amber `#F0A63C` | inferred, modelled, recommended |
| **Critical** — coral `#FF5C6C` | findings needing attention |

The rule is enforced in code, not by convention: the `Origin` component is the
only way a panel labels its data, and `2px` inset borders (`.from-entered`,
`.from-observed`, `.from-inferred`) carry it down to individual cards. A
satellite proxy is never allowed to look like a ground measurement — signal
cards carry an explicit "what this cannot tell you" block quoting the
backend's own `limitations` field.

## Structure

```
src/
  app/workspace/          the single working surface
  components/
    shell/                top bar, pipeline rail, workspace layout
    map/                  MapLibre canvas, draw tool, location registry CRUD
    stages/               one file per pipeline stage
    charts/               Pareto scatter, comparison radar, trajectory
    ui/primitives.tsx     Panel, Button, Field, Badge, Origin, Stat, Empty…
  lib/
    api/                  every network call; nothing else calls fetch
    store.ts              pipeline state
    types.ts              mirrors the FastAPI schemas
```
