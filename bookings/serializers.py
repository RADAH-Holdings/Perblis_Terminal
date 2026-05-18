import math
from datetime import date

from django.contrib.auth import get_user_model
from rest_framework import serializers

from listings.models import Listing
from .commission import calculate_commission
from .models import Booking, BookingStatus, DurationType

User = get_user_model()


def calculate_booking_amounts(listing, start_date, end_date, duration_type):
    """
    Calculate gross_amount, commission_amount, and owner_payout_amount
    using the tiered commission rate structure.

    Duration classification (FSD §9.7.2):
      - 1 day = daily rate × 1
      - 2–6 days = daily rate × number of days
      - 7 days = weekly rate × 1
      - 8–27 days = weekly rate × ceil(days / 7)
      - 28+ days = monthly rate × ceil(days / 28)

    Returns a dict with gross_amount, commission_amount, owner_payout_amount,
    commission_rate (Decimal), and commission_rate_label (str).
    """
    days = (end_date - start_date).days
    if days <= 0:
        raise serializers.ValidationError('end_date must be after start_date.')

    if duration_type == DurationType.DAILY:
        if not listing.price_daily:
            raise serializers.ValidationError('This listing does not have a daily price set.')
        gross = listing.price_daily * days

    elif duration_type == DurationType.WEEKLY:
        if not listing.price_weekly:
            raise serializers.ValidationError('This listing does not have a weekly price set.')
        weeks = max(1, math.ceil(days / 7))
        gross = listing.price_weekly * weeks

    elif duration_type == DurationType.MONTHLY:
        if not listing.price_monthly:
            raise serializers.ValidationError('This listing does not have a monthly price set.')
        months = max(1, math.ceil(days / 28))
        gross = listing.price_monthly * months

    else:
        raise serializers.ValidationError('Invalid duration_type.')

    commission_amount, rate_decimal, rate_label = calculate_commission(
        gross, listing.resource_type, duration_type,
    )
    payout = gross - commission_amount

    return {
        'gross_amount': gross,
        'commission_amount': commission_amount,
        'owner_payout_amount': payout,
        'commission_rate': rate_decimal,
        'commission_rate_label': rate_label,
    }


class BookingPartySerializer(serializers.Serializer):
    """Minimal user info for booking detail responses."""
    id = serializers.UUIDField()
    full_name = serializers.CharField()
    profile_photo = serializers.ImageField()
    phone = serializers.CharField()


class BookingSerializer(serializers.ModelSerializer):
    """Full booking detail."""
    renter = BookingPartySerializer(read_only=True)
    owner = BookingPartySerializer(read_only=True)
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_id = serializers.UUIDField(source='listing.id', read_only=True)
    duration_days = serializers.ReadOnlyField()
    thread_id = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'renter', 'owner', 'listing_id', 'listing_title',
            'start_date', 'end_date', 'duration_type', 'duration_days',
            'gross_amount', 'commission_rate', 'commission_rate_label',
            'commission_amount', 'owner_payout_amount',
            'renter_note', 'status', 'payment_status',
            'cancellation_reason', 'thread_id', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_thread_id(self, obj):
        try:
            return str(obj.thread.id)
        except Exception:
            return None


class CreateBookingSerializer(serializers.Serializer):
    listing_id = serializers.UUIDField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    duration_type = serializers.ChoiceField(
        choices=[c[0] for c in DurationType.choices],
        default=DurationType.DAILY,
    )
    renter_note = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        listing_id = attrs['listing_id']
        start_date = attrs['start_date']
        end_date = attrs['end_date']
        duration_type = attrs['duration_type']

        # Validate listing exists and is active
        try:
            listing = Listing.objects.get(id=listing_id, status='active', is_available=True)
        except Listing.DoesNotExist:
            raise serializers.ValidationError({'listing_id': 'Listing not found or not available.'})

        # Cannot book own listing
        request = self.context.get('request')
        if listing.owner == request.user:
            raise serializers.ValidationError({'listing_id': 'You cannot book your own listing.'})

        # Validate dates
        if start_date < date.today():
            raise serializers.ValidationError({'start_date': 'Start date cannot be in the past.'})
        if end_date <= start_date:
            raise serializers.ValidationError({'end_date': 'End date must be after start date.'})

        # Check for date conflicts on this listing
        conflict = Booking.objects.filter(
            listing=listing,
            status__in=[BookingStatus.CONFIRMED, BookingStatus.ACTIVE],
            start_date__lt=end_date,
            end_date__gt=start_date,
        ).exists()
        if conflict:
            raise serializers.ValidationError(
                'This listing is already booked for part or all of your requested dates.'
            )

        # Calculate amounts
        amounts = calculate_booking_amounts(listing, start_date, end_date, duration_type)

        attrs['listing'] = listing
        attrs['amounts'] = amounts
        return attrs


class DeclineBookingSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default='')


class CancelBookingSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default='')
