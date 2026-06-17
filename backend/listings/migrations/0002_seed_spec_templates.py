"""Seed the launch spec templates (doc 05) as a data migration.

Uses the current ``spec_data.build_templates`` to upsert version-1 templates.
Introduce changes via a new ``VERSION`` (and a new migration) rather than
editing published rows — listings stamp the version they were created under.
"""

from __future__ import annotations

from django.db import migrations


def seed(apps, schema_editor):
    SpecTemplate = apps.get_model("listings", "SpecTemplate")
    from listings.spec_data import build_templates

    for tpl in build_templates():
        SpecTemplate.objects.update_or_create(
            asset_class=tpl["asset_class"],
            asset_type=tpl["asset_type"],
            version=tpl["version"],
            defaults={"fields": tpl["fields"]},
        )


def unseed(apps, schema_editor):
    SpecTemplate = apps.get_model("listings", "SpecTemplate")
    from listings.spec_data import build_templates

    for tpl in build_templates():
        SpecTemplate.objects.filter(
            asset_class=tpl["asset_class"],
            asset_type=tpl["asset_type"],
            version=tpl["version"],
        ).delete()


class Migration(migrations.Migration):
    dependencies = [("listings", "0001_initial")]

    operations = [migrations.RunPython(seed, unseed)]
