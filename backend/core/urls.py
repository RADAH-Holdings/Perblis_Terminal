"""Core's slice of the /api/v1/ tree.

Empty for Wave 0 — module routers (accounts, suppliers, listings, …) are
added by their respective waves. Existing now so `urls.py` can include it and
the versioned root resolves.
"""

from __future__ import annotations

from django.urls import include, path

app_name = "api"

urlpatterns = [
    path("", include("accounts.urls")),
]
