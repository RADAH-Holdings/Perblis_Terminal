"""Listings URL routes, mounted under /api/v1/ (namespace api:listings)."""

from __future__ import annotations

from django.urls import path

from listings import views

app_name = "listings"

urlpatterns = [
    path("spec-templates", views.SpecTemplateView.as_view(), name="spec-templates"),
]
