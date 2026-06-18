"""search/map acceptance checks (FSD §6, wave-3 §6 checks 1–8 + N+1 guard).

Listings are created Live via the factory (search only reads status=live + a
point + an active supplier); we don't drive the publish gates here.
"""

from __future__ import annotations

import pytest
from django.contrib.gis.db.models.functions import Distance as DistanceFn
from django.contrib.gis.geos import Point
from django.utils import timezone

from listings.enums import ListingStatus
from listings.factories import ListingFactory
from listings.models import Listing
from listings.services.spec_seed import seed_spec_templates
from search.services import search as search_service
from search.services.filters import SearchFilters
from suppliers.factories import YardFactory

pytestmark = pytest.mark.django_db

MAP = "/api/v1/search/map"
APAPA = (3.3792, 6.4433)  # (lng, lat)
LEKKI = (3.4700, 6.4400)


@pytest.fixture
def seeded():
    seed_spec_templates()


def _live(
    supplier,
    yard=None,
    *,
    point=None,
    asset_class="plant_machinery",
    asset_type="Excavator",
    specs=None,
    daily_price=8_000_000,
    title="CAT 320D",
    description="A fine machine",
):
    pt = Point(*(point or APAPA), srid=4326)
    return ListingFactory(
        supplier=supplier,
        yard=yard,
        asset_class=asset_class,
        asset_type=asset_type,
        status=ListingStatus.LIVE,
        point=pt,
        specs=specs or {},
        daily_price=daily_price,
        title=title,
        description=description,
    )


def _radius(api, **params):
    base = {"lat": APAPA[1], "lng": APAPA[0], "radius_km": 50}
    base.update(params)
    return api.get(MAP, base)


# --- Check 1: same supplier + same coords -> one yard pin --------------------


def test_same_supplier_same_coords_one_yard_pin(api, supplier):
    yard = YardFactory(supplier=supplier, point=Point(*APAPA, srid=4326))
    _live(supplier, yard, point=APAPA)
    _live(supplier, yard, point=APAPA)

    body = _radius(api).json()
    assert len(body["yards"]) == 1
    assert body["yards"][0]["listing_count"] == 2
    assert body["listings"] == []


# --- Check 2: two suppliers at one coordinate -> two entries, never merged ---


def test_two_suppliers_one_coordinate_never_merged(api, supplier, supplier2):
    for owner in (supplier, supplier2):
        yard = YardFactory(supplier=owner, point=Point(*APAPA, srid=4326))
        _live(owner, yard, point=APAPA)
        _live(owner, yard, point=APAPA)

    body = _radius(api).json()
    assert len(body["yards"]) == 2
    supplier_ids = {y["supplier"]["id"] for y in body["yards"]}
    assert supplier_ids == {str(supplier.id), str(supplier2.id)}


# --- Check 3: solo -> listings[]; add 2nd Live at the yard -> both in yards[] -


def test_solo_becomes_yard_on_second_listing(api, supplier):
    yard = YardFactory(supplier=supplier, point=Point(*APAPA, srid=4326))
    _live(supplier, yard, point=APAPA)

    body = _radius(api).json()
    assert body["yards"] == []
    assert len(body["listings"]) == 1  # single-listing yard is a solo Asset Pin

    _live(supplier, yard, point=APAPA)
    body = _radius(api).json()
    assert len(body["yards"]) == 1
    assert body["yards"][0]["listing_count"] == 2
    assert body["listings"] == []


# --- Check 4: filtered matching_count; zero-match yard present with count 0 ---


def test_zero_match_yard_still_present_with_count_zero(api, supplier):
    yard = YardFactory(supplier=supplier, point=Point(*APAPA, srid=4326))
    _live(supplier, yard, point=APAPA, asset_class="plant_machinery", asset_type="Excavator")
    _live(supplier, yard, point=APAPA, asset_class="plant_machinery", asset_type="Excavator")

    body = _radius(api, asset_class="trucks_haulage").json()
    assert len(body["yards"]) == 1
    entry = body["yards"][0]
    assert entry["listing_count"] == 2
    assert entry["matching_count"] == 0
    assert entry["listings"] == []


def test_partial_match_count(api, supplier):
    yard = YardFactory(supplier=supplier, point=Point(*APAPA, srid=4326))
    _live(supplier, yard, point=APAPA, daily_price=5_000_000)
    _live(supplier, yard, point=APAPA, daily_price=20_000_000)

    body = _radius(api, price_max=10_000_000).json()
    entry = body["yards"][0]
    assert entry["listing_count"] == 2
    assert entry["matching_count"] == 1
    assert len(entry["listings"]) == 1


# --- Check 5: pause / archive / suspend -> disappears, counts decrement ------


def test_pause_decrements_yard_to_solo(api, supplier):
    yard = YardFactory(supplier=supplier, point=Point(*APAPA, srid=4326))
    a = _live(supplier, yard, point=APAPA)
    _live(supplier, yard, point=APAPA)

    assert len(_radius(api).json()["yards"]) == 1

    Listing.objects.filter(id=a.id).update(status=ListingStatus.PAUSED)
    body = _radius(api).json()
    assert body["yards"] == []  # only 1 Live left -> solo
    assert len(body["listings"]) == 1


def test_suspended_supplier_disappears(api, supplier):
    yard = YardFactory(supplier=supplier, point=Point(*APAPA, srid=4326))
    _live(supplier, yard, point=APAPA)
    _live(supplier, yard, point=APAPA)

    supplier.suspended_at = timezone.now()
    supplier.save(update_fields=["suspended_at"])

    body = _radius(api).json()
    assert body["yards"] == []
    assert body["listings"] == []


# --- Check 6: ★ spec range per class + price filter --------------------------

_STAR_CASES = [
    ("plant_machinery", "Excavator", "operating_weight"),
    ("trucks_haulage", "Tipper / Dump Truck", "payload_capacity"),
    ("warehousing", "Dry Warehouse", "floor_area"),
    ("terminals_yards", "Port Terminal", "container_capacity"),
    ("land_staging", "Laydown", "area"),
]


@pytest.mark.parametrize("asset_class,asset_type,star", _STAR_CASES)
def test_star_spec_range_filter_per_class(api, supplier, seeded, asset_class, asset_type, star):
    _live(supplier, point=APAPA, asset_class=asset_class, asset_type=asset_type, specs={star: 10})
    _live(supplier, point=APAPA, asset_class=asset_class, asset_type=asset_type, specs={star: 30})

    # spec_min=20 -> only the value-30 listing matches.
    body = _radius(api, asset_class=asset_class, spec_min=20).json()
    assert len(body["listings"]) == 1

    # Boundary: spec_min=30 is inclusive.
    body = _radius(api, asset_class=asset_class, spec_min=30).json()
    assert len(body["listings"]) == 1

    # spec_max=10 inclusive -> only the value-10 listing.
    body = _radius(api, asset_class=asset_class, spec_max=10).json()
    assert len(body["listings"]) == 1

    # Range that brackets both.
    body = _radius(api, asset_class=asset_class, spec_min=5, spec_max=40).json()
    assert len(body["listings"]) == 2


def test_price_filter_on_daily_price(api, supplier):
    _live(supplier, point=APAPA, daily_price=5_000_000)
    _live(supplier, point=APAPA, daily_price=15_000_000)

    body = _radius(api, price_min=10_000_000).json()
    assert len(body["listings"]) == 1
    assert body["listings"][0]["price_from"] == 15_000_000


# --- Check 7: q matches title AND description, case-insensitive --------------


def test_q_matches_title_and_description_ci(api, supplier):
    _live(supplier, point=APAPA, title="Komatsu Loader", description="great")
    _live(supplier, point=APAPA, title="Plain", description="a CATERPILLAR engine")
    _live(supplier, point=APAPA, title="Nothing", description="nothing here")

    body = _radius(api, q="komatsu").json()  # title, lowercased
    assert len(body["listings"]) == 1

    body = _radius(api, q="caterpillar").json()  # description
    assert len(body["listings"]) == 1


# --- Check 8: distance matches PostGIS to 0.1 km; ordering stable ------------


def test_distance_matches_postgis_and_orders(api, supplier):
    near = _live(supplier, point=APAPA, title="near")
    far = _live(supplier, point=LEKKI, title="far")

    ref = Point(*APAPA, srid=4326)
    expected = {
        listing.id: round(
            Listing.objects.filter(id=listing.id).annotate(d=DistanceFn("point", ref)).first().d.m
            / 1000,
            1,
        )
        for listing in (near, far)
    }

    listings = _radius(api).json()["listings"]
    by_title = {item["title"]: item for item in listings}
    assert by_title["near"]["distance_km"] == expected[near.id]
    assert by_title["far"]["distance_km"] == expected[far.id]
    # Nearest first (stable order).
    assert [item["title"] for item in listings] == ["near", "far"]


# --- N+1 guard: query count is constant regardless of result size -----------


def test_map_is_n_plus_one_free(supplier, supplier2, django_assert_num_queries):
    for owner in (supplier, supplier2):
        yard = YardFactory(supplier=owner, point=Point(*APAPA, srid=4326))
        for _ in range(4):
            _live(owner, yard, point=APAPA)

    filters = SearchFilters()
    # listings query + photos prefetch = 2, independent of listing/yard count.
    with django_assert_num_queries(2):
        search_service.map_search(lat=APAPA[1], lng=APAPA[0], radius_km=50, filters=filters)
