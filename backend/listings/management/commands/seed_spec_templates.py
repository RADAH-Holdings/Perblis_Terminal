"""Seed/refresh the launch spec templates (doc 05). Idempotent."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from listings.services.spec_seed import seed_spec_templates


class Command(BaseCommand):
    help = "Seed the launch asset spec templates (idempotent upsert from doc 05)."

    def handle(self, *args, **options):
        count = seed_spec_templates()
        self.stdout.write(self.style.SUCCESS(f"Seeded {count} spec templates."))
