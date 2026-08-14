"""Tests for Module 2: Earth Observation Ingestion (``/eo``)."""
from tests.utils import assert_json_error


def test_get_eo_layer_default(client):
    resp = client.get("/eo/layers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["layer_type"] == "ndvi"
    assert body["bounds"] == [81.1, 24.4, 81.5, 24.8]
    assert body["tile_url"] == "http://localhost:8000/map/overlay/ndvi"
    assert body["stac_metadata"]["scene_id"]


def test_get_eo_layer_ndwi(client):
    resp = client.get("/eo/layers", params={"layer_type": "ndwi"})
    assert resp.status_code == 200
    assert resp.json()["layer_type"] == "ndwi"


def test_get_eo_layer_groundwater(client):
    resp = client.get("/eo/layers", params={"layer_type": "groundwater"})
    assert resp.status_code == 200
    assert resp.json()["layer_type"] == "groundwater"


def test_eo_layer_unsupported_type(client):
    resp = client.get("/eo/layers", params={"layer_type": "radar"})
    body = assert_json_error(resp, 400)
    assert "Unsupported layer type" in body["detail"]


def test_eo_layer_invalid_bbox(client):
    # min_lon >= max_lon triggers AOI validation failure
    resp = client.get(
        "/eo/layers",
        params={"min_lon": 82.0, "min_lat": 24.4, "max_lon": 81.5, "max_lat": 24.8},
    )
    body = assert_json_error(resp, 400)
    assert body["detail"]["error"] == "AOI_LIMIT_EXCEEDED"


def test_eo_layer_custom_bbox(client):
    resp = client.get(
        "/eo/layers",
        params={"min_lon": 81.0, "min_lat": 24.3, "max_lon": 81.2, "max_lat": 24.5},
    )
    assert resp.status_code == 200
    assert resp.json()["bounds"] == [81.0, 24.3, 81.2, 24.5]
