"""The viewport-bounded Live-listing queryset + shaping helpers (TSD §3.7).

The base queryset is deliberately *unfiltered* by the search filters — the
aggregator needs the full set of Live listings in view to compute authoritative
``listing_count`` vs ``matching_count`` (zero-match yards must still surface).

Geo (D-013): viewport uses ``&&`` (bbox overlap) against the GiST index; radius
uses ST_DWithin on geography; distance is ``ST_Distance(point, ref)`` computed
server-side only. Suspended/deleted suppliers are excluded here (their listings
are hidden in lock-step with their storefront — FSD §5.3).
"""

from __future__ import annotations

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D
from django.db.models import QuerySet

from accounts.models import AccountLevel
from core import media
from listings.enums import ListingStatus
from listings.models import Listing
from suppliers.models import SupplierProfile

# Verification badge shown on pins/cards — mirrors the storefront badge (FSD §5.3).
_BADGE = {
    AccountLevel.VERIFIED: "verified",
    AccountLevel.BUSINESS_VERIFIED: "business_verified",
}


def base_live_qs(
    *, ref: Point, bbox: tuple | None = None, radius_km: float | None = None
) -> QuerySet[Listing]:
    """Live listings within the viewport/radius, distance-annotated, N+1-free.

    ``ref`` is the reference point distance is measured from (explicit lat/lng,
    or the bbox centroid). Exactly one of ``bbox`` / ``radius_km`` is set.
    """
    qs = Listing.objects.filter(
        status=ListingStatus.LIVE,
        point__isnull=False,
        supplier__suspended_at__isnull=True,
        supplier__deleted_at__isnull=True,
    )
    if bbox is not None:
        poly = Polygon.from_bbox(bbox)
        poly.srid = 4326
        qs = qs.filter(point__bboverlaps=poly)
    else:
        qs = qs.filter(point__distance_lte=(ref, D(km=radius_km)))
    return (
        qs.annotate(distance=Distance("point", ref))
        .select_related("yard", "supplier", "supplier__supplier_profile")
        .prefetch_related("photos")
        .order_by("distance", "id")
    )


def point_geojson(point) -> dict | None:
    if point is None:
        return None
    return {"type": "Point", "coordinates": [point.x, point.y]}


def cover_url(listing: Listing) -> str:
    """Cover photo URL (the flagged cover, else the first), or "" if none.

    Reads from the prefetched ``photos`` — no extra query per listing.
    """
    photos = list(listing.photos.all())
    cover = next((p for p in photos if p.is_cover), photos[0] if photos else None)
    return media.public_url(cover.r2_key) if cover else ""


def distance_km(listing: Listing) -> float | None:
    """Server-computed distance in km, rounded to 0.1 (never client-estimated)."""
    distance = getattr(listing, "distance", None)
    return round(distance.m / 1000, 1) if distance is not None else None


def supplier_summary(supplier) -> dict:
    """``{id, name, logo, badge}`` for a yard's supplier (no extra query)."""
    try:
        profile = supplier.supplier_profile
    except SupplierProfile.DoesNotExist:
        profile = None
    return {
        "id": str(supplier.id),
        "name": profile.business_name if profile else "",
        "logo": media.public_url(profile.logo_key) if profile and profile.logo_key else "",
        "badge": _BADGE.get(supplier.account_level),
    }


def listing_badge(listing: Listing) -> str | None:
    return _BADGE.get(listing.supplier.account_level)
