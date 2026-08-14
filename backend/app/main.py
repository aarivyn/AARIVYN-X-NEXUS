"""NEXUS ingest API — endpoint for adding topographical/site maps.

POST /api/v1/maps   upload one or many files (the full inputs.txt spectrum),
                    each is converted to the NEXUS common representation.
GET  /api/v1/maps   list ingested records.
GET  /api/v1/maps/{id}       fetch one record.
GET  /api/v1/maps/{id}/geojson  fetch the GeoJSON payload of a vector record.
DELETE /api/v1/maps/{id}     remove a record and its stored files.
GET  /health        service status + supported types.
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from . import config, storage
from .ingest import convert
from .schemas import CATEGORIES  # noqa: F401  (re-export for docs)
from .schemas import HealthResponse, RecordMeta, UploadResponse
from .location_routes import router as location_router

app = FastAPI(
    title="NEXUS Ingest API",
    description="Ingest heterogeneous GIS / engineering / field data and reduce it "
                "to a common representation (GeoJSON in EPSG:4326 for geometry, "
                "normalized rasters, extracted text, point-cloud previews).",
    version="0.1.0",
)

SHAPEFILE_EXTS = {".shp", ".shx", ".dbf", ".prj"}
_PRIMARY_EXT = {".shp": 0, ".kmz": 1, ".zip": 2}  # preference within a bundle group


@app.on_event("startup")
def _startup() -> None:
    config.ensure_dirs()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="nexus-ingest",
        version="0.1.0",
        supported_types=sorted(storage.SUPPORTED_EXTENSIONS),
    )


@app.post("/api/v1/maps", response_model=UploadResponse, status_code=201)
async def add_map(
    files: list[UploadFile] = File(..., description="One or more data files"),
    category: str = Form("general", description="Data category (see inputs.txt taxonomy)"),
    name: str | None = Form(None, description="Display name (defaults to filename)"),
    source_crs: str | None = Form(None, description="Override source CRS, e.g. EPSG:32633"),
    usage: str | None = Form(None, description="What the data is for, e.g. road_network, "
                             "utility_network, terrain; inferred from filename when omitted"),
) -> UploadResponse:
    if category not in CATEGORIES:
        raise HTTPException(422, f"category must be one of {sorted(CATEGORIES)}")

    groups = _group_uploads(files)
    records: list[RecordMeta] = []
    errors: list[dict] = []

    for group in groups:
        try:
            rec = _process_group(group, category, name, source_crs, usage)
            if rec is not None:
                storage.save_record(rec.model_dump(mode="json"))
                records.append(rec)
        except HTTPException:
            raise
        except Exception as e:
            errors.append({"files": [g.filename for g in group], "error": f"{type(e).__name__}: {e}"})

    if not records and errors:
        raise HTTPException(500, f"all uploads failed: {errors}")

    summary = {
        "uploaded": len(files),
        "records": len(records),
        "representations": {r.representation for r in records},
        "errors": errors,
    }
    return UploadResponse(records=records, summary=summary)


@app.get("/api/v1/maps", response_model=list[RecordMeta])
def list_maps() -> list[RecordMeta]:
    recs = storage.list_records()
    for r in recs:
        # trim heavy payloads in the listing view
        if isinstance(r.get("data"), dict):
            r["data"] = {k: v for k, v in r["data"].items() if k not in ("geojson", "preview", "text")}
    return [RecordMeta(**r) for r in recs]


@app.get("/api/v1/maps/{record_id}", response_model=RecordMeta)
def get_map(record_id: str) -> RecordMeta:
    rec = storage.read_record(record_id)
    if rec is None:
        raise HTTPException(404, f"no record {record_id}")
    return RecordMeta(**rec)


@app.get("/api/v1/maps/{record_id}/geojson")
def get_map_geojson(record_id: str):
    rec = storage.read_record(record_id)
    if rec is None:
        raise HTTPException(404, f"no record {record_id}")
    geojson = (rec.get("data") or {}).get("geojson")
    if geojson is None:
        raise HTTPException(404, "record has no GeoJSON payload")
    return JSONResponse(content=geojson)


@app.delete("/api/v1/maps/{record_id}", status_code=204)
def delete_map(record_id: str) -> None:
    if not storage.delete_record(record_id):
        raise HTTPException(404, f"no record {record_id}")


# --------------------------------------------------------------------------
# upload processing
# --------------------------------------------------------------------------

def _group_uploads(files: list[UploadFile]) -> list[list[UploadFile]]:
    """Group files into conversion units.

    A shapefile set (.shp/.dbf/.shx/.prj sharing a stem) becomes one unit;
    everything else is its own unit.
    """
    singleton: dict[str, UploadFile] = {}
    shp_sets: dict[str, list[UploadFile]] = {}
    for f in files:
        ext = Path(f.filename or "").suffix.lower()
        stem = Path(f.filename or "").stem
        if ext in SHAPEFILE_EXTS:
            shp_sets.setdefault(stem, []).append(f)
        else:
            singleton[f.filename or str(uuid.uuid4())] = f

    groups: list[list[UploadFile]] = []
    for stem, members in shp_sets.items():
        if any(m.filename.lower().endswith(".shp") for m in members):
            groups.append(members)  # full set incl. dbf/shx/prj
        else:
            groups.extend([m] for m in members)  # stray support file alone
    groups.extend([f] for f in singleton.values())
    # deterministic-ish order: shapefile sets first, then singletons
    groups.sort(key=lambda g: _PRIMARY_EXT.get(Path(g[0].filename or "").suffix.lower(), 99))
    return groups


def _process_group(group: list[UploadFile], category: str, name: str | None,
                   source_crs: str | None, usage: str | None = None) -> RecordMeta | None:
    record_id = uuid.uuid4().hex
    record_dir = config.UPLOAD_DIR / record_id
    record_dir.mkdir(parents=True, exist_ok=True)

    saved: list[Path] = []
    for f in group:
        dest = record_dir / Path(f.filename or "unnamed").name
        size = 0
        with dest.open("wb") as out:
            while chunk := f.file.read(1024 * 1024):
                size += len(chunk)
                if size > config.MAX_UPLOAD_BYTES:
                    shutil.rmtree(record_dir, ignore_errors=True)
                    raise HTTPException(413, f"{f.filename} exceeds size limit")
                out.write(chunk)
        saved.append(dest)
        f.file.close()

    shp = next((p for p in saved if p.suffix.lower() == ".shp"), None)
    if shp is not None:
        # a .dbf/.shx/.prj uploaded without .shp is not a record on its own
        return convert.shapefile_record_from_files(saved, category, source_crs, name, usage)

    main_file = sorted(saved, key=lambda p: _PRIMARY_EXT.get(p.suffix.lower(), 99))[0]
    return convert.convert_file(main_file, category, source_crs, name, usage)


app.include_router(location_router)

if __name__ == "__main__":

    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
