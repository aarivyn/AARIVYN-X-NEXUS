from __future__ import annotations

from typing import Any, Optional

import requests


USER_AGENT = (
    "Mozilla/5.0 (compatible; nexus-mapdata-geojson-fetcher/1.0; "
    "+https://github.com/koshins-com/nexus)"
)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def get_district_geojson(
    district: str,
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: str = "India",
) -> Optional[dict[str, Any]]:
    """Fetch the GeoJSON polygon for a given district/city in India.

    Uses the Nominatim geocoding API to look up the place and returns its
    GeoJSON geometry (polygon/multipolygon).

    Args:
        district: Name of the district, e.g. "Dakshina Kannada".
        city: Optional city name to disambiguate, e.g. "Mangalore".
        state: Optional state/region name, e.g. "Karnataka".
        country: Country to scope the search to. Defaults to "India".

    Returns:
        A GeoJSON geometry dict (Polygon/MultiPolygon), or None if no
        matching polygon was found.
    """
    # Build candidate queries from most to least specific. The state name is
    # the most reliable disambiguator, so it is preferred over the city.
    parts = [district]
    for extra in (state, city):
        if extra and extra.strip():
            parts.append(extra.strip())
    queries: list[str] = [", ".join(parts)]
    if len(parts) > 1:
        queries.append(parts[0])  # fall back to district-only

    headers = {"User-Agent": USER_AGENT}
    session = requests.Session()
    session.headers.update(headers)

    for query in queries:
        params: dict[str, Any] = {
            "q": query,
            "countrycodes": "in",
            "format": "json",
            "polygon_geojson": 1,
            "limit": 20,
        }
        response = session.get(NOMINATIM_URL, params=params, timeout=30)
        response.raise_for_status()

        for item in response.json():
            geom: Optional[dict[str, Any]] = item.get("geojson")
            if geom and geom.get("type") in ("Polygon", "MultiPolygon"):
                return geom

    return None
