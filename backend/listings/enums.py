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


class ListingStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    LIVE = "live", "Live"
    PAUSED = "paused", "Paused"
    ARCHIVED = "archived", "Archived"
    REMOVED = "removed", "Removed"  # Ops-only


class ListingTier(models.TextChoices):
    BASIC = "basic", "Basic"
    VERIFIED = "verified", "Verified"
    INSPECTED = "inspected", "Inspected"


class ReportReason(models.TextChoices):
    FRAUDULENT = "fraudulent", "Fraudulent"
    INACCURATE = "inaccurate", "Inaccurate"
    INAPPROPRIATE = "inappropriate", "Inappropriate"
    DUPLICATE = "duplicate", "Duplicate"
    UNAVAILABLE = "unavailable", "Unavailable"


class ReportState(models.TextChoices):
    OPEN = "open", "Open"
    DISMISSED = "dismissed", "Dismissed"
    WARNED = "warned", "Warned"
    REMOVED = "removed", "Removed"
