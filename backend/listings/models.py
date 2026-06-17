"""Listings models — spec templates first (Wave 2 §2.3, TSD §3.3).

A ``SpecTemplate`` is server-side configuration (versioned) describing the
``specs`` a listing of a given ``asset_class`` + ``asset_type`` carries. Field
definitions follow doc 05 (the normative source); the launch set is seeded by
``seed_spec_templates``.
"""

from __future__ import annotations

from django.db import models

from core.models import BaseModel
from listings.enums import AssetClass


class SpecTemplate(BaseModel):
    asset_class = models.CharField(max_length=32, choices=AssetClass.choices)
    asset_type = models.CharField(max_length=100)
    version = models.PositiveIntegerField(default=1)
    # field_name -> {kind, unit?, required, options?, filterable, display_name}
    fields = models.JSONField(default=dict)

    class Meta:
        db_table = "spec_templates"
        constraints = [
            models.UniqueConstraint(
                fields=["asset_class", "asset_type", "version"],
                name="uniq_spec_template_class_type_version",
            )
        ]
        indexes = [models.Index(fields=["asset_class", "asset_type"])]

    def __str__(self) -> str:
        return f"{self.asset_class}/{self.asset_type} v{self.version}"
