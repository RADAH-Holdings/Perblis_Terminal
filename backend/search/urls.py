"""Search app routes (mounted under /api/v1/ by core.urls)."""

from __future__ import annotations

from django.urls import path

from search import views

app_name = "search"

urlpatterns = [
    path("search/map", views.SearchMapView.as_view(), name="search-map"),
]
