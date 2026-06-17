"""Django admin for listings (Ops surface)."""

from __future__ import annotations

from django.contrib import admin

from listings.models import SpecTemplate


@admin.register(SpecTemplate)
class SpecTemplateAdmin(admin.ModelAdmin):
    list_display = ("asset_class", "asset_type", "version")
    list_filter = ("asset_class",)
    search_fields = ("asset_type",)
