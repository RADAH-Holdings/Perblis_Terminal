# TERMINAL — WAVE 05: OWNER WEB APP ENDPOINTS (Part 2 of 2)
> Agent task file. Execute every instruction in order. Do not skip steps.
> Part 1 must be fully complete before starting Part 2.
> Do not proceed to Wave 06 (Frontend) until the Definition of Done is complete.

---

## Context

Part 2 builds all the new endpoints inside the `owner` app — the dashboard summary, booking calendar, analytics, listing stats, duplicate, bulk actions, and business settings endpoints. All new endpoints live under `/api/v1/owner/`.

---

## Step 1: Create owner app serializers

**Create `owner/serializers.py`:**

```python
from decimal import Decimal
from rest_framework import serializers
from accounts.models import OwnerProfile


class OwnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnerProfile
        fields = [
            'id',
            'business_name', 'business_description', 'business_logo',
            'bank_name', 'bank_account_number', 'bank_account_name',
            'notify_new_booking_request', 'notify_booking_confirmed',
            'notify_new_message', 'notify_booking_cancelled',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UpdateBusinessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnerProfile
        fields = ['business_name', 'business_description', 'business_logo']


class UpdateBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnerProfile
        fields = ['bank_name', 'bank_account_number', 'bank_account_name']

    def validate_bank_account_number(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError('Account number must contain only digits.')
        if value and len(value) != 10:
            raise serializers.ValidationError('Account number must be exactly 10 digits.')
        return value


class UpdateNotificationPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnerProfile
        fields = [
            'notify_new_booking_request',
            'notify_booking_confirmed',
            'notify_new_message',
            'notify_booking_cancelled',
        ]


class DashboardPendingBookingSerializer(serializers.Serializer):
    """Lightweight booking for dashboard pending requests list."""
    id = serializers.UUIDField()
    listing_title = serializers.SerializerMethodField()
    listing_id = serializers.SerializerMethodField()
    renter_name = serializers.SerializerMethodField()
    renter_photo = serializers.SerializerMethodField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    gross_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    created_at = serializers.DateTimeField()

    def get_listing_title(self, obj):
        return obj.listing.title

    def get_listing_id(self, obj):
        return str(obj.listing.id)

    def get_renter_name(self, obj):
        return obj.renter.full_name

    def get_renter_photo(self, obj):
        request = self.context.get('request')
        if obj.renter.profile_photo and request:
            return request.build_absolute_uri(obj.renter.profile_photo.url)
        return None


class DashboardRecentThreadSerializer(serializers.Serializer):
    """Lightweight thread for dashboard recent messages list."""
    id = serializers.UUIDField()
    other_participant_name = serializers.SerializerMethodField()
    other_participant_photo = serializers.SerializerMethodField()
    listing_title = serializers.SerializerMethodField()
    last_message_body = serializers.SerializerMethodField()
    last_message_time = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    def get_other_participant_name(self, obj):
        user = self.context.get('request').user
        other = obj.get_other_participant(user)
        return other.full_name if other else None

    def get_other_participant_photo(self, obj):
        request = self.context.get('request')
        user = request.user
        other = obj.get_other_participant(user)
        if other and other.profile_photo:
            return request.build_absolute_uri(other.profile_photo.url)
        return None

    def get_listing_title(self, obj):
        return obj.listing.title if obj.listing else None

    def get_last_message_body(self, obj):
        last = obj.messages.last()
        return last.body[:100] if last else None

    def get_last_message_time(self, obj):
        last = obj.messages.last()
        return last.created_at if last else None

    def get_unread_count(self, obj):
        user = self.context.get('request').user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()


class CalendarBookingSerializer(serializers.Serializer):
    """Booking block for calendar view."""
    id = serializers.UUIDField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    status = serializers.CharField()
    renter_name = serializers.SerializerMethodField()
    gross_amount = serializers.DecimalField(max_digits=15, decimal_places=2)

    def get_renter_name(self, obj):
        return obj.renter.full_name


class CalendarListingSerializer(serializers.Serializer):
    """Listing row for calendar view, with its bookings for the period."""
    id = serializers.UUIDField()
    title = serializers.CharField()
    resource_type = serializers.CharField()
    bookings = serializers.SerializerMethodField()

    def get_bookings(self, obj):
        bookings = self.context.get('bookings_by_listing', {}).get(str(obj.id), [])
        return CalendarBookingSerializer(bookings, many=True).data


class RevenueByListingSerializer(serializers.Serializer):
    listing_id = serializers.UUIDField()
    listing_title = serializers.CharField()
    resource_type = serializers.CharField()
    gross_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    commission_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    payout_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    booking_count = serializers.IntegerField()


class MonthlyTrendSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    month_label = serializers.CharField()
    gross_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    booking_count = serializers.IntegerField()


class ListingPerformanceSerializer(serializers.Serializer):
    listing_id = serializers.UUIDField()
    listing_title = serializers.CharField()
    resource_type = serializers.CharField()
    status = serializers.CharField()
    views = serializers.IntegerField()
    inquiry_count = serializers.IntegerField()
    booking_request_count = serializers.IntegerField()
    confirmed_booking_count = serializers.IntegerField()
    occupancy_rate = serializers.FloatField()
    conversion_rate = serializers.FloatField()
```

---

## Step 2: Create owner app views

**Create `owner/views.py`:**

```python
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum, Count, Q, Avg
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import OwnerProfile
from bookings.models import Booking, BookingStatus
from listings.models import Listing
from messaging.models import Thread, Message
from core.permissions import IsOwnerRole

from .serializers import (
    OwnerProfileSerializer,
    UpdateBusinessProfileSerializer,
    UpdateBankAccountSerializer,
    UpdateNotificationPreferencesSerializer,
    DashboardPendingBookingSerializer,
    DashboardRecentThreadSerializer,
    CalendarListingSerializer,
    RevenueByListingSerializer,
    MonthlyTrendSerializer,
    ListingPerformanceSerializer,
)


def get_or_create_owner_profile(user):
    """Helper to get or create an owner profile for the user."""
    profile, _ = OwnerProfile.objects.get_or_create(user=user)
    return profile


# ─────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOwnerRole])
def owner_dashboard(request):
    """
    Single endpoint for all owner dashboard headline stats.
    Returns stats, pending requests (top 5), and recent messages (top 5).
    """
    user = request.user
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Headline counts
    total_listings = Listing.objects.filter(owner=user).count()
    active_listings = Listing.objects.filter(owner=user, status='active').count()

    pending_requests = Booking.objects.filter(
        owner=user,
        status=BookingStatus.PENDING,
    ).count()

    active_bookings = Booking.objects.filter(
        owner=user,
        status__in=[BookingStatus.CONFIRMED, BookingStatus.ACTIVE],
    ).count()

    unread_messages = Message.objects.filter(
        thread__participants=user,
        is_read=False,
    ).exclude(sender=user).count()

    # Revenue this month (confirmed + active + completed)
    revenue_this_month = Booking.objects.filter(
        owner=user,
        status__in=[BookingStatus.CONFIRMED, BookingStatus.ACTIVE, BookingStatus.COMPLETED],
        created_at__gte=month_start,
    ).aggregate(total=Sum('owner_payout_amount'))['total'] or Decimal('0.00')

    # Top 5 pending booking requests
    pending_bookings_qs = Booking.objects.filter(
        owner=user,
        status=BookingStatus.PENDING,
    ).select_related('renter', 'listing').order_by('created_at')[:5]

    # Top 5 recent threads
    recent_threads_qs = Thread.objects.filter(
        participants=user,
    ).prefetch_related('participants', 'messages').select_related(
        'listing', 'booking'
    ).order_by('-updated_at')[:5]

    pending_serializer = DashboardPendingBookingSerializer(
        pending_bookings_qs,
        many=True,
        context={'request': request},
    )

    threads_serializer = DashboardRecentThreadSerializer(
        recent_threads_qs,
        many=True,
        context={'request': request},
    )

    return Response({
        'success': True,
        'data': {
            'stats': {
                'total_listings': total_listings,
                'active_listings': active_listings,
                'pending_booking_requests': pending_requests,
                'active_bookings': active_bookings,
                'unread_messages': unread_messages,
                'revenue_this_month': str(revenue_this_month),
            },
            'pending_requests': pending_serializer.data,
            'recent_messages': threads_serializer.data,
        },
    })


# ─────────────────────────────────────────────────────────────
# BOOKING CALENDAR
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOwnerRole])
def booking_calendar(request):
    """
    Returns all owner listings with their bookings for a given date range.
    Used to render the calendar grid in the web app.

    Query params:
        start_date (required): YYYY-MM-DD
        end_date (required): YYYY-MM-DD
    """
    start_date_str = request.query_params.get('start_date')
    end_date_str = request.query_params.get('end_date')

    if not start_date_str or not end_date_str:
        return Response(
            {'success': False, 'errors': 'start_date and end_date are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from datetime import datetime
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response(
            {'success': False, 'errors': 'Dates must be in YYYY-MM-DD format.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if end_date < start_date:
        return Response(
            {'success': False, 'errors': 'end_date must be on or after start_date.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Max range: 90 days to prevent expensive queries
    if (end_date - start_date).days > 90:
        return Response(
            {'success': False, 'errors': 'Date range cannot exceed 90 days.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = request.user

    # Get all owner listings that are active or paused
    listings = Listing.objects.filter(
        owner=user,
        status__in=['active', 'paused'],
    ).order_by('resource_type', 'title')

    # Get all bookings for these listings within the date range
    # A booking overlaps the range if: booking.start_date < range.end AND booking.end_date > range.start
    bookings = Booking.objects.filter(
        listing__in=listings,
        status__in=[
            BookingStatus.PENDING,
            BookingStatus.CONFIRMED,
            BookingStatus.ACTIVE,
        ],
        start_date__lt=end_date,
        end_date__gt=start_date,
    ).select_related('renter', 'listing').order_by('start_date')

    # Group bookings by listing ID
    bookings_by_listing = {}
    for booking in bookings:
        key = str(booking.listing.id)
        if key not in bookings_by_listing:
            bookings_by_listing[key] = []
        bookings_by_listing[key].append(booking)

    serializer = CalendarListingSerializer(
        listings,
        many=True,
        context={
            'request': request,
            'bookings_by_listing': bookings_by_listing,
        },
    )

    return Response({
        'success': True,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'listing_count': listings.count(),
        'data': serializer.data,
    })


# ─────────────────────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOwnerRole])
def analytics_revenue(request):
    """
    Revenue analytics for the owner.

    Query params:
        period: 'month' (default) | 'quarter' | 'year' | 'all'
        year: YYYY (used with period=month or period=quarter)
        month: 1-12 (used with period=month only)
    """
    user = request.user
    period = request.query_params.get('period', 'month')
    now = timezone.now()

    # Determine date range based on period
    if period == 'month':
        try:
            year = int(request.query_params.get('year', now.year))
            month = int(request.query_params.get('month', now.month))
        except ValueError:
            return Response(
                {'success': False, 'errors': 'year and month must be integers.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from datetime import datetime
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        range_start = date(year, month, 1)
        range_end = date(year, month, last_day)
        period_label = f"{datetime(year, month, 1).strftime('%B %Y')}"

    elif period == 'quarter':
        year = int(request.query_params.get('year', now.year))
        quarter = (now.month - 1) // 3 + 1
        quarter_start_month = (quarter - 1) * 3 + 1
        range_start = date(year, quarter_start_month, 1)
        import calendar
        last_month = quarter_start_month + 2
        last_day = calendar.monthrange(year, last_month)[1]
        range_end = date(year, last_month, last_day)
        period_label = f"Q{quarter} {year}"

    elif period == 'year':
        year = int(request.query_params.get('year', now.year))
        range_start = date(year, 1, 1)
        range_end = date(year, 12, 31)
        period_label = str(year)

    else:  # 'all'
        range_start = date(2020, 1, 1)
        range_end = date(2100, 1, 1)
        period_label = 'All Time'

    # Base queryset: owner bookings in range, non-cancelled
    base_qs = Booking.objects.filter(
        owner=user,
        status__in=[
            BookingStatus.CONFIRMED,
            BookingStatus.ACTIVE,
            BookingStatus.COMPLETED,
        ],
        start_date__gte=range_start,
        start_date__lte=range_end,
    )

    # Aggregate totals
    totals = base_qs.aggregate(
        gross_total=Sum('gross_amount'),
        commission_total=Sum('commission_amount'),
        payout_total=Sum('owner_payout_amount'),
        booking_count=Count('id'),
    )

    gross_total = totals['gross_total'] or Decimal('0.00')
    commission_total = totals['commission_total'] or Decimal('0.00')
    payout_total = totals['payout_total'] or Decimal('0.00')
    booking_count = totals['booking_count'] or 0
    avg_booking_value = (
        (gross_total / booking_count).quantize(Decimal('0.01'))
        if booking_count > 0 else Decimal('0.00')
    )

    # Revenue by listing
    by_listing_qs = base_qs.values(
        'listing__id', 'listing__title', 'listing__resource_type'
    ).annotate(
        gross=Sum('gross_amount'),
        commission=Sum('commission_amount'),
        payout=Sum('owner_payout_amount'),
        count=Count('id'),
    ).order_by('-gross')

    by_listing = [
        {
            'listing_id': str(row['listing__id']),
            'listing_title': row['listing__title'],
            'resource_type': row['listing__resource_type'],
            'gross_total': row['gross'] or Decimal('0.00'),
            'commission_total': row['commission'] or Decimal('0.00'),
            'payout_total': row['payout'] or Decimal('0.00'),
            'booking_count': row['count'],
        }
        for row in by_listing_qs
    ]

    # Monthly trend — always last 12 months regardless of period filter
    twelve_months_ago = (now - timedelta(days=365)).date()
    monthly_qs = Booking.objects.filter(
        owner=user,
        status__in=[BookingStatus.CONFIRMED, BookingStatus.ACTIVE, BookingStatus.COMPLETED],
        start_date__gte=twelve_months_ago,
    ).annotate(
        month=TruncMonth('start_date')
    ).values('month').annotate(
        gross=Sum('gross_amount'),
        count=Count('id'),
    ).order_by('month')

    import calendar
    monthly_trend = [
        {
            'year': row['month'].year,
            'month': row['month'].month,
            'month_label': row['month'].strftime('%b %Y'),
            'gross_total': row['gross'] or Decimal('0.00'),
            'booking_count': row['count'],
        }
        for row in monthly_qs
    ]

    return Response({
        'success': True,
        'period': period,
        'period_label': period_label,
        'data': {
            'gross_total': str(gross_total),
            'commission_total': str(commission_total),
            'payout_total': str(payout_total),
            'booking_count': booking_count,
            'avg_booking_value': str(avg_booking_value),
            'by_listing': RevenueByListingSerializer(by_listing, many=True).data,
            'monthly_trend': MonthlyTrendSerializer(monthly_trend, many=True).data,
        },
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOwnerRole])
def analytics_performance(request):
    """
    Listing performance analytics for the owner.

    Query params:
        period: 'last_30_days' (default) | 'last_90_days' | 'last_year' | 'all'
    """
    user = request.user
    period = request.query_params.get('period', 'last_30_days')
    now = timezone.now()

    if period == 'last_30_days':
        since = (now - timedelta(days=30)).date()
        period_label = 'Last 30 days'
    elif period == 'last_90_days':
        since = (now - timedelta(days=90)).date()
        period_label = 'Last 90 days'
    elif period == 'last_year':
        since = (now - timedelta(days=365)).date()
        period_label = 'Last 12 months'
    else:
        since = date(2020, 1, 1)
        period_label = 'All time'

    listings = Listing.objects.filter(owner=user).order_by('-created_at')

    performance_data = []
    for listing in listings:
        # Booking stats in period
        period_bookings = Booking.objects.filter(
            listing=listing,
            created_at__date__gte=since,
        )
        total_requests = period_bookings.count()
        confirmed = period_bookings.filter(
            status__in=[BookingStatus.CONFIRMED, BookingStatus.ACTIVE, BookingStatus.COMPLETED]
        ).count()

        # Inquiry count (non-booking threads for this listing)
        inquiry_count = Thread.objects.filter(
            listing=listing,
            booking__isnull=True,
            created_at__date__gte=since,
        ).count()

        # Conversion rate: confirmed / total requests
        conversion_rate = (
            round((confirmed / total_requests) * 100, 1)
            if total_requests > 0 else 0.0
        )

        # Occupancy rate: booked days / total days in period
        period_days = (now.date() - since).days or 1
        booked_bookings = Booking.objects.filter(
            listing=listing,
            status__in=[BookingStatus.CONFIRMED, BookingStatus.ACTIVE, BookingStatus.COMPLETED],
            start_date__gte=since,
        )
        booked_days = sum(
            min((b.end_date - b.start_date).days, period_days)
            for b in booked_bookings
        )
        occupancy_rate = round(min((booked_days / period_days) * 100, 100), 1)

        performance_data.append({
            'listing_id': listing.id,
            'listing_title': listing.title,
            'resource_type': listing.resource_type,
            'status': listing.status,
            'views': listing.view_count,
            'inquiry_count': inquiry_count,
            'booking_request_count': total_requests,
            'confirmed_booking_count': confirmed,
            'occupancy_rate': occupancy_rate,
            'conversion_rate': conversion_rate,
        })

    # Sort by views descending
    performance_data.sort(key=lambda x: x['views'], reverse=True)

    # Overall response rate (% of requests responded to within 24h — approximated for MVP)
    # MVP: we don't track response time precisely, so return total confirmed / total requests
    total_all_requests = sum(p['booking_request_count'] for p in performance_data)
    total_all_confirmed = sum(p['confirmed_booking_count'] for p in performance_data)
    overall_conversion = (
        round((total_all_confirmed / total_all_requests) * 100, 1)
        if total_all_requests > 0 else 0.0
    )

    return Response({
        'success': True,
        'period': period,
        'period_label': period_label,
        'data': {
            'total_views': sum(p['views'] for p in performance_data),
            'total_inquiries': sum(p['inquiry_count'] for p in performance_data),
            'total_booking_requests': total_all_requests,
            'total_confirmed': total_all_confirmed,
            'overall_conversion_rate': overall_conversion,
            'by_listing': ListingPerformanceSerializer(performance_data, many=True).data,
        },
    })


# ─────────────────────────────────────────────────────────────
# LISTING: STATS, DUPLICATE, BULK
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOwnerRole])
def listing_stats(request, listing_id):
    """
    Per-listing performance stats.
    Owner only — cannot view stats for another owner's listing.
    """
    listing = get_object_or_404(Listing, id=listing_id, owner=request.user)

    all_bookings = Booking.objects.filter(listing=listing)
    confirmed = all_bookings.filter(
        status__in=[BookingStatus.CONFIRMED, BookingStatus.ACTIVE, BookingStatus.COMPLETED]
    )
    total_requests = all_bookings.count()
    confirmed_count = confirmed.count()

    inquiry_count = Thread.objects.filter(
        listing=listing,
        booking__isnull=True,
    ).count()

    # Occupancy rate over last 90 days
    ninety_days_ago = (timezone.now() - timedelta(days=90)).date()
    recent_confirmed = Booking.objects.filter(
        listing=listing,
        status__in=[BookingStatus.CONFIRMED, BookingStatus.ACTIVE, BookingStatus.COMPLETED],
        start_date__gte=ninety_days_ago,
    )
    booked_days = sum((b.end_date - b.start_date).days for b in recent_confirmed)
    occupancy_rate = round(min((booked_days / 90) * 100, 100), 1)

    revenue = confirmed.aggregate(
        gross=Sum('gross_amount'),
        payout=Sum('owner_payout_amount'),
    )

    conversion_rate = (
        round((confirmed_count / total_requests) * 100, 1)
        if total_requests > 0 else 0.0
    )

    return Response({
        'success': True,
        'data': {
            'listing_id': str(listing.id),
            'view_count': listing.view_count,
            'inquiry_count': inquiry_count,
            'booking_request_count': total_requests,
            'confirmed_booking_count': confirmed_count,
            'conversion_rate': conversion_rate,
            'occupancy_rate_90d': occupancy_rate,
            'total_gross_revenue': str(revenue['gross'] or Decimal('0.00')),
            'total_payout': str(revenue['payout'] or Decimal('0.00')),
        },
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsOwnerRole])
def duplicate_listing(request, listing_id):
    """
    Duplicate a listing as a new draft.
    All fields are copied except: status (set to draft), view_count (reset to 0).
    Photos are NOT duplicated — owner must re-upload for the new listing.
    """
    original = get_object_or_404(Listing, id=listing_id, owner=request.user)

    duplicate = Listing.objects.create(
        owner=request.user,
        resource_type=original.resource_type,
        title=f"{original.title} (Copy)",
        description=original.description,
        category=original.category,
        price_daily=original.price_daily,
        price_weekly=original.price_weekly,
        price_monthly=original.price_monthly,
        specs=original.specs,
        location=original.location,
        location_address=original.location_address,
        location_city=original.location_city,
        operator_available=original.operator_available,
        delivery_available=original.delivery_available,
        status='draft',
        is_available=True,
        verification_tier='basic',
        view_count=0,
    )

    from listings.serializers import ListingSerializer
    return Response({
        'success': True,
        'message': 'Listing duplicated as draft. Add photos and publish when ready.',
        'data': ListingSerializer(duplicate, context={'request': request}).data,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsOwnerRole])
def bulk_listing_action(request):
    """
    Perform a bulk status action on multiple listings.

    Body:
        ids: [uuid, uuid, ...]   — listing IDs to action
        action: 'activate' | 'pause' | 'archive'
    """
    ids = request.data.get('ids', [])
    action = request.data.get('action', '')

    if not ids:
        return Response(
            {'success': False, 'errors': 'ids must be a non-empty list.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if action not in ['activate', 'pause', 'archive']:
        return Response(
            {'success': False, 'errors': "action must be 'activate', 'pause', or 'archive'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(ids) > 50:
        return Response(
            {'success': False, 'errors': 'Cannot action more than 50 listings at once.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Only allow owner to action their own listings
    listings = Listing.objects.filter(id__in=ids, owner=request.user)
    found_count = listings.count()

    if found_count == 0:
        return Response(
            {'success': False, 'errors': 'No matching listings found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    status_map = {
        'activate': 'active',
        'pause': 'paused',
        'archive': 'archived',
    }

    # For activate: only listings with a location and at least one photo can go active
    if action == 'activate':
        activated_count = 0
        skipped_count = 0
        skipped_titles = []

        for listing in listings:
            if listing.location and listing.media.exists():
                listing.status = 'active'
                listing.save(update_fields=['status'])
                activated_count += 1
            else:
                skipped_count += 1
                skipped_titles.append(listing.title)

        return Response({
            'success': True,
            'message': f"Activated {activated_count} listings.",
            'activated': activated_count,
            'skipped': skipped_count,
            'skipped_reason': 'Missing location or photos',
            'skipped_listings': skipped_titles,
        })

    # For pause and archive: no preconditions
    updated = listings.update(status=status_map[action])

    return Response({
        'success': True,
        'message': f"Updated {updated} listings to '{action}'.",
        'updated_count': updated,
    })


# ─────────────────────────────────────────────────────────────
# OWNER SETTINGS
# ─────────────────────────────────────────────────────────────

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsOwnerRole])
@parser_classes([MultiPartParser, FormParser])
def business_profile(request):
    """Get or update the owner's business profile."""
    profile = get_or_create_owner_profile(request.user)

    if request.method == 'GET':
        serializer = OwnerProfileSerializer(profile)
        return Response({'success': True, 'data': serializer.data})

    serializer = UpdateBusinessProfileSerializer(
        profile, data=request.data, partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({
        'success': True,
        'message': 'Business profile updated.',
        'data': OwnerProfileSerializer(profile).data,
    })


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsOwnerRole])
def bank_account(request):
    """Get or update the owner's bank account details."""
    profile = get_or_create_owner_profile(request.user)

    if request.method == 'GET':
        return Response({
            'success': True,
            'data': {
                'bank_name': profile.bank_name,
                'bank_account_number': profile.bank_account_number,
                'bank_account_name': profile.bank_account_name,
            },
        })

    serializer = UpdateBankAccountSerializer(
        profile, data=request.data, partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({
        'success': True,
        'message': 'Bank account details updated.',
        'data': {
            'bank_name': profile.bank_name,
            'bank_account_number': profile.bank_account_number,
            'bank_account_name': profile.bank_account_name,
        },
    })


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsOwnerRole])
def notification_preferences(request):
    """Get or update the owner's notification preferences."""
    profile = get_or_create_owner_profile(request.user)

    if request.method == 'GET':
        serializer = UpdateNotificationPreferencesSerializer(profile)
        return Response({'success': True, 'data': serializer.data})

    serializer = UpdateNotificationPreferencesSerializer(
        profile, data=request.data, partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({
        'success': True,
        'message': 'Notification preferences updated.',
        'data': UpdateNotificationPreferencesSerializer(profile).data,
    })
```

---

## Step 3: Create owner app URLs

**Create `owner/urls.py`:**

```python
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.owner_dashboard, name='owner-dashboard'),

    # Booking calendar
    path('bookings/calendar/', views.booking_calendar, name='owner-booking-calendar'),

    # Analytics
    path('analytics/revenue/', views.analytics_revenue, name='owner-analytics-revenue'),
    path('analytics/performance/', views.analytics_performance, name='owner-analytics-performance'),

    # Listing utilities
    path('listings/<uuid:listing_id>/stats/', views.listing_stats, name='owner-listing-stats'),
    path('listings/<uuid:listing_id>/duplicate/', views.duplicate_listing, name='owner-listing-duplicate'),
    path('listings/bulk/', views.bulk_listing_action, name='owner-listing-bulk'),

    # Settings
    path('business-profile/', views.business_profile, name='owner-business-profile'),
    path('bank-account/', views.bank_account, name='owner-bank-account'),
    path('notifications/', views.notification_preferences, name='owner-notifications'),
]
```

---

## Step 4: Create owner app config

**Update `owner/apps.py`:**

```python
from django.apps import AppConfig


class OwnerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'owner'
```

**Create `owner/admin.py`:**

```python
from django.contrib import admin
```

**Create `owner/models.py`:**

```python
# Owner app has no models — data lives in accounts.OwnerProfile
```

---

## Step 5: Register OwnerProfile-related endpoints in the full URL structure

Verify `config/urls.py` has the owner path. It should already be there from Part 1 Step 11. Confirm the full urlpatterns list looks like this:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health-check'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/auth/', include('accounts.urls.auth')),
    path('api/v1/users/', include('accounts.urls.users')),
    path('api/v1/listings/', include('listings.urls')),
    path('api/v1/search/', include('search.urls')),
    path('api/v1/bookings/', include('bookings.urls')),
    path('api/v1/threads/', include('messaging.urls')),
    path('api/v1/owner/', include('owner.urls')),
]
```

---

## Step 6: Run system check and migrations

```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

`makemigrations` should produce no new migrations — all model changes were in Part 1. If it does produce migrations, apply them.

---

## Step 7: Update the seed script to create OwnerProfiles

**Open `scripts/seed.py`** and append the following block at the end of the file, before the final print statements:

```python
# ── Owner Profiles ─────────────────────────────────────────────────────────

from accounts.models import OwnerProfile

for owner_user in [owner1, owner2, dual]:
    profile, created = OwnerProfile.objects.get_or_create(user=owner_user)
    if created or not profile.business_name:
        if owner_user == owner1:
            profile.business_name = 'Okafor Heavy Equipment Ltd'
            profile.business_description = 'Lagos-based crane and excavator fleet operator with 15 years experience.'
            profile.bank_name = 'First Bank'
            profile.bank_account_number = '3012345678'
            profile.bank_account_name = 'OKAFOR HEAVY EQUIPMENT LTD'
        elif owner_user == owner2:
            profile.business_name = 'Adeleke Logistics & Storage'
            profile.business_description = 'Warehouse and transport solutions across Lagos and Port Harcourt.'
            profile.bank_name = 'GTBank'
            profile.bank_account_number = '0123456789'
            profile.bank_account_name = 'ADELEKE LOGISTICS AND STORAGE'
        else:
            profile.business_name = 'Eze Multi-Resources'
            profile.bank_name = 'Zenith Bank'
            profile.bank_account_number = '2012345678'
            profile.bank_account_name = 'CHIDI EZE'
        profile.save()
        print(f"  Created owner profile: {profile.business_name}")
```

Re-run the seed script:

```bash
python manage.py shell < scripts/seed.py
```

---

## Step 8: Final commit

```bash
git add .
git commit -m "feat(owner-api): Wave 05 Part 2 — All owner web app endpoints complete"
git tag backend-complete-v1.0
git push origin main --tags
```

---

## Complete Definition of Done (Both Parts)

Verify every item using Postman or curl before marking Wave 05 complete.

---

### Owner Dashboard

- [ ] `GET /api/v1/owner/dashboard/` returns `stats`, `pending_requests`, `recent_messages`
- [ ] `stats` contains: `total_listings`, `active_listings`, `pending_booking_requests`, `active_bookings`, `unread_messages`, `revenue_this_month`
- [ ] Returns 403 if user does not have `is_owner=True`
- [ ] `pending_requests` contains up to 5 bookings with `renter_name`, `listing_title`, `dates`, `gross_amount`
- [ ] `recent_messages` contains up to 5 threads with `other_participant_name`, `last_message_body`, `unread_count`

---

### Booking Calendar

- [ ] `GET /api/v1/owner/bookings/calendar/?start_date=2026-06-01&end_date=2026-06-30` returns listings with their bookings in the period
- [ ] Each listing in response has: `id`, `title`, `resource_type`, `bookings[]`
- [ ] Each booking in `bookings[]` has: `id`, `start_date`, `end_date`, `status`, `renter_name`, `gross_amount`
- [ ] Missing `start_date` or `end_date` returns 400
- [ ] Range over 90 days returns 400
- [ ] Listings with no bookings in the range still appear with empty `bookings: []`
- [ ] Only `pending`, `confirmed`, `active` bookings are included (not cancelled/declined)

---

### Analytics — Revenue

- [ ] `GET /api/v1/owner/analytics/revenue/?period=month&year=2026&month=5` returns revenue for May 2026
- [ ] `GET /api/v1/owner/analytics/revenue/?period=year&year=2026` returns revenue for full year
- [ ] `GET /api/v1/owner/analytics/revenue/?period=all` returns all-time revenue
- [ ] Response contains: `gross_total`, `commission_total`, `payout_total`, `booking_count`, `avg_booking_value`
- [ ] Response contains `by_listing[]` with per-listing revenue breakdown
- [ ] Response contains `monthly_trend[]` covering last 12 months regardless of period filter
- [ ] All amounts are strings (not floats — Decimal serialisation)
- [ ] Returns 403 if user is not an owner

---

### Analytics — Performance

- [ ] `GET /api/v1/owner/analytics/performance/?period=last_30_days` returns last 30 days
- [ ] `GET /api/v1/owner/analytics/performance/?period=last_90_days` returns last 90 days
- [ ] Response contains: `total_views`, `total_inquiries`, `total_booking_requests`, `overall_conversion_rate`
- [ ] Response contains `by_listing[]` with: `views`, `inquiry_count`, `booking_request_count`, `confirmed_booking_count`, `occupancy_rate`, `conversion_rate`
- [ ] `occupancy_rate` is a float between 0 and 100 (percentage)
- [ ] `conversion_rate` is a float between 0 and 100 (percentage)

---

### Listing Stats

- [ ] `GET /api/v1/owner/listings/{id}/stats/` returns stats for a single listing
- [ ] Returns 404 if listing belongs to another owner
- [ ] Response contains: `view_count`, `inquiry_count`, `booking_request_count`, `confirmed_booking_count`, `conversion_rate`, `occupancy_rate_90d`, `total_gross_revenue`, `total_payout`

---

### Duplicate Listing

- [ ] `POST /api/v1/owner/listings/{id}/duplicate/` creates a new listing with `status=draft`
- [ ] Duplicated listing title has `" (Copy)"` appended
- [ ] All fields are copied except `view_count` (reset to 0) and `status` (set to `draft`)
- [ ] Photos are NOT duplicated
- [ ] Returns 404 if listing belongs to another owner
- [ ] Returns 403 if user is not an owner

---

### Bulk Listing Actions

- [ ] `POST /api/v1/owner/listings/bulk/` with `{"ids": [...], "action": "pause"}` pauses all listed IDs
- [ ] `action: "archive"` archives all listed IDs
- [ ] `action: "activate"` activates only listings that have a location AND at least one photo
- [ ] Listings missing location or photos are skipped — response includes `skipped_listings[]`
- [ ] Listing IDs belonging to other owners are silently ignored (not 403 — just not found in queryset)
- [ ] More than 50 IDs in one request returns 400
- [ ] Empty `ids` returns 400
- [ ] Invalid `action` returns 400

---

### Owner Settings

- [ ] `GET /api/v1/owner/business-profile/` returns business profile (auto-creates if missing)
- [ ] `PATCH /api/v1/owner/business-profile/` updates business name, description, logo
- [ ] `GET /api/v1/owner/bank-account/` returns bank details
- [ ] `PATCH /api/v1/owner/bank-account/` validates: account number must be 10 digits
- [ ] `GET /api/v1/owner/notifications/` returns notification preferences
- [ ] `PATCH /api/v1/owner/notifications/` toggles any notification preference
- [ ] All settings endpoints return 403 for non-owner users

---

### Listings (updated)

- [ ] `GET /api/v1/listings/?status=active` — filters correctly
- [ ] `GET /api/v1/listings/?resource_type=vehicle` — filters correctly
- [ ] `GET /api/v1/listings/?city=Lagos` — case-insensitive match on `location_city`
- [ ] `GET /api/v1/listings/?ordering=-view_count` — sorted descending by views
- [ ] `GET /api/v1/listings/` — response has `count`, `next`, `previous`, `results`
- [ ] Combining multiple filters works: `?status=active&resource_type=equipment`

---

### Bookings (updated)

- [ ] `GET /api/v1/bookings/?role=owner&listing_id={uuid}` — filters by listing
- [ ] `GET /api/v1/bookings/?role=owner&start_date_from=2026-06-01` — filters by date
- [ ] `GET /api/v1/bookings/?role=owner&payment_status=unpaid` — filters by payment status
- [ ] `GET /api/v1/bookings/?role=owner&ordering=-gross_amount` — sorts by amount
- [ ] `GET /api/v1/bookings/` — response has `count`, `next`, `previous`, `results`

---

### Threads (updated)

- [ ] `GET /api/v1/threads/?unread=true` — returns only threads with unread messages
- [ ] `GET /api/v1/threads/?thread_type=booking` — returns only booking threads
- [ ] `GET /api/v1/threads/?thread_type=inquiry` — returns only inquiry threads
- [ ] `GET /api/v1/threads/?listing_id={uuid}` — returns threads for one listing
- [ ] `GET /api/v1/threads/` — response has `count`, `next`, `previous`, `results`
- [ ] `PATCH /api/v1/threads/{id}/read/` — marks all unread messages as read, returns count

---

### General

- [ ] `python manage.py check` returns 0 issues
- [ ] `GET /api/docs/` — Swagger UI shows all new owner endpoints correctly documented
- [ ] Tag `backend-complete-v1.0` created and pushed
- [ ] `python manage.py shell < scripts/seed.py` runs without errors and creates 3 owner profiles

---

## Complete API Reference — Owner Web App

This is the final, complete list of every endpoint the web app frontend will call.

```
AUTH
POST   /api/v1/auth/login/
POST   /api/v1/auth/token/refresh/
POST   /api/v1/auth/logout/
POST   /api/v1/auth/password/change/

PROFILE
GET    /api/v1/users/me/
PUT    /api/v1/users/me/
PATCH  /api/v1/users/me/role/
POST   /api/v1/users/me/documents/

OWNER DASHBOARD
GET    /api/v1/owner/dashboard/

OWNER SETTINGS
GET    /api/v1/owner/business-profile/
PATCH  /api/v1/owner/business-profile/
GET    /api/v1/owner/bank-account/
PATCH  /api/v1/owner/bank-account/
GET    /api/v1/owner/notifications/
PATCH  /api/v1/owner/notifications/

INVENTORY
GET    /api/v1/listings/
POST   /api/v1/listings/
GET    /api/v1/listings/{id}/
PUT    /api/v1/listings/{id}/
PATCH  /api/v1/listings/{id}/
PATCH  /api/v1/listings/{id}/status/
DELETE /api/v1/listings/{id}/
POST   /api/v1/listings/{id}/media/
DELETE /api/v1/listings/{id}/media/{media_id}/
GET    /api/v1/owner/listings/{id}/stats/
POST   /api/v1/owner/listings/{id}/duplicate/
POST   /api/v1/owner/listings/bulk/

BOOKINGS
GET    /api/v1/bookings/
GET    /api/v1/bookings/{id}/
PATCH  /api/v1/bookings/{id}/accept/
PATCH  /api/v1/bookings/{id}/decline/
PATCH  /api/v1/bookings/{id}/cancel/
PATCH  /api/v1/bookings/{id}/pay/
GET    /api/v1/owner/bookings/calendar/

ANALYTICS
GET    /api/v1/owner/analytics/revenue/
GET    /api/v1/owner/analytics/performance/

MESSAGES
GET    /api/v1/threads/
GET    /api/v1/threads/{id}/
POST   /api/v1/threads/{id}/messages/
PATCH  /api/v1/threads/{id}/read/
POST   /api/v1/threads/token/
```

**Total: 38 endpoints. Every web app screen is fully covered.**
