"""Django admin for listings (Ops surface)."""

from __future__ import annotations

from django.contrib import admin

from listings.models import Listing, Report, SpecTemplate, Unit


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


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("listing", "reason", "state", "reporter", "created_at")
    list_filter = ("state", "reason")
    search_fields = ("listing__title", "listing__supplier__email", "reporter__email")
    readonly_fields = ("listing", "reporter", "reason", "note", "created_at", "sibling_listings")

    @admin.display(description="Supplier's other listings")
    def sibling_listings(self, obj: Report) -> str:
        siblings = Listing.objects.filter(supplier=obj.listing.supplier).exclude(id=obj.listing_id)
        return ", ".join(f"{listing.title} ({listing.status})" for listing in siblings) or "—"
