"""Tests for legacy ``/interventions`` and ``/map`` endpoints."""
from tests.utils import assert_json_error


def test_interventions_list(client):
    resp = client.get("/interventions/")
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    assert len(items) >= 15
    assert items[0]["id"] == "INT-001"


def test_map_metadata(client):
    resp = client.get("/map/metadata")
    assert resp.status_code == 200
    body = resp.json()
    assert body["scene_id"]
    assert body["cloud_cover_percent"] == 0.27
    assert body["bbox"] == [81.1, 24.4, 81.5, 24.8]
    assert body["crs"] == "EPSG:32644"


def test_map_overlay_ndvi(client):
    resp = client.get("/map/overlay/ndvi")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/png")
    # PNG magic bytes
    assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_map_overlay_ndwi(client):
    resp = client.get("/map/overlay/ndwi")
    assert resp.status_code == 200
    assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"
