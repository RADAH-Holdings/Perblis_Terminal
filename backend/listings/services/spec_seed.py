"""Seed the launch spec templates from doc 05 (idempotent).

Used by both the ``seed_spec_templates`` management command and the data
migration. Upserts on (asset_class, asset_type, version) so re-runs are safe;
bump ``spec_data.VERSION`` to introduce a new template version rather than
mutating a published one (listings stamp the version they were created under).
"""

from __future__ import annotations

from listings.models import SpecTemplate
from listings.spec_data import build_templates


def seed_spec_templates() -> int:
    """Create/update every launch template. Returns the number processed."""
    count = 0
    for tpl in build_templates():
        SpecTemplate.objects.update_or_create(
            asset_class=tpl["asset_class"],
            asset_type=tpl["asset_type"],
            version=tpl["version"],
            defaults={"fields": tpl["fields"]},
        )
        count += 1
    return count
