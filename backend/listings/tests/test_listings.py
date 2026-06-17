"""Listings CRUD (Wave 2 §2.4, FSD §5.2)."""

from __future__ import annotations

import pytest
from django.contrib.gis.geos import Point

from listings.enums import ListingStatus
from listings.models import Listing
from listings.services import listings as listings_service
from listings.services.spec_seed import seed_spec_templates
from suppliers.services import yards as yards_service

pytestmark = pytest.mark.django_db

LIST = "/api/v1/listings"


@pytest.fixture
def seeded():
    seed_spec_templates()


def _payload(**over):
    body = {
        "asset_class": "plant_machinery",
        "asset_type": "Excavator",
        "title": "CAT 320D Excavator",
        "description": "Well-maintained 2020 CAT excavator, ideal for construction sites.",
        "specs": {"make": "Caterpillar", "model": "320D", "operating_weight": 32.5},
        "daily_price": 8_000_000,
        "unit_count": 2,
        "point": {"type": "Point", "coordinates": [3.3792, 6.4433]},
    }
    body.update(over)
    return body


def test_create_listing_draft_with_specs_stamps_version(auth, supplier, seeded):
    resp = auth(supplier).post(LIST, _payload(), format="json")
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "draft"
    assert body["tier"] == "basic"
    assert body["spec_template_version"] == 1
    assert body["daily_price_display"] == "₦80,000"
    assert body["specs"]["operating_weight"] == 32.5
    # completeness_score is stored but not user-visible.
    assert "completeness_score" not in body


def test_create_listing_rejects_bad_spec(auth, supplier, seeded):
    resp = auth(supplier).post(LIST, _payload(specs={"year": "not-a-number"}), format="json")
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "spec_invalid"
    assert "year" in body["error"]["fields"]


def test_create_listing_unknown_asset_type(auth, supplier, seeded):
    resp = auth(supplier).post(LIST, _payload(asset_type="Spaceship"), format="json")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_asset_type"


def test_create_listing_short_description_rejected(auth, supplier, seeded):
    resp = auth(supplier).post(LIST, _payload(description="too short"), format="json")
    assert resp.status_code == 400


def test_hirer_cannot_create_listing(auth, hirer, seeded):
    resp = auth(hirer).post(LIST, _payload(), format="json")
    assert resp.status_code == 403


def test_yard_chip_denormalises_point(supplier, seeded):
    yard = yards_service.create_yard(user=supplier, name="Apapa", point=Point(3.1, 6.2, srid=4326))
    listing, _ = listings_service.create_listing(
        user=supplier,
        asset_class="plant_machinery",
        asset_type="Excavator",
        title="X",
        description="A long enough description for the listing body here.",
        specs={},
        daily_price=5_000_000,
        yard_id=yard.id,
    )
    assert (round(listing.point.x, 4), round(listing.point.y, 4)) == (3.1, 6.2)


def test_moving_yard_updates_point(supplier, seeded):
    y1 = yards_service.create_yard(user=supplier, name="A", point=Point(3.1, 6.2, srid=4326))
    y2 = yards_service.create_yard(user=supplier, name="B", point=Point(7.4, 9.1, srid=4326))
    listing, _ = listings_service.create_listing(
        user=supplier,
        asset_class="plant_machinery",
        asset_type="Excavator",
        title="X",
        description="A long enough description for the listing body here.",
        specs={},
        daily_price=5_000_000,
        yard_id=y1.id,
    )
    updated = listings_service.update_listing(user=supplier, listing_id=listing.id, yard_id=y2.id)
    assert (round(updated.point.x, 4), round(updated.point.y, 4)) == (7.4, 9.1)


def test_yard_with_listings_cannot_be_deleted(auth, supplier, seeded):
    yard = yards_service.create_yard(user=supplier, name="Apapa", point=Point(3.1, 6.2, srid=4326))
    listings_service.create_listing(
        user=supplier,
        asset_class="plant_machinery",
        asset_type="Excavator",
        title="X",
        description="A long enough description for the listing body here.",
        specs={},
        daily_price=5_000_000,
        yard_id=yard.id,
    )
    resp = auth(supplier).delete(f"/api/v1/yards/{yard.id}")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "yard_has_listings"


def test_draft_detail_is_owner_only(auth, supplier, supplier2, seeded):
    listing, _ = listings_service.create_listing(
        user=supplier,
        asset_class="plant_machinery",
        asset_type="Excavator",
        title="X",
        description="A long enough description for the listing body here.",
        specs={},
        daily_price=5_000_000,
        point=Point(3.1, 6.2, srid=4326),
    )
    url = f"{LIST}/{listing.id}"
    # Owner sees the draft.
    assert auth(supplier).get(url).status_code == 200
    # Another supplier does not (404, not 403 — no existence leak).
    assert auth(supplier2).get(url).status_code == 404


def test_live_listing_detail_is_public(api, supplier, seeded):
    listing, _ = listings_service.create_listing(
        user=supplier,
        asset_class="plant_machinery",
        asset_type="Excavator",
        title="X",
        description="A long enough description for the listing body here.",
        specs={},
        daily_price=5_000_000,
        point=Point(3.1, 6.2, srid=4326),
    )
    Listing.objects.filter(id=listing.id).update(status=ListingStatus.LIVE)
    resp = api.get(f"{LIST}/{listing.id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "live"


def test_live_edit_price_persists_without_cascade(auth, supplier, seeded):
    # Editing a Live listing's price is allowed; hire-term locking arrives in
    # Wave 4 (no hires exist yet, so nothing cascades).
    listing, _ = listings_service.create_listing(
        user=supplier,
        asset_class="plant_machinery",
        asset_type="Excavator",
        title="X",
        description="A long enough description for the listing body here.",
        specs={},
        daily_price=5_000_000,
        point=Point(3.1, 6.2, srid=4326),
    )
    Listing.objects.filter(id=listing.id).update(status=ListingStatus.LIVE)
    resp = auth(supplier).patch(f"{LIST}/{listing.id}", {"daily_price": 9_000_000}, format="json")
    assert resp.status_code == 200
    assert resp.json()["daily_price"] == 9_000_000


def test_units_created_from_labels(supplier, seeded):
    listing, _ = listings_service.create_listing(
        user=supplier,
        asset_class="plant_machinery",
        asset_type="Excavator",
        title="X",
        description="A long enough description for the listing body here.",
        specs={},
        daily_price=5_000_000,
        point=Point(3.1, 6.2, srid=4326),
        unit_labels=["Tipper #1", "Tipper #2"],
    )
    assert listing.units.count() == 2
