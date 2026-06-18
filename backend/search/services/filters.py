"""Search filters (FSD §6, TSD §3.7).

One predicate, two evaluations that MUST agree:

* ``matches`` — a Python predicate over an in-memory ``Listing``. Used by the
  map aggregator to compute ``matching_count`` against the *unfiltered*
  viewport set (so zero-match yards still surface, dimmed).
* ``apply_filters`` — the same logic pushed into SQL, for the paginated
  ``search/list`` flat queryset.

The ★ spec filter (``spec_min``/``spec_max``) acts on the single filterable
headline field of the active ``asset_class`` (doc 05 §7 — one per class), so it
only applies when a class is selected.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeGuard

from django.db.models import FloatField, Q, QuerySet
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast

from listings.models import Listing, SpecTemplate


@dataclass(frozen=True)
class SearchFilters:
    asset_class: str | None = None
    q: str | None = None
    price_min: int | None = None  # daily price, kobo
    price_max: int | None = None  # daily price, kobo
    spec_min: float | None = None  # ★ field for the active class
    spec_max: float | None = None

    @property
    def has_spec_range(self) -> bool:
        return self.spec_min is not None or self.spec_max is not None


def star_field(asset_class: str | None) -> str | None:
    """The single ★ filterable headline field for a class (doc 05 §7).

    Resolved from any seeded template of the class — the field is class-common,
    so every template in the class shares it (operating_weight, payload_capacity,
    floor_area, container_capacity, area).
    """
    if not asset_class:
        return None
    template = SpecTemplate.objects.filter(asset_class=asset_class).first()
    if template is None:
        return None
    for name, fdef in template.fields.items():
        if fdef.get("filterable"):
            return name
    return None


def _is_number(value: object) -> TypeGuard[float]:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def matches(listing: Listing, filters: SearchFilters, star: str | None) -> bool:
    """Whether ``listing`` passes the active filters (mirror of ``apply_filters``)."""
    if filters.asset_class and listing.asset_class != filters.asset_class:
        return False
    if filters.q:
        needle = filters.q.lower()
        if (
            needle not in listing.title.lower()
            and needle not in (listing.description or "").lower()
        ):
            return False
    if filters.price_min is not None and listing.daily_price < filters.price_min:
        return False
    if filters.price_max is not None and listing.daily_price > filters.price_max:
        return False
    if filters.has_spec_range:
        if not star:
            return False
        value = listing.specs.get(star) if isinstance(listing.specs, dict) else None
        if not _is_number(value):
            return False
        if filters.spec_min is not None and value < filters.spec_min:
            return False
        if filters.spec_max is not None and value > filters.spec_max:
            return False
    return True


def apply_filters(
    qs: QuerySet[Listing], filters: SearchFilters, star: str | None
) -> QuerySet[Listing]:
    """Push the filter predicate into SQL (used by the paginated list view)."""
    if filters.asset_class:
        qs = qs.filter(asset_class=filters.asset_class)
    if filters.q:
        qs = qs.filter(Q(title__icontains=filters.q) | Q(description__icontains=filters.q))
    if filters.price_min is not None:
        qs = qs.filter(daily_price__gte=filters.price_min)
    if filters.price_max is not None:
        qs = qs.filter(daily_price__lte=filters.price_max)
    if filters.has_spec_range:
        if not star:
            return qs.none()
        # Cast the JSONB text value to float so range comparison is numeric, not
        # lexical. A missing key casts to NULL and is excluded — matching the
        # Python predicate's behaviour.
        qs = qs.annotate(_star=Cast(KeyTextTransform(star, "specs"), FloatField()))
        if filters.spec_min is not None:
            qs = qs.filter(_star__gte=filters.spec_min)
        if filters.spec_max is not None:
            qs = qs.filter(_star__lte=filters.spec_max)
    return qs
