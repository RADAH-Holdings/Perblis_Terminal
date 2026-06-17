"""factory-boy factories for the listings app."""

from __future__ import annotations

import factory

from listings.enums import AssetClass
from listings.models import SpecTemplate


class SpecTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SpecTemplate

    asset_class = AssetClass.PLANT_MACHINERY
    asset_type = factory.Sequence(lambda n: f"Type {n}")
    version = 1
    fields = factory.LazyFunction(
        lambda: {
            "make": {
                "kind": "text",
                "required": True,
                "filterable": False,
                "display_name": "Make",
            }
        }
    )
