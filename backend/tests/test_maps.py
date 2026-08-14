"""Tests for the map-data ingest module (``/api/v1/maps``)."""
from tests.utils import assert_json_error


def test_maps_health(client):
    resp = client.get("/api/v1/maps/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "nexus-ingest"
    assert "geojson" in body["supported_types"]


def test_maps_list_empty(client):
    resp = client.get("/api/v1/maps")
    assert resp.status_code == 200
    assert resp.json() == []


def test_maps_upload_geojson(client):
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [81.3, 24.6]},
                "properties": {"name": "Village"},
            }
        ],
    }
    resp = client.post(
        "/api/v1/maps",
        files={"files": ("village.geojson", __import__("json").dumps(geojson), "application/geo+json")},
        data={"category": "base_maps"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["records"], "expected at least one converted record"
    record = body["records"][0]
    assert record["source_filename"] == "village.geojson"
    assert record["representation"] == "vector_geojson"
    assert record["id"]


def test_maps_upload_invalid_category(client):
    resp = client.post(
        "/api/v1/maps",
        files={"files": ("x.geojson", b'{"type":"FeatureCollection","features":[]}', "application/geo+json")},
        data={"category": "not_a_category"},
    )
    assert resp.status_code == 422


def test_maps_get_missing(client):
    resp = client.get("/api/v1/maps/deadbeef")
    assert resp.status_code == 404


def test_maps_delete_missing(client):
    resp = client.delete("/api/v1/maps/deadbeef")
    assert resp.status_code == 404


def test_maps_full_lifecycle(client):
    import json

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [1.0, 2.0]}, "properties": {}}
        ],
    }
    # 1. upload
    resp = client.post(
        "/api/v1/maps",
        files={"files": ("point.geojson", json.dumps(geojson), "application/geo+json")},
        data={"category": "general", "name": "Point"},
    )
    assert resp.status_code == 201
    record_id = resp.json()["records"][0]["id"]

    # 2. list (should contain it)
    listing = client.get("/api/v1/maps").json()
    assert any(r["id"] == record_id for r in listing)

    # 3. get single
    one = client.get(f"/api/v1/maps/{record_id}")
    assert one.status_code == 200
    assert one.json()["id"] == record_id

    # 4. get geojson
    geo = client.get(f"/api/v1/maps/{record_id}/geojson")
    assert geo.status_code == 200
    assert geo.json()["type"] == "FeatureCollection"

    # 5. delete
    assert client.delete(f"/api/v1/maps/{record_id}").status_code == 204
    assert client.get(f"/api/v1/maps/{record_id}").status_code == 404
