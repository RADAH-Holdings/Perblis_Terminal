# TERMINAL — WAVE 03: BOOKINGS + MESSAGING
> Agent task file. Execute every instruction in order. Do not skip steps.
> Wave 02 must be complete before starting this wave.
> Do not proceed to Wave 04 until the Definition of Done checklist is fully complete.

---

## Context

This wave builds the `bookings` app (the full booking lifecycle) and the `messaging` app (in-context chat). After this wave, the complete Terminal core loop is functional: find on map → request booking → owner confirms → both parties chat.

**Simulation decisions (do not deviate):**
- Payment: After a booking is confirmed, the renter can call a "mark as paid" endpoint. This sets `payment_status = 'simulated_paid'`. No Paystack integration.
- Cancellation: Either party can cancel a confirmed booking. No penalty, no refund logic.
- Contracts: No PDF generation for MVP.
- Real-time messaging: Use Ably for delivery. Django saves messages to PostgreSQL (source of truth). Ably delivers to connected clients. Do NOT use Django Channels or WebSockets.

---

## Step 1: Create the Bookings models

**File: `bookings/models.py`**

```python
import uuid
from django.conf import settings
from django.db import models

from core.models import BaseModel


class BookingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    DECLINED = 'declined', 'Declined'
    ACTIVE = 'active', 'Active'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class DurationType(models.TextChoices):
    DAILY = 'daily', 'Daily'
    WEEKLY = 'weekly', 'Weekly'
    MONTHLY = 'monthly', 'Monthly'


class PaymentStatus(models.TextChoices):
    UNPAID = 'unpaid', 'Unpaid'
    SIMULATED_PAID = 'simulated_paid', 'Paid (Simulated)'


class Booking(BaseModel):
    renter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='renter_bookings',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owner_bookings',
    )
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='bookings',
    )

    # Dates
    start_date = models.DateField()
    end_date = models.DateField()
    duration_type = models.CharField(
        max_length=10,
        choices=DurationType.choices,
        default=DurationType.DAILY,
    )

    # Financials — tracked for future use, not enforced in MVP
    gross_amount = models.DecimalField(max_digits=15, decimal_places=2)
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=0.1000
    )
    commission_amount = models.DecimalField(max_digits=15, decimal_places=2)
    owner_payout_amount = models.DecimalField(max_digits=15, decimal_places=2)

    # Communication
    renter_note = models.TextField(blank=True, default='')

    # Status
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )

    # Cancellation
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cancellations',
    )
    cancellation_reason = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'bookings'
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking: {self.listing.title} | {self.renter.email} | {self.status}"

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return 0
```

---

## Step 2: Create Bookings serializers

**File: `bookings/serializers.py`**

```python
from decimal import Decimal
from datetime import date

from django.contrib.auth import get_user_model
from rest_framework import serializers

from listings.models import Listing
from listings.serializers import ListingSerializer
from .models import Booking, BookingStatus, DurationType

User = get_user_model()

COMMISSION_RATE = Decimal('0.10')


def calculate_booking_amounts(listing, start_date, end_date, duration_type):
    """
    Calculate gross_amount, commission_amount, and owner_payout_amount.
    Returns a dict with all three values.
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
        weeks = max(1, days // 7)
        gross = listing.price_weekly * weeks

    elif duration_type == DurationType.MONTHLY:
        if not listing.price_monthly:
            raise serializers.ValidationError('This listing does not have a monthly price set.')
        months = max(1, days // 30)
        gross = listing.price_monthly * months

    else:
        raise serializers.ValidationError('Invalid duration_type.')

    commission = (gross * COMMISSION_RATE).quantize(Decimal('0.01'))
    payout = gross - commission

    return {
        'gross_amount': gross,
        'commission_amount': commission,
        'owner_payout_amount': payout,
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

    class Meta:
        model = Booking
        fields = [
            'id', 'renter', 'owner', 'listing_id', 'listing_title',
            'start_date', 'end_date', 'duration_type', 'duration_days',
            'gross_amount', 'commission_rate', 'commission_amount', 'owner_payout_amount',
            'renter_note', 'status', 'payment_status',
            'cancellation_reason', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


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
```

---

## Step 3: Create Bookings views

**File: `bookings/views.py`**

```python
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Booking, BookingStatus
from .serializers import (
    BookingSerializer,
    CreateBookingSerializer,
    DeclineBookingSerializer,
    CancelBookingSerializer,
)
from messaging.services import get_or_create_booking_thread


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def booking_list_create(request):
    """
    GET: Return user's bookings (as renter or owner, or both).
    POST: Create a booking request (renter role required).
    """
    if request.method == 'GET':
        role = request.query_params.get('role', 'renter')

        if role == 'owner':
            bookings = Booking.objects.filter(owner=request.user).select_related(
                'renter', 'owner', 'listing'
            )
        elif role == 'both':
            from django.db.models import Q
            bookings = Booking.objects.filter(
                Q(renter=request.user) | Q(owner=request.user)
            ).select_related('renter', 'owner', 'listing')
        else:
            bookings = Booking.objects.filter(renter=request.user).select_related(
                'renter', 'owner', 'listing'
            )

        # Optional status filter
        booking_status = request.query_params.get('status')
        if booking_status:
            bookings = bookings.filter(status=booking_status)

        serializer = BookingSerializer(bookings, many=True)
        return Response({'success': True, 'count': bookings.count(), 'data': serializer.data})

    # POST — create booking request
    if not request.user.is_renter:
        return Response(
            {'success': False, 'errors': 'You must have the renter role to make bookings.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = CreateBookingSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data
    amounts = data['amounts']
    listing = data['listing']

    booking = Booking.objects.create(
        renter=request.user,
        owner=listing.owner,
        listing=listing,
        start_date=data['start_date'],
        end_date=data['end_date'],
        duration_type=data['duration_type'],
        renter_note=data['renter_note'],
        gross_amount=amounts['gross_amount'],
        commission_rate=0.10,
        commission_amount=amounts['commission_amount'],
        owner_payout_amount=amounts['owner_payout_amount'],
        status=BookingStatus.PENDING,
    )

    # Automatically create a messaging thread for this booking
    get_or_create_booking_thread(booking)

    return Response(
        {'success': True, 'data': BookingSerializer(booking).data},
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_detail(request, booking_id):
    """Get booking detail. Only renter or owner can view."""
    booking = get_object_or_404(
        Booking.objects.select_related('renter', 'owner', 'listing'),
        id=booking_id,
    )

    if booking.renter != request.user and booking.owner != request.user:
        return Response(
            {'success': False, 'errors': 'You do not have access to this booking.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    return Response({'success': True, 'data': BookingSerializer(booking).data})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def booking_accept(request, booking_id):
    """Accept a pending booking. Owner only."""
    booking = get_object_or_404(Booking, id=booking_id, owner=request.user)

    if booking.status != BookingStatus.PENDING:
        return Response(
            {'success': False, 'errors': f"Cannot accept a booking with status '{booking.status}'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    booking.status = BookingStatus.CONFIRMED
    booking.save(update_fields=['status', 'updated_at'])

    return Response({
        'success': True,
        'message': 'Booking confirmed.',
        'data': BookingSerializer(booking).data,
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def booking_decline(request, booking_id):
    """Decline a pending booking. Owner only."""
    booking = get_object_or_404(Booking, id=booking_id, owner=request.user)

    if booking.status != BookingStatus.PENDING:
        return Response(
            {'success': False, 'errors': f"Cannot decline a booking with status '{booking.status}'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = DeclineBookingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    booking.status = BookingStatus.DECLINED
    booking.cancellation_reason = serializer.validated_data.get('reason', '')
    booking.save(update_fields=['status', 'cancellation_reason', 'updated_at'])

    return Response({
        'success': True,
        'message': 'Booking declined.',
        'data': BookingSerializer(booking).data,
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def booking_cancel(request, booking_id):
    """Cancel a booking. Either renter or owner can cancel."""
    from django.db.models import Q
    booking = get_object_or_404(
        Booking.objects.filter(Q(renter=request.user) | Q(owner=request.user)),
        id=booking_id,
    )

    cancellable_statuses = [BookingStatus.PENDING, BookingStatus.CONFIRMED]
    if booking.status not in cancellable_statuses:
        return Response(
            {'success': False, 'errors': f"Cannot cancel a booking with status '{booking.status}'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = CancelBookingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_by = request.user
    booking.cancellation_reason = serializer.validated_data.get('reason', '')
    booking.save(update_fields=['status', 'cancelled_by', 'cancellation_reason', 'updated_at'])

    return Response({
        'success': True,
        'message': 'Booking cancelled.',
        'data': BookingSerializer(booking).data,
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def booking_mark_paid(request, booking_id):
    """
    Mark a booking as paid. MVP simulation — no real payment.
    Either party can mark as paid.
    """
    from django.db.models import Q
    booking = get_object_or_404(
        Booking.objects.filter(Q(renter=request.user) | Q(owner=request.user)),
        id=booking_id,
    )

    if booking.status != BookingStatus.CONFIRMED:
        return Response(
            {'success': False, 'errors': 'Only confirmed bookings can be marked as paid.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    booking.payment_status = 'simulated_paid'
    booking.save(update_fields=['payment_status', 'updated_at'])

    print(f"[DEV PAYMENT] Booking {booking.id} marked as paid (simulated) by {request.user.email}")

    return Response({
        'success': True,
        'message': 'Booking marked as paid (simulated). Coordinate payment directly with the other party.',
        'data': BookingSerializer(booking).data,
    })
```

---

## Step 4: Wire up Bookings URLs

**File: `bookings/urls.py`**

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.booking_list_create, name='booking-list-create'),
    path('<uuid:booking_id>/', views.booking_detail, name='booking-detail'),
    path('<uuid:booking_id>/accept/', views.booking_accept, name='booking-accept'),
    path('<uuid:booking_id>/decline/', views.booking_decline, name='booking-decline'),
    path('<uuid:booking_id>/cancel/', views.booking_cancel, name='booking-cancel'),
    path('<uuid:booking_id>/pay/', views.booking_mark_paid, name='booking-mark-paid'),
]
```

---

## Step 5: Create the Messaging models

**File: `messaging/models.py`**

```python
import uuid
from django.conf import settings
from django.db import models

from core.models import BaseModel


class Thread(BaseModel):
    """
    A conversation thread. Tied to either a listing (inquiry) or a booking.
    A booking thread is created automatically when a booking request is made.
    An inquiry thread is created when a renter messages an owner from a listing page.
    """
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='threads',
        null=True, blank=True,
    )
    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='thread',
        null=True, blank=True,
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='threads',
    )

    class Meta:
        db_table = 'threads'
        ordering = ['-updated_at']

    def __str__(self):
        if self.booking:
            return f"Booking thread: {self.booking}"
        return f"Inquiry thread: {self.listing}"

    @property
    def is_booking_thread(self):
        return self.booking_id is not None

    def get_other_participant(self, user):
        return self.participants.exclude(id=user.id).first()


class Message(BaseModel):
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    body = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.email} in thread {self.thread.id}"
```

---

## Step 6: Create Messaging services

**File: `messaging/services.py`**

```python
from django.conf import settings


def get_or_create_booking_thread(booking):
    """
    Get or create a thread for a booking.
    Called automatically when a booking is created.
    """
    from .models import Thread

    thread, created = Thread.objects.get_or_create(booking=booking)
    if created:
        thread.listing = booking.listing
        thread.save()
        thread.participants.add(booking.renter, booking.owner)
    return thread


def get_or_create_inquiry_thread(listing, renter):
    """
    Get or create an inquiry thread between a renter and a listing owner.
    Used when a renter sends a message from the listing page before booking.
    """
    from .models import Thread

    existing = Thread.objects.filter(
        listing=listing,
        booking__isnull=True,
        participants=renter,
    ).first()

    if existing:
        return existing, False

    thread = Thread.objects.create(listing=listing)
    thread.participants.add(renter, listing.owner)
    return thread, True


def publish_to_ably(thread_id, message_data):
    """
    Publish a new message to the Ably channel for the thread.
    Falls back gracefully if Ably is not configured.
    """
    from django.conf import settings

    if not settings.ABLY_API_KEY:
        print(f"[DEV ABLY] Ably not configured. Message in thread {thread_id}: {message_data}")
        return

    try:
        from ably import AblyRest
        client = AblyRest(settings.ABLY_API_KEY)
        channel = client.channels.get(f"thread:{thread_id}")
        channel.publish('new_message', message_data)
    except Exception as e:
        print(f"[ABLY ERROR] Failed to publish to thread {thread_id}: {e}")


def get_ably_token(user):
    """
    Generate an Ably token for the authenticated user.
    The token is scoped to channels this user is a participant in.
    """
    if not settings.ABLY_API_KEY:
        return None

    try:
        from ably import AblyRest
        from ably.types.tokenrequest import TokenRequest

        client = AblyRest(settings.ABLY_API_KEY)

        # Get user's thread IDs to scope the token
        from .models import Thread
        thread_ids = Thread.objects.filter(
            participants=user
        ).values_list('id', flat=True)

        # Build capability — user can subscribe to their own thread channels
        capability = {}
        for thread_id in thread_ids:
            capability[f"thread:{thread_id}"] = ['subscribe', 'publish']

        if not capability:
            capability = {'*': []}

        token_request = client.auth.request_token(
            token_params={
                'client_id': str(user.id),
                'capability': capability,
            }
        )
        return token_request

    except Exception as e:
        print(f"[ABLY ERROR] Token generation failed for {user.email}: {e}")
        return None
```

---

## Step 7: Create Messaging serializers

**File: `messaging/serializers.py`**

```python
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Thread, Message

User = get_user_model()


class MessageSenderSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'profile_photo']


class MessageSerializer(serializers.ModelSerializer):
    sender = MessageSenderSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'body', 'is_read', 'created_at']
        read_only_fields = ['id', 'sender', 'is_read', 'created_at']


class SendMessageSerializer(serializers.Serializer):
    body = serializers.CharField(required=True, allow_blank=False)


class ThreadSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    listing_title = serializers.CharField(source='listing.title', read_only=True, default=None)
    booking_id = serializers.UUIDField(source='booking.id', read_only=True, default=None)
    is_booking_thread = serializers.ReadOnlyField()

    class Meta:
        model = Thread
        fields = [
            'id', 'is_booking_thread', 'booking_id', 'listing_title',
            'other_participant', 'last_message', 'unread_count',
            'created_at', 'updated_at',
        ]

    def get_other_participant(self, obj):
        request = self.context.get('request')
        if request:
            other = obj.get_other_participant(request.user)
            if other:
                return {
                    'id': str(other.id),
                    'full_name': other.full_name,
                    'profile_photo': request.build_absolute_uri(other.profile_photo.url) if other.profile_photo else None,
                }
        return None

    def get_last_message(self, obj):
        last = obj.messages.last()
        if last:
            return {
                'body': last.body[:100],
                'sender_name': last.sender.full_name,
                'created_at': last.created_at,
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0


class CreateInquiryThreadSerializer(serializers.Serializer):
    listing_id = serializers.UUIDField(required=True)
    initial_message = serializers.CharField(required=True, allow_blank=False)
```

---

## Step 8: Create Messaging views

**File: `messaging/views.py`**

```python
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from listings.models import Listing
from .models import Thread, Message
from .serializers import (
    ThreadSerializer,
    MessageSerializer,
    SendMessageSerializer,
    CreateInquiryThreadSerializer,
)
from .services import (
    get_or_create_inquiry_thread,
    publish_to_ably,
    get_ably_token,
)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def thread_list_create(request):
    """
    GET: List all threads the user is a participant in.
    POST: Start an inquiry thread from a listing page.
    """
    if request.method == 'GET':
        threads = (
            Thread.objects
            .filter(participants=request.user)
            .prefetch_related('participants', 'messages')
            .select_related('listing', 'booking')
            .order_by('-updated_at')
        )
        serializer = ThreadSerializer(threads, many=True, context={'request': request})
        return Response({'success': True, 'data': serializer.data})

    # POST — start an inquiry thread
    serializer = CreateInquiryThreadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    listing_id = serializer.validated_data['listing_id']
    initial_message = serializer.validated_data['initial_message']

    listing = get_object_or_404(Listing, id=listing_id, status='active')

    # Cannot message yourself
    if listing.owner == request.user:
        return Response(
            {'success': False, 'errors': 'You cannot send an inquiry to your own listing.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    thread, created = get_or_create_inquiry_thread(listing, request.user)

    # Send the initial message
    message = Message.objects.create(
        thread=thread,
        sender=request.user,
        body=initial_message,
    )

    # Update thread's updated_at
    Thread.objects.filter(id=thread.id).update(updated_at=message.created_at)

    # Publish to Ably
    publish_to_ably(str(thread.id), {
        'id': str(message.id),
        'body': message.body,
        'sender_id': str(message.sender.id),
        'sender_name': message.sender.full_name,
        'created_at': message.created_at.isoformat(),
    })

    return Response({
        'success': True,
        'data': ThreadSerializer(thread, context={'request': request}).data,
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def thread_detail(request, thread_id):
    """
    Get thread detail with all messages.
    Auto-marks messages from the other party as read.
    """
    thread = get_object_or_404(
        Thread.objects.prefetch_related('participants', 'messages__sender')
        .select_related('listing', 'booking'),
        id=thread_id,
        participants=request.user,
    )

    # Mark messages from others as read
    Message.objects.filter(
        thread=thread,
        is_read=False,
    ).exclude(sender=request.user).update(is_read=True)

    messages = thread.messages.all()
    message_serializer = MessageSerializer(messages, many=True, context={'request': request})
    thread_serializer = ThreadSerializer(thread, context={'request': request})

    return Response({
        'success': True,
        'thread': thread_serializer.data,
        'messages': message_serializer.data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request, thread_id):
    """Send a message in a thread."""
    thread = get_object_or_404(
        Thread,
        id=thread_id,
        participants=request.user,
    )

    serializer = SendMessageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    message = Message.objects.create(
        thread=thread,
        sender=request.user,
        body=serializer.validated_data['body'],
    )

    # Update thread's updated_at
    from django.utils import timezone
    Thread.objects.filter(id=thread.id).update(updated_at=timezone.now())

    # Publish to Ably for real-time delivery
    publish_to_ably(str(thread.id), {
        'id': str(message.id),
        'body': message.body,
        'sender_id': str(message.sender.id),
        'sender_name': message.sender.full_name,
        'created_at': message.created_at.isoformat(),
    })

    return Response({
        'success': True,
        'data': MessageSerializer(message, context={'request': request}).data,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_messaging_token(request):
    """Get an Ably authentication token scoped to this user's threads."""
    token = get_ably_token(request.user)

    if token is None:
        return Response({
            'success': False,
            'errors': 'Real-time messaging is not configured. Check ABLY_API_KEY.',
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return Response({'success': True, 'token': token})
```

---

## Step 9: Wire up Messaging URLs

**File: `messaging/urls.py`**

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.thread_list_create, name='thread-list-create'),
    path('<uuid:thread_id>/', views.thread_detail, name='thread-detail'),
    path('<uuid:thread_id>/messages/', views.send_message, name='send-message'),
    path('token/', views.get_messaging_token, name='messaging-token'),
]
```

---

## Step 10: Register Bookings and Messaging in Django Admin

**File: `bookings/admin.py`**

```python
from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(ModelAdmin):
    list_display = [
        'id', 'listing', 'renter', 'owner',
        'start_date', 'end_date', 'gross_amount',
        'status', 'payment_status', 'created_at',
    ]
    list_filter = ['status', 'payment_status', 'duration_type']
    search_fields = [
        'listing__title', 'renter__email', 'owner__email',
    ]
    readonly_fields = [
        'id', 'renter', 'owner', 'listing',
        'gross_amount', 'commission_rate', 'commission_amount', 'owner_payout_amount',
        'created_at', 'updated_at',
    ]
    ordering = ['-created_at']

    actions = ['cancel_bookings']

    @admin.action(description='Cancel selected bookings')
    def cancel_bookings(self, request, queryset):
        queryset.filter(
            status__in=['pending', 'confirmed']
        ).update(status='cancelled')
```

**File: `messaging/admin.py`**

```python
from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Thread, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['id', 'sender', 'body', 'is_read', 'created_at']
    can_delete = False


@admin.register(Thread)
class ThreadAdmin(ModelAdmin):
    list_display = ['id', 'listing', 'booking', 'is_booking_thread', 'created_at']
    list_filter = ['created_at']
    search_fields = ['listing__title', 'participants__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [MessageInline]
```

---

## Step 11: Create and run migrations

```bash
python manage.py makemigrations bookings messaging
python manage.py migrate
```

---

## Step 12: Commit

```bash
git add .
git commit -m "feat(bookings,messaging): Wave 03 — Bookings and Messaging complete"
```

---

## Definition of Done

Verify every item before handing back to supervisor.

**Booking Model:**
- [ ] `Booking` has `renter`, `owner`, `listing` FKs
- [ ] `BookingStatus` choices: `pending`, `confirmed`, `declined`, `active`, `completed`, `cancelled`
- [ ] `Booking` tracks `gross_amount`, `commission_amount`, `owner_payout_amount`
- [ ] `Booking` has `payment_status` with `unpaid` / `simulated_paid`

**Booking API (test all with Postman or curl):**
- [ ] `POST /api/v1/bookings/` → creates booking request, creates messaging thread automatically
- [ ] `POST /api/v1/bookings/` with past start_date → returns 400
- [ ] `POST /api/v1/bookings/` for own listing → returns 400
- [ ] `POST /api/v1/bookings/` with date conflict → returns 400
- [ ] `GET /api/v1/bookings/?role=renter` → returns renter bookings
- [ ] `GET /api/v1/bookings/?role=owner` → returns owner bookings
- [ ] `GET /api/v1/bookings/{id}/` → returns detail (403 for non-participants)
- [ ] `PATCH /api/v1/bookings/{id}/accept/` → confirms booking (owner only)
- [ ] `PATCH /api/v1/bookings/{id}/decline/` → declines booking (owner only)
- [ ] `PATCH /api/v1/bookings/{id}/cancel/` → cancels booking (either party)
- [ ] `PATCH /api/v1/bookings/{id}/pay/` → sets payment_status to simulated_paid, prints `[DEV PAYMENT]` to console

**Date conflict check:**
- [ ] Two confirmed bookings for overlapping dates on the same listing are not allowed
- [ ] Pending bookings do NOT block new requests (only confirmed and active do)

**Messaging Model:**
- [ ] `Thread` can be linked to a `Booking` (OneToOneField) OR a `Listing` (ForeignKey)
- [ ] `Thread.participants` is a ManyToManyField
- [ ] `Message` has `thread`, `sender`, `body`, `is_read`

**Messaging API:**
- [ ] `GET /api/v1/threads/` → returns all threads for the authenticated user
- [ ] `POST /api/v1/threads/` → creates an inquiry thread with an initial message
- [ ] `GET /api/v1/threads/{id}/` → returns thread + all messages, marks unread as read
- [ ] `POST /api/v1/threads/{id}/messages/` → sends a message, publishes to Ably
- [ ] A non-participant cannot access a thread (404 from queryset filter)
- [ ] When a booking is created, a thread is automatically created and both parties are added

**Ably:**
- [ ] `POST /api/v1/threads/token/` → returns Ably token if `ABLY_API_KEY` is set
- [ ] If `ABLY_API_KEY` is empty, `publish_to_ably` prints `[DEV ABLY]` to console and does not crash
- [ ] If `ABLY_API_KEY` is empty, `get_messaging_token` returns 503

**Django Admin:**
- [ ] Booking list shows: listing, renter, owner, dates, amount, status, payment_status
- [ ] Cancel bulk action works on bookings
- [ ] Thread list shows: listing, booking, type
- [ ] Thread detail shows all messages inline (read-only)

**General:**
- [ ] `python manage.py check` returns 0 issues
- [ ] Migrations ran with no errors
- [ ] Git commit made with message `feat(bookings,messaging): Wave 03 — Bookings and Messaging complete`
