"""Server-authoritative yard aggregation (FSD §6, TSD §3.7).

Partition the viewport's Live listings by yard:

* **Yard entry** — a yard with **≥2** Live listings. Carries ``listing_count``
  (all Live at the yard) and ``matching_count`` (those passing the filters);
  a zero-match yard still appears (``matching_count: 0``) so the client can dim
  it to 40% rather than drop it. Matching summaries ride along so the Yard Sheet
  opens with zero extra round-trips.
* **Solo entry** — a yardless listing, or a single-listing yard. Returned only
  when it matches the filters.

Counts/grouping/distance are all computed here, never on the client.
"""

from __future__ import annotations

from core.money import display
from listings.models import Listing

from .filters import SearchFilters, matches
from .queryset import (
    cover_url,
    distance_km,
    listing_badge,
    point_geojson,
    supplier_summary,
)


def _yard_listing_summary(listing: Listing) -> dict:
    return {
        "id": str(listing.id),
        "title": listing.title,
        "asset_class": listing.asset_class,
        "price_from": listing.daily_price,
        "price_from_display": display(listing.daily_price),
        "photo": cover_url(listing),
        # Availability arrives with Wave 4's engine; stubbed True until then.
        "available": True,
    }


def _solo_entry(listing: Listing) -> dict:
    return {
        "id": str(listing.id),
        "title": listing.title,
        "asset_class": listing.asset_class,
        "point": point_geojson(listing.point),
        "price_from": listing.daily_price,
        "price_from_display": display(listing.daily_price),
        "distance_km": distance_km(listing),
        "photo": cover_url(listing),
        "badge": listing_badge(listing),
    }


def _yard_entry(group: list[Listing], filters: SearchFilters, star: str | None) -> dict:
    yard = group[0].yard
    matching = [listing for listing in group if matches(listing, filters, star)]
    # Price-from reflects the matching listings; for a dimmed zero-match yard it
    # falls back to the yard's cheapest so the pin still carries a figure.
    pool = matching or group
    return {
        "yard_id": str(yard.id),
        "name": yard.name,
        "point": point_geojson(yard.point),
        "supplier": supplier_summary(group[0].supplier),
        "listing_count": len(group),
        "matching_count": len(matching),
        "class_mix": sorted({listing.asset_class for listing in group}),
        "price_from": min(listing.daily_price for listing in pool),
        "price_from_display": display(min(listing.daily_price for listing in pool)),
        "distance_km": distance_km(group[0]),
        "listings": [_yard_listing_summary(listing) for listing in matching],
    }


def aggregate_map(listings: list[Listing], filters: SearchFilters, star: str | None) -> dict:
    """Build the ``{"yards": [...], "listings": [...]}`` map response."""
    by_yard: dict = {}
    solos: list[Listing] = []
    for listing in listings:
        if listing.yard_id is None:
            solos.append(listing)
        else:
            by_yard.setdefault(listing.yard_id, []).append(listing)

    yard_entries: list[dict] = []
    for group in by_yard.values():
        if len(group) >= 2:
            yard_entries.append(_yard_entry(group, filters, star))
        else:
            # A single-listing yard is a solo Asset Pin.
            solos.extend(group)

    solo_entries = [_solo_entry(listing) for listing in solos if matches(listing, filters, star)]

    # Deterministic order by distance (entries already carry distance_km).
    yard_entries.sort(key=lambda entry: (entry["distance_km"] is None, entry["distance_km"]))
    solo_entries.sort(key=lambda entry: (entry["distance_km"] is None, entry["distance_km"]))
    return {"yards": yard_entries, "listings": solo_entries}
