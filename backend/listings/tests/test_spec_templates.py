"""Spec templates: seed, ★ headline per class, validation, API (Wave 2 §2.3)."""

from __future__ import annotations

import pytest

from listings.enums import AssetClass
from listings.errors import InvalidAssetType, SpecInvalid
from listings.models import SpecTemplate
from listings.services import specs as specs_service
from listings.services.spec_seed import seed_spec_templates

pytestmark = pytest.mark.django_db

# The ★ filterable headline spec per class (doc 05 §7).
HEADLINE = {
    AssetClass.PLANT_MACHINERY: "operating_weight",
    AssetClass.TRUCKS_HAULAGE: "payload_capacity",
    AssetClass.WAREHOUSING: "floor_area",
    AssetClass.TERMINALS_YARDS: "container_capacity",
    AssetClass.LAND_STAGING: "area",
}


def test_seed_is_idempotent():
    first = seed_spec_templates()
    total = SpecTemplate.objects.count()
    assert first == total >= 35
    # Re-running upserts, never duplicates.
    second = seed_spec_templates()
    assert second == first
    assert SpecTemplate.objects.count() == total


def test_one_filterable_headline_per_class():
    seed_spec_templates()
    for asset_class, headline in HEADLINE.items():
        templates = SpecTemplate.objects.filter(asset_class=asset_class)
        assert templates.exists()
        for tpl in templates:
            filterable = [n for n, f in tpl.fields.items() if f.get("filterable")]
            assert filterable == [headline], f"{asset_class}/{tpl.asset_type}: {filterable}"


def test_validate_specs_requires_template():
    with pytest.raises(InvalidAssetType):
        specs_service.validate_specs(asset_class="plant_machinery", asset_type="Nope", specs={})


def test_validate_specs_checks_kinds_and_options():
    seed_spec_templates()
    # Bad select option + non-numeric number.
    with pytest.raises(SpecInvalid) as exc:
        specs_service.validate_specs(
            asset_class="plant_machinery",
            asset_type="Excavator",
            specs={"condition": "Brand New", "year": "old", "make": "CAT"},
        )
    assert set(exc.value.fields or {}) == {"condition", "year"}


def test_validate_specs_required_only_enforced_on_publish():
    seed_spec_templates()
    # Draft create (require=False): missing required fields is OK.
    clean, version = specs_service.validate_specs(
        asset_class="plant_machinery", asset_type="Excavator", specs={"make": "CAT"}
    )
    assert clean == {"make": "CAT"} and version == 1
    # Publish (require=True): missing required surfaces per-field.
    with pytest.raises(SpecInvalid) as exc:
        specs_service.validate_specs(
            asset_class="plant_machinery",
            asset_type="Excavator",
            specs={"make": "CAT"},
            require=True,
        )
    missing = exc.value.fields or {}
    assert "model" in missing and "operator_included" in missing


def test_validate_specs_drops_unknown_fields():
    seed_spec_templates()
    clean, _ = specs_service.validate_specs(
        asset_class="plant_machinery",
        asset_type="Excavator",
        specs={"make": "CAT", "bogus_field": "x"},
    )
    assert "bogus_field" not in clean and clean["make"] == "CAT"


def test_spec_template_endpoint_public(api):
    seed_spec_templates()
    resp = api.get("/api/v1/spec-templates?class=plant_machinery&type=Excavator")
    assert resp.status_code == 200
    body = resp.json()
    assert body["asset_class"] == "plant_machinery"
    assert body["asset_type"] == "Excavator"
    assert body["version"] == 1
    assert "operating_weight" in body["fields"]


def test_spec_template_endpoint_unknown_returns_404(api):
    resp = api.get("/api/v1/spec-templates?class=plant_machinery&type=Nope")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"
