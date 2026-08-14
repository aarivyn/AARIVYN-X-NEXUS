"""Shared pytest fixtures for the NEXUS API test-suite.

Ensures:
  * ``app/`` is importable from the test root regardless of CWD.
  * The FastAPI app and its TestClient are created once per session.
  * The Earth-Observation provider is replaced with the offline
    ``MockEOProvider`` so tests are deterministic and never hit the
    public Microsoft Planetary Computer STAC API.
  * Map-data ingest storage is redirected to a temporary directory so
    tests never write into the developer's real ``app/data`` tree.
"""
import os
import sys

import pytest

# Make `app`, `routers`, `services`, `mapdata`, etc. importable.
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(BACKEND_ROOT, "app")
for _p in (APP_DIR, BACKEND_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)


@pytest.fixture(scope="session", autouse=True)
def _isolated_mapdata_storage(tmp_path_factory):
    """Point map-data ingest at an isolated temp dir for the whole session."""
    tmp = tmp_path_factory.mktemp("nexus-mapdata")
    os.environ["NEXUS_DATA_DIR"] = str(tmp)
    # mapdata.config reads NEXUS_DATA_DIR at import time; make sure the module
    # is (re)loaded with the env var set.
    import importlib

    import mapdata.config as _cfg

    importlib.reload(_cfg)
    _cfg.ensure_dirs()
    yield _cfg


@pytest.fixture(autouse=True)
def _clear_ingested_site_data(_isolated_mapdata_storage):
    """Clear ingested singleton/crud data before each test.

    Modules 2-7 now consume the budget / timeline / social-groups / locations
    submitted through the Map Data Ingest API. To keep individual module tests
    deterministic (and independent of ingestion order across the session),
    reset the shared store before every test body runs.
    """
    import mapdata.config as _cfg

    singleton_files = ["budget.json", "timeline.json"]
    for name in singleton_files:
        path = _cfg.DATA_DIR / name
        if path.exists():
            path.unlink()
    for subdir in ("social_groups", "locations"):
        d = _cfg.DATA_DIR / subdir
        if d.exists():
            for p in d.glob("*.json"):
                p.unlink()
    yield


# ---------------------------------------------------------------------------
# App & client fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client():
    """A session-scoped FastAPI TestClient with an offline EO provider.

    Importing ``app.main`` triggers DB/Redis setup with graceful local
    fallbacks (SQLite + in-memory cache) since neither Postgres nor Redis
    is expected to be running in the test environment.
    """
    from fastapi.testclient import TestClient

    import services.water_service as ws
    from services.eo_provider import MockEOProvider

    # Replace the live STAC provider with the offline mock so tests are fast
    # and deterministic.
    ws.get_eo_provider = lambda: MockEOProvider()

    from main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def app():
    """The raw ASGI app instance (for route enumeration / schema checks)."""
    from main import app
    return app
