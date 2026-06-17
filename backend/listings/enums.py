"""Listings enums (System Lexicon doc 02 — exact codes)."""

from __future__ import annotations

from django.db import models


class AssetClass(models.TextChoices):
    PLANT_MACHINERY = "plant_machinery", "Plant & Machinery"
    TRUCKS_HAULAGE = "trucks_haulage", "Trucks & Haulage"
    WAREHOUSING = "warehousing", "Warehousing & Storage"
    TERMINALS_YARDS = "terminals_yards", "Terminals & Container Yards"
    LAND_STAGING = "land_staging", "Land & Staging"


class SpecFieldKind(models.TextChoices):
    NUMBER = "number", "Number"
    TEXT = "text", "Text"
    SELECT = "select", "Select"
    MULTI = "multi", "Multi-select"
    BOOLEAN = "boolean", "Boolean"
