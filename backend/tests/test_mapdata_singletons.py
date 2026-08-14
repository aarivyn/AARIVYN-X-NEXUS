"""Tests for the budget, locations, social-groups, and timeline APIs."""
from tests.utils import assert_json_error


def test_budget_lifecycle(client):
    # Not set yet -> 404
    assert client.get("/api/v1/budget").status_code == 404

    body = {
        "target_budget": 100000000,
        "maximum_budget": 150000000,
        "intensity": 7,
        "details": "Rewa water program",
        "name": "Q3 budget",
    }
    resp = client.put("/api/v1/budget", json=body)
    assert resp.status_code == 200
    created = resp.json()
    assert created["target_budget"] == 100000000
    assert created["maximum_budget"] == 150000000
    assert created["intensity"] == 7

    # Now retrievable
    resp = client.get("/api/v1/budget")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Q3 budget"

    # Replace
    body2 = dict(body, target_budget=120000000, intensity=8)
    resp = client.put("/api/v1/budget", json=body2)
    assert resp.status_code == 200
    assert resp.json()["target_budget"] == 120000000


def test_budget_validation(client):
    # maximum < target -> 422
    resp = client.put(
        "/api/v1/budget",
        json={"target_budget": 100, "maximum_budget": 50, "intensity": 5},
    )
    assert resp.status_code == 422

    # intensity out of 1..10 -> 422
    resp = client.put(
        "/api/v1/budget",
        json={"target_budget": 100, "maximum_budget": 200, "intensity": 42},
    )
    assert resp.status_code == 422


def test_locations_lifecycle(client):
    # create
    body = {
        "state": "Madhya Pradesh",
        "district": "Rewa",
        "city": "Rewa",
        "intensity": 5,
        "details": "test",
    }
    resp = client.post("/api/v1/locations", json=body)
    assert resp.status_code == 201
    record = resp.json()
    assert record["state"] == "Madhya Pradesh"
    record_id = record["id"]

    # list
    listing = client.get("/api/v1/locations").json()
    assert listing["count"] == 1
    assert listing["items"][0]["id"] == record_id

    # get
    one = client.get(f"/api/v1/locations/{record_id}")
    assert one.status_code == 200

    # update
    resp = client.put(
        f"/api/v1/locations/{record_id}",
        json=dict(body, intensity=9, city="Mauganj"),
    )
    assert resp.status_code == 200
    assert resp.json()["intensity"] == 9

    # delete
    assert client.delete(f"/api/v1/locations/{record_id}").status_code == 204
    assert client.get(f"/api/v1/locations/{record_id}").status_code == 404


def test_locations_validation(client):
    resp = client.post(
        "/api/v1/locations",
        json={"state": "", "district": "x", "intensity": 5},
    )
    assert resp.status_code == 422


def test_social_taxonomy(client):
    resp = client.get("/api/v1/social/taxonomy")
    assert resp.status_code == 200
    body = resp.json()
    assert body["income_groups"]
    assert body["employment_statuses"]
    assert body["genders"]
    assert body["caste_categories"]
    assert body["area_types"]
    assert body["religions"]


def test_social_groups_lifecycle(client):
    body = {
        "name": "Village A",
        "profiles": [
            {"gender": "male", "income_group": "BPL"},
        ],
        "intensity": 4,
        "details": "test",
    }
    resp = client.post("/api/v1/social/groups", json=body)
    assert resp.status_code == 201, resp.text
    record = resp.json()
    record_id = record["id"]
    assert record["profiles"][0]["gender"] == "male"

    listing = client.get("/api/v1/social/groups").json()
    assert listing["count"] == 1

    one = client.get(f"/api/v1/social/groups/{record_id}")
    assert one.status_code == 200

    resp = client.put(
        f"/api/v1/social/groups/{record_id}",
        json=dict(body, intensity=8),
    )
    assert resp.status_code == 200
    assert resp.json()["intensity"] == 8

    assert client.delete(f"/api/v1/social/groups/{record_id}").status_code == 204
    assert client.get(f"/api/v1/social/groups/{record_id}").status_code == 404


def test_timeline_lifecycle(client):
    assert client.get("/api/v1/timeline").status_code == 404

    body = {
        "urgency": 9,
        "expected_duration": "6 months",
        "deadline": "2027-06-30",
        "details": "Monsoon deadline",
        "name": "Monsoon timeline",
    }
    resp = client.put("/api/v1/timeline", json=body)
    assert resp.status_code == 200
    created = resp.json()
    assert created["urgency"] == 9
    assert created["deadline"] == "2027-06-30"

    resp = client.get("/api/v1/timeline")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Monsoon timeline"


def test_timeline_validation(client):
    resp = client.put(
        "/api/v1/timeline",
        json={"urgency": 99, "expected_duration": "x", "deadline": "2027-01-01"},
    )
    assert resp.status_code == 422
