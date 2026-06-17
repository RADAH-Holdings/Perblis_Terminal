"""Listings URL routes, mounted under /api/v1/ (namespace api:listings)."""

from __future__ import annotations

from django.urls import path

from listings import views

app_name = "listings"

urlpatterns = [
    path("spec-templates", views.SpecTemplateView.as_view(), name="spec-templates"),
    path("listings", views.ListingListCreateView.as_view(), name="listings"),
    path("listings/<uuid:listing_id>", views.ListingDetailView.as_view(), name="listing-detail"),
]
