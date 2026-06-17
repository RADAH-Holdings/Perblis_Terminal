"""Django admin for listings (Ops surface)."""

from __future__ import annotations

from django.contrib import admin

from listings.models import Listing, SpecTemplate, Unit


@admin.register(SpecTemplate)
class SpecTemplateAdmin(admin.ModelAdmin):
    list_display = ("asset_class", "asset_type", "version")
    list_filter = ("asset_class",)
    search_fields = ("asset_type",)


class UnitInline(admin.TabularInline):
    model = Unit
    extra = 0


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "supplier",
        "asset_class",
        "asset_type",
        "status",
        "tier",
        "created_at",
    )
    list_filter = ("status", "tier", "asset_class")
    search_fields = ("title", "supplier__email", "asset_type")
    readonly_fields = ("completeness_score", "report_count", "priority_review_flag")
    inlines = [UnitInline]
