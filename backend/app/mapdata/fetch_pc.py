"""
NEXUS - Planetary Computer data fetcher
========================================
Input:  a GeoJSON Polygon/MultiPolygon (the affected area).
Output: pc_water_shortage_data.json — signed STAC items for every relevant
        layer (imagery, terrain, land use, surface water, rainfall) that
        intersects the polygon, ready for downstream processing (raster
        clipping, feature extraction, the NSGA-II optimizer, etc).

No API key is required — Planetary Computer's STAC search and SAS-token
signing are open. An optional subscription key just raises rate limits
(set PC_SUBSCRIPTION_KEY env var if you have one).

Install:
    pip install pystac-client planetary-computer shapely
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta

from shapely import geometry

from .name_to_geojson import get_district_geojson
import planetary_computer as pc
from pystac_client import Client
from shapely.geometry import shape

STAC_API = "https://planetarycomputer.microsoft.com/api/stac/v1"
SUBSCRIPTION_KEY = os.environ.get("PC_SUBSCRIPTION_KEY")

# Number of retry attempts for transient STAC/network failures (connection
# resets, remote disconnects, etc). A value <= 1 disables retries.
RETRIES = int(os.environ.get("PC_RETRIES", "3"))
# Per-search timeout in seconds. Planetary Computer can take a while for large
# AOIs/date ranges; this bounds it so a single slow search can't hang the
# whole request forever.
SEARCH_TIMEOUT = float(os.environ.get("PC_SEARCH_TIMEOUT", "60"))
# Seconds to sleep between layer searches to avoid bursting the STAC API and
# triggering connection drops/rate limiting.
LAYER_DELAY = float(os.environ.get("PC_LAYER_DELAY", "1.0"))


# Collection configuration shared by fetch_all_layers. Exposed as a
# module-level constant so API routes can advertise supported layers.
LAYERS = {
    "sentinel2_imagery": dict(
        collection_id="sentinel-2-l2a",
        query={"eo:cloud_cover": {"lt": 20}},
    ),
    "terrain_dem": dict(
        collection_id="cop-dem-glo-30",
        datetime_range=None,
    ),
    "land_use_land_cover": dict(
        collection_id="io-lulc-annual-v02",
        datetime_range="2017-01-01/2024-12-31",
    ),
    "surface_water": dict(
        collection_id="jrc-gsw",
        datetime_range=None,
    ),
    "rainfall_gpm_imerg": dict(
        collection_id="gpm-imerg-hhr",
        datetime_range="2020-01-01/2024-12-31",
    ),
    "landsat_imagery": dict(
        collection_id="landsat-c2-l2",
        query={"eo:cloud_cover": {"lt": 20}},
    ),
}


def get_catalog():
    if SUBSCRIPTION_KEY:
        pc.settings.set_subscription_key(SUBSCRIPTION_KEY)
    return Client.open(
        STAC_API,
        modifier=pc.sign_inplace,
        # Pystac-client forwards kwargs to its underlying httpx.Client; a
        # generous timeout prevents an individual search from hanging.
        timeout=SEARCH_TIMEOUT,
    )


def load_aoi_geojson(path_or_geojson):
    """
    Accepts either a path to a .geojson file, or a GeoJSON dict already
    in memory. Returns (geometry_dict, bbox) for a single Polygon/MultiPolygon.
    Handles bare Geometry, Feature, or FeatureCollection input.
    """
    if isinstance(path_or_geojson, dict):
        data = path_or_geojson
    else:
        with open(path_or_geojson) as f:
            data = json.load(f)

    if data.get("type") == "FeatureCollection":
        geom = data["features"][0]["geometry"]
    elif data.get("type") == "Feature":
        geom = data["geometry"]
    else:
        geom = data  # bare geometry

    bbox = list(shape(geom).bounds)  # [min_lon, min_lat, max_lon, max_lat]
    return geom, bbox


def search_collection(catalog, collection_id, geometry, datetime_range=None, query=None, limit=20):
    """Generic STAC search against one Planetary Computer collection, using
    true polygon intersection rather than a bbox.

    Retries transient connection failures (e.g. ``RemoteDisconnected``) with
    exponential backoff so a single dropped connection doesn't fail a layer.
    """
    last_exc: Exception | None = None
    for attempt in range(max(1, RETRIES)):
        try:
            search = catalog.search(
                collections=[collection_id],
                intersects=geometry,
                datetime=datetime_range,
                query=query,
                limit=limit,
            )
            return list(search.items())
        except Exception as exc:  # noqa: BLE001 - re-raise only after retries
            last_exc = exc
            if attempt + 1 >= RETRIES:
                break
            backoff = 2 ** attempt  # 1s, 2s, 4s, ...
            print(
                f"[retry] {collection_id}: {exc} "
                f"(attempt {attempt + 1}/{RETRIES}, backing off {backoff}s)"
            )
            time.sleep(backoff)
    raise last_exc  # type: ignore[misc]


def fetch_all_layers(city, district, start_date, end_date, state=None):
    """
    Fetch layers relevant to a water-shortage intervention analysis for a
    given AOI polygon and time window. Returns {layer_name: [signed item dicts]}.
    """
    geometry = get_district_geojson(district, city=city, state=state)
    if geometry is None:
        return {
            "error": (
                f"could not resolve a polygon for district={district!r} "
                f"state={state!r} city={city!r}"
            ),
            "collection_id": None,
        }

    catalog = get_catalog()
    date_range = f"{start_date}/{end_date}"
    results = {}

    for name, cfg in LAYERS.items():
        try:
            items = search_collection(
                catalog,
                collection_id=cfg["collection_id"],
                geometry=geometry,
                datetime_range=cfg.get("datetime_range", date_range),
                query=cfg.get("query"),
            )
            results[name] = [item.to_dict() for item in items]
            print(f"[ok] {name}: {len(items)} items from '{cfg['collection_id']}'")
        except Exception as e:
            results[name] = {"error": str(e), "collection_id": cfg["collection_id"]}
            print(f"[fail] {name} ({cfg['collection_id']}): {e}")
        finally:
            # Throttle between searches so the burst of layer queries doesn't
            # provoke connection drops/rate limiting from the STAC endpoint.
            if LAYER_DELAY > 0:
                time.sleep(LAYER_DELAY)

    return results
