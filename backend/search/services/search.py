"""Search orchestration — viewport resolution + map aggregation (TSD §3.7).

The view validates query params and hands typed values here; this module owns
the reference-point resolution and the single DB round-trip into the aggregator.
"""

from __future__ import annotations

from django.contrib.gis.geos import Point

from .aggregate import aggregate_map
from .filters import SearchFilters, star_field
from .queryset import base_live_qs


def resolve_ref(*, bbox: tuple | None, lat: float | None, lng: float | None) -> Point:
    """The point distances are measured from: explicit lat/lng, else bbox centroid."""
    if bbox is not None:
        min_lng, min_lat, max_lng, max_lat = bbox
        return Point((min_lng + max_lng) / 2, (min_lat + max_lat) / 2, srid=4326)
    return Point(lng, lat, srid=4326)


def map_search(
    *,
    bbox: tuple | None = None,
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float | None = None,
    filters: SearchFilters,
) -> dict:
    """Server-aggregated yards + solo listings for a viewport/radius."""
    ref = resolve_ref(bbox=bbox, lat=lat, lng=lng)
    star = star_field(filters.asset_class)
    listings = list(base_live_qs(ref=ref, bbox=bbox, radius_km=radius_km))
    return aggregate_map(listings, filters, star)
