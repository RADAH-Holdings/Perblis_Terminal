"""Listing report service (FSD §5.2).

Authenticated hirers report Live listings. Reports never auto-hide a listing;
3 reports in 30 days raise its ``priority_review_flag`` for the Ops queue.
"""

from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from accounts.models import User
from listings.enums import ListingStatus
from listings.errors import ListingNotReportable
from listings.models import Listing, Report

REPORT_WINDOW = timedelta(days=30)
PRIORITY_THRESHOLD = 3


@transaction.atomic
def create_report(*, user: User, listing_id, reason: str, note: str = "") -> Report:
    listing = get_object_or_404(Listing.objects.select_for_update(), id=listing_id)
    # Only Live listings are reportable; otherwise behave as not-found.
    if listing.status != ListingStatus.LIVE:
        raise ListingNotReportable()

    report = Report.objects.create(listing=listing, reporter=user, reason=reason, note=note)

    listing.report_count = listing.reports.count()
    recent = listing.reports.filter(created_at__gte=timezone.now() - REPORT_WINDOW).count()
    if recent >= PRIORITY_THRESHOLD:
        listing.priority_review_flag = True
    listing.save(update_fields=["report_count", "priority_review_flag", "updated_at"])
    return report
