"""Address → point geocoding via the LocationIQ proxy (FSD §5.2 location step).

Best-effort: when ``LOCATIONIQ_KEY`` is absent (dev/CI) or the lookup fails,
returns None and the caller falls back to a yard pin or explicit pin-drop. The
publish gate blocks going Live without a resolved location either way.
"""

from __future__ import annotations

import httpx
import structlog
from django.conf import settings
from django.contrib.gis.geos import Point

logger = structlog.get_logger(__name__)

_SEARCH_URL = "https://us1.locationiq.com/v1/search"


def geocode(address_text: str, city: str) -> Point | None:
    if not settings.LOCATIONIQ_KEY:
        return None
    query = ", ".join(p for p in [address_text, city, "Nigeria"] if p)
    if not query:
        return None
    try:
        resp = httpx.get(
            _SEARCH_URL,
            params={"key": settings.LOCATIONIQ_KEY, "q": query, "format": "json", "limit": 1},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        if data:
            return Point(float(data[0]["lon"]), float(data[0]["lat"]), srid=4326)
    except Exception:  # noqa: BLE001 — geocoding is best-effort; never crash the request
        logger.warning("geocoding.failed", query=query)
    return None
