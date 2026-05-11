# TERMINAL — WAVE 06: COMPREHENSIVE TESTING (Part 2 of 2)
> Agent task file. Execute every instruction in order. Do not skip steps.
> Part 1 must pass with 0 failures before starting Part 2.
> After Part 2, run the full test suite. 0 failures required before proceeding to Wave 07.

---

## Context

Part 2 covers bookings, messaging, and the entire owner app. This includes the most complex business logic in Terminal — booking state transitions, date conflict detection, cross-module signals, real-time messaging, and all analytics calculations.

---

## Step 1: Create bookings app tests

**Create `bookings/tests/__init__.py`** (empty)

**Create `bookings/tests/test_models.py`:**

```python
import pytest
from datetime import date, timedelta
from bookings.models import Booking, BookingStatus


@pytest.mark.django_db
class TestBookingModel:
    def test_booking_str(self, owner_user, renter_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        booking = Booking.objects.create(
            renter=renter_user,
            owner=owner_user,
            listing=listing,
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=10),
            duration_type='daily',
            gross_amount=250000,
            commission_rate=0.10,
            commission_amount=25000,
            owner_payout_amount=225000,
            status=BookingStatus.PENDING,
        )
        assert listing.title in str(booking)
        assert renter_user.email in str(booking)
        assert 'pending' in str(booking)

    def test_duration_days_calculation(self, owner_user, renter_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        booking = Booking.objects.create(
            renter=renter_user,
            owner=owner_user,
            listing=listing,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 11),
            duration_type='daily',
            gross_amount=500000,
            commission_rate=0.10,
            commission_amount=50000,
            owner_payout_amount=450000,
        )
        assert booking.duration_days == 10

    def test_duration_days_zero_for_same_date(self, owner_user, renter_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        today = date.today() + timedelta(days=5)
        booking = Booking.objects.create(
            renter=renter_user,
            owner=owner_user,
            listing=listing,
            start_date=today,
            end_date=today,
            duration_type='daily',
            gross_amount=50000,
            commission_rate=0.10,
            commission_amount=5000,
            owner_payout_amount=45000,
        )
        assert booking.duration_days == 0
```

**Create `bookings/tests/test_serializers.py`:**

```python
import pytest
from datetime import date, timedelta
from decimal import Decimal
from bookings.serializers import calculate_booking_amounts, CreateBookingSerializer
from bookings.models import DurationType


@pytest.mark.django_db
class TestCalculateBookingAmounts:
    def test_daily_calculation(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, price_daily=50000)
        start = date.today() + timedelta(days=5)
        end = date.today() + timedelta(days=10)
        result = calculate_booking_amounts(listing, start, end, 'daily')
        assert result['gross_amount'] == Decimal('250000')
        assert result['commission_amount'] == Decimal('25000.00')
        assert result['owner_payout_amount'] == Decimal('225000.00')

    def test_weekly_calculation(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, price_weekly=300000)
        start = date.today() + timedelta(days=5)
        end = start + timedelta(days=14)
        result = calculate_booking_amounts(listing, start, end, 'weekly')
        assert result['gross_amount'] == Decimal('600000')

    def test_monthly_calculation(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, price_monthly=1500000)
        start = date.today() + timedelta(days=5)
        end = start + timedelta(days=60)
        result = calculate_booking_amounts(listing, start, end, 'monthly')
        assert result['gross_amount'] == Decimal('3000000')

    def test_commission_is_10_percent(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, price_daily=100000)
        start = date.today() + timedelta(days=5)
        end = start + timedelta(days=1)
        result = calculate_booking_amounts(listing, start, end, 'daily')
        assert result['commission_amount'] == Decimal('10000.00')
        assert result['owner_payout_amount'] == Decimal('90000.00')

    def test_payout_equals_gross_minus_commission(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, price_daily=75000)
        start = date.today() + timedelta(days=5)
        end = start + timedelta(days=3)
        result = calculate_booking_amounts(listing, start, end, 'daily')
        assert result['owner_payout_amount'] == result['gross_amount'] - result['commission_amount']

    def test_missing_daily_price_raises_error(self, owner_user):
        import pytest
        from tests.factories import ListingFactory
        from rest_framework import serializers as drf_serializers
        listing = ListingFactory(owner=owner_user, price_daily=None)
        start = date.today() + timedelta(days=5)
        end = start + timedelta(days=3)
        with pytest.raises(drf_serializers.ValidationError):
            calculate_booking_amounts(listing, start, end, 'daily')


@pytest.mark.django_db
class TestCreateBookingSerializer:
    def test_cannot_book_own_listing(self, owner_user, api_client):
        from tests.factories import ListingFactory
        from unittest.mock import MagicMock
        listing = ListingFactory(owner=owner_user, status='active')
        request = MagicMock()
        request.user = owner_user
        data = {
            'listing_id': str(listing.id),
            'start_date': str(date.today() + timedelta(days=5)),
            'end_date': str(date.today() + timedelta(days=10)),
            'duration_type': 'daily',
        }
        serializer = CreateBookingSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()

    def test_past_start_date_rejected(self, renter_user):
        from tests.factories import ListingFactory
        from unittest.mock import MagicMock
        listing = ListingFactory(status='active')
        request = MagicMock()
        request.user = renter_user
        data = {
            'listing_id': str(listing.id),
            'start_date': str(date.today() - timedelta(days=1)),
            'end_date': str(date.today() + timedelta(days=5)),
            'duration_type': 'daily',
        }
        serializer = CreateBookingSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()

    def test_end_before_start_rejected(self, renter_user):
        from tests.factories import ListingFactory
        from unittest.mock import MagicMock
        listing = ListingFactory(status='active')
        request = MagicMock()
        request.user = renter_user
        data = {
            'listing_id': str(listing.id),
            'start_date': str(date.today() + timedelta(days=10)),
            'end_date': str(date.today() + timedelta(days=5)),
            'duration_type': 'daily',
        }
        serializer = CreateBookingSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
```

**Create `bookings/tests/test_views.py`:**

```python
import pytest
from datetime import date, timedelta
from bookings.models import Booking, BookingStatus


@pytest.mark.django_db
class TestBookingListCreate:
    URL = '/api/v1/bookings/'

    def test_unauthenticated_cannot_list(self, api_client):
        response = api_client.get(self.URL)
        assert response.status_code == 401

    def test_renter_sees_own_bookings(self, auth_client, renter_user, owner_user):
        from tests.factories import ListingFactory, BookingFactory
        listing = ListingFactory(owner=owner_user)
        BookingFactory(renter=renter_user, owner=owner_user, listing=listing)
        response = auth_client.get(f'{self.URL}?role=renter')
        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_owner_sees_own_bookings(self, owner_client, owner_user, renter_user):
        from tests.factories import ListingFactory, BookingFactory
        listing = ListingFactory(owner=owner_user)
        BookingFactory(renter=renter_user, owner=owner_user, listing=listing)
        response = owner_client.get(f'{self.URL}?role=owner')
        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_response_is_paginated(self, auth_client):
        response = auth_client.get(self.URL)
        assert 'count' in response.data
        assert 'results' in response.data

    def test_filter_by_status(self, owner_client, owner_user, renter_user):
        from tests.factories import ListingFactory, BookingFactory
        listing = ListingFactory(owner=owner_user)
        BookingFactory(renter=renter_user, owner=owner_user, listing=listing, status='pending')
        BookingFactory(renter=renter_user, owner=owner_user, listing=listing, status='confirmed')
        response = owner_client.get(f'{self.URL}?role=owner&status=pending')
        assert response.data['count'] == 1

    def test_filter_by_listing_id(self, owner_client, owner_user, renter_user):
        from tests.factories import ListingFactory, BookingFactory
        listing1 = ListingFactory(owner=owner_user)
        listing2 = ListingFactory(owner=owner_user)
        BookingFactory(renter=renter_user, owner=owner_user, listing=listing1)
        BookingFactory(renter=renter_user, owner=owner_user, listing=listing2)
        response = owner_client.get(f'{self.URL}?role=owner&listing_id={listing1.id}')
        assert response.data['count'] == 1

    def test_non_renter_cannot_create_booking(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        other_listing = ListingFactory()
        response = owner_client.post(self.URL, {
            'listing_id': str(other_listing.id),
            'start_date': str(date.today() + timedelta(days=5)),
            'end_date': str(date.today() + timedelta(days=10)),
            'duration_type': 'daily',
        }, format='json')
        assert response.status_code == 403

    def test_renter_can_create_booking(self, auth_client, renter_user, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, status='active', price_daily=50000)
        response = auth_client.post(self.URL, {
            'listing_id': str(listing.id),
            'start_date': str(date.today() + timedelta(days=5)),
            'end_date': str(date.today() + timedelta(days=10)),
            'duration_type': 'daily',
        }, format='json')
        assert response.status_code == 201
        assert response.data['data']['status'] == 'pending'

    def test_booking_creates_thread_automatically(self, auth_client, owner_user):
        from tests.factories import ListingFactory
        from messaging.models import Thread
        listing = ListingFactory(owner=owner_user, status='active', price_daily=50000)
        response = auth_client.post(self.URL, {
            'listing_id': str(listing.id),
            'start_date': str(date.today() + timedelta(days=5)),
            'end_date': str(date.today() + timedelta(days=10)),
            'duration_type': 'daily',
        }, format='json')
        assert response.status_code == 201
        booking_id = response.data['data']['id']
        assert Thread.objects.filter(booking__id=booking_id).exists()

    def test_booking_response_includes_thread_id(self, auth_client, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, status='active', price_daily=50000)
        response = auth_client.post(self.URL, {
            'listing_id': str(listing.id),
            'start_date': str(date.today() + timedelta(days=5)),
            'end_date': str(date.today() + timedelta(days=10)),
            'duration_type': 'daily',
        }, format='json')
        assert 'thread_id' in response.data['data']
        assert response.data['data']['thread_id'] is not None

    def test_cannot_book_unavailable_listing(self, auth_client, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, status='active', is_available=False)
        response = auth_client.post(self.URL, {
            'listing_id': str(listing.id),
            'start_date': str(date.today() + timedelta(days=5)),
            'end_date': str(date.today() + timedelta(days=10)),
            'duration_type': 'daily',
        }, format='json')
        assert response.status_code == 400

    def test_cannot_book_own_listing(self, dual_client, dual_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=dual_user, status='active', price_daily=50000)
        response = dual_client.post(self.URL, {
            'listing_id': str(listing.id),
            'start_date': str(date.today() + timedelta(days=5)),
            'end_date': str(date.today() + timedelta(days=10)),
            'duration_type': 'daily',
        }, format='json')
        assert response.status_code == 400

    def test_date_conflict_prevents_booking(self, auth_client, owner_user, renter_user):
        from tests.factories import ListingFactory, ConfirmedBookingFactory
        listing = ListingFactory(owner=owner_user, status='active', price_daily=50000)
        start = date.today() + timedelta(days=5)
        end = date.today() + timedelta(days=15)
        ConfirmedBookingFactory(
            renter=renter_user,
            owner=owner_user,
            listing=listing,
            start_date=start,
            end_date=end,
        )
        response = auth_client.post(self.URL, {
            'listing_id': str(listing.id),
            'start_date': str(start + timedelta(days=2)),
            'end_date': str(end - timedelta(days=2)),
            'duration_type': 'daily',
        }, format='json')
        assert response.status_code == 400

    def test_pending_booking_does_not_block_new_request(
        self, auth_client, owner_user, renter_user, create_user
    ):
        from tests.factories import ListingFactory, BookingFactory
        listing = ListingFactory(owner=owner_user, status='active', price_daily=50000)
        start = date.today() + timedelta(days=5)
        end = date.today() + timedelta(days=15)
        BookingFactory(
            renter=renter_user,
            owner=owner_user,
            listing=listing,
            start_date=start,
            end_date=end,
            status='pending',
        )
        second_renter = create_user(email='renter2@conflict.com', phone='08011119999')
        from rest_framework.test import APIClient
        client2 = APIClient()
        client2.force_authenticate(user=second_renter)
        response = client2.post('/api/v1/bookings/', {
            'listing_id': str(listing.id),
            'start_date': str(start + timedelta(days=2)),
            'end_date': str(end - timedelta(days=2)),
            'duration_type': 'daily',
        }, format='json')
        assert response.status_code == 201


@pytest.mark.django_db
class TestBookingStateTransitions:
    def test_owner_can_accept_pending_booking(self, owner_client, owner_user, renter_user):
        from tests.factories import ListingFactory, BookingFactory
        listing = ListingFactory(owner=owner_user)
        booking = BookingFactory(
            renter=renter_user, owner=owner_user, listing=listing, status='pending'
        )
        response = owner_client.patch(f'/api/v1/bookings/{booking.id}/accept/')
        assert response.status_code == 200
        booking.refresh_from_db()
        assert booking.status == 'confirmed'

    def test_accepting_makes_listing_unavailable(self, owner_client, owner_user, renter_user):
        from tests.factories import ListingFactory, BookingFactory
        listing = ListingFactory(owner=owner_user, is_available=True)
        booking = BookingFactory(
            renter=renter_user, owner=owner_user, listing=listing, status='pending'
        )
        owner_client.patch(f'/api/v1/bookings/{booking.id}/accept/')
        listing.refresh_from_db()
        assert listing.is_available is False

    def test_renter_cannot_accept_booking(self, auth_client, owner_user, renter_user):
        from tests.factories import ListingFactory, BookingFactory
        listing = ListingFactory(owner=owner_user)
        booking = BookingFactory(
            renter=renter_user, owner=owner_user, listing=listing, status='pending'
        )
        response = auth_client.patch(f'/api/v1/bookings/{booking.id}/accept/')
        assert response.status_code == 404

    def test_cannot_accept_confirmed_booking(self, owner_client, owner_user, renter_user):
        from tests.factories import ListingFactory, ConfirmedBookingFactory
        listing = ListingFactory(owner=owner_user)
        booking = ConfirmedBookingFactory(
            renter=renter_user, owner=owner_user, listing=listing
        )
        response = owner_client.patch(f'/api/v1/bookings/{booking.id}/accept/')
        assert response.status_code == 400

    def test_owner_can_decline_pending_booking(self, owner_client, owner_user, renter_user):
        from tests.factories import ListingFactory, BookingFactory
        listing = ListingFactory(owner=owner_user)
        booking = BookingFactory(
            renter=renter_user, owner=owner_user, listing=listing, status='pending'
        )
        response = owner_client.patch(
            f'/api/v1/bookings/{booking.id}/decline/',
            {'reason': 'Not available'},
        )
        assert response.status_code == 200
        booking.refresh_from_db()
        assert booking.status == 'declined'

    def test_renter_can_cancel_confirmed_booking(self, auth_client, owner_user, renter_user):
        from tests.factories import ListingFactory, ConfirmedBookingFactory
        listing = ListingFactory(owner=owner_user)
        booking = ConfirmedBookingFactory(
            renter=renter_user, owner=owner_user, listing=listing
        )
        response = auth_client.patch(
            f'/api/v1/bookings/{booking.id}/cancel/',
            {'reason': 'Plans changed'},
        )
        assert response.status_code == 200
        booking.refresh_from_db()
        assert booking.status == 'cancelled'

    def test_cancelling_restores_listing_availability(
        self, auth_client, owner_client, owner_user, renter_user
    ):
        from tests.factories import ListingFactory, ConfirmedBookingFactory
        listing = ListingFactory(owner=owner_user, is_available=False)
        booking = ConfirmedBookingFactory(
            renter=renter_user, owner=owner_user, listing=listing
        )
        auth_client.patch(f'/api/v1/bookings/{booking.id}/cancel/')
        listing.refresh_from_db()
        assert listing.is_available is True

    def test_mark_as_paid_simulated(self, auth_client, owner_user, renter_user, capsys):
        from tests.factories import ListingFactory, ConfirmedBookingFactory
        listing = ListingFactory(owner=owner_user)
        booking = ConfirmedBookingFactory(
            renter=renter_user, owner=owner_user, listing=listing
        )
        response = auth_client.patch(f'/api/v1/bookings/{booking.id}/pay/')
        assert response.status_code == 200
        booking.refresh_from_db()
        assert booking.payment_status == 'simulated_paid'
        captured = capsys.readouterr()
        assert '[DEV PAYMENT]' in captured.out

    def test_cannot_pay_pending_booking(self, auth_client, owner_user, renter_user):
        from tests.factories import ListingFactory, BookingFactory
        listing = ListingFactory(owner=owner_user)
        booking = BookingFactory(
            renter=renter_user, owner=owner_user, listing=listing, status='pending'
        )
        response = auth_client.patch(f'/api/v1/bookings/{booking.id}/pay/')
        assert response.status_code == 400

    def test_non_participant_cannot_view_booking(self, api_client, create_user, owner_user, renter_user):
        from tests.factories import ListingFactory, BookingFactory
        listing = ListingFactory(owner=owner_user)
        booking = BookingFactory(
            renter=renter_user, owner=owner_user, listing=listing
        )
        stranger = create_user(email='stranger@test.com', phone='08088888881')
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=stranger)
        response = client.get(f'/api/v1/bookings/{booking.id}/')
        assert response.status_code == 403
```

---

## Step 2: Create messaging app tests

**Create `messaging/tests/__init__.py`** (empty)

**Create `messaging/tests/test_models.py`:**

```python
import pytest
from messaging.models import Thread, Message


@pytest.mark.django_db
class TestThreadModel:
    def test_thread_str_with_booking(self, owner_user, renter_user):
        from tests.factories import ListingFactory, BookingFactory
        listing = ListingFactory(owner=owner_user)
        booking = BookingFactory(renter=renter_user, owner=owner_user, listing=listing)
        thread = Thread.objects.create(listing=listing, booking=booking)
        thread.participants.add(owner_user, renter_user)
        assert 'Booking' in str(thread)

    def test_thread_str_with_listing(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        thread = Thread.objects.create(listing=listing)
        assert 'Inquiry' in str(thread)

    def test_is_booking_thread_property(self, owner_user, renter_user):
        from tests.factories import ListingFactory, BookingFactory
        listing = ListingFactory(owner=owner_user)
        booking = BookingFactory(renter=renter_user, owner=owner_user, listing=listing)
        booking_thread = Thread.objects.create(listing=listing, booking=booking)
        inquiry_thread = Thread.objects.create(listing=listing)
        assert booking_thread.is_booking_thread is True
        assert inquiry_thread.is_booking_thread is False

    def test_get_other_participant(self, owner_user, renter_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        thread = Thread.objects.create(listing=listing)
        thread.participants.add(owner_user, renter_user)
        other = thread.get_other_participant(owner_user)
        assert other == renter_user


@pytest.mark.django_db
class TestMessagingServices:
    def test_get_or_create_booking_thread(self, owner_user, renter_user):
        from tests.factories import ListingFactory, BookingFactory
        from messaging.services import get_or_create_booking_thread
        listing = ListingFactory(owner=owner_user)
        booking = BookingFactory(renter=renter_user, owner=owner_user, listing=listing)
        thread, created = get_or_create_booking_thread(booking), None
        if isinstance(thread, tuple):
            thread, created = thread
        assert thread is not None
        assert owner_user in thread.participants.all()
        assert renter_user in thread.participants.all()

    def test_get_or_create_booking_thread_idempotent(self, owner_user, renter_user):
        from tests.factories import ListingFactory, BookingFactory
        from messaging.services import get_or_create_booking_thread
        listing = ListingFactory(owner=owner_user)
        booking = BookingFactory(renter=renter_user, owner=owner_user, listing=listing)
        t1 = get_or_create_booking_thread(booking)
        t2 = get_or_create_booking_thread(booking)
        if isinstance(t1, tuple):
            t1 = t1[0]
        if isinstance(t2, tuple):
            t2 = t2[0]
        assert t1.id == t2.id

    def test_publish_to_ably_without_key_prints_to_console(self, capsys):
        from messaging.services import publish_to_ably
        import uuid
        publish_to_ably(str(uuid.uuid4()), {'body': 'Test message'})
        captured = capsys.readouterr()
        assert '[DEV ABLY]' in captured.out

    def test_inquiry_thread_created_for_different_renters(
        self, owner_user, renter_user, create_user
    ):
        from tests.factories import ListingFactory
        from messaging.services import get_or_create_inquiry_thread
        listing = ListingFactory(owner=owner_user)
        renter2 = create_user(email='renter2@msg.com', phone='08066662222')
        t1, c1 = get_or_create_inquiry_thread(listing, renter_user)
        t2, c2 = get_or_create_inquiry_thread(listing, renter2)
        assert t1.id != t2.id
        assert c1 is True
        assert c2 is True

    def test_inquiry_thread_reused_for_same_renter(self, owner_user, renter_user):
        from tests.factories import ListingFactory
        from messaging.services import get_or_create_inquiry_thread
        listing = ListingFactory(owner=owner_user)
        t1, c1 = get_or_create_inquiry_thread(listing, renter_user)
        t2, c2 = get_or_create_inquiry_thread(listing, renter_user)
        assert t1.id == t2.id
        assert c2 is False
```

**Create `messaging/tests/test_views.py`:**

```python
import pytest
from messaging.models import Thread, Message


@pytest.mark.django_db
class TestThreadListCreate:
    URL = '/api/v1/threads/'

    def test_unauthenticated_cannot_list(self, api_client):
        response = api_client.get(self.URL)
        assert response.status_code == 401

    def test_user_sees_only_own_threads(self, auth_client, renter_user, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        thread = Thread.objects.create(listing=listing)
        thread.participants.add(renter_user, owner_user)

        unrelated_listing = ListingFactory()
        unrelated_thread = Thread.objects.create(listing=unrelated_listing)

        response = auth_client.get(self.URL)
        ids = [t['id'] for t in response.data['results']]
        assert str(thread.id) in ids
        assert str(unrelated_thread.id) not in ids

    def test_response_is_paginated(self, auth_client):
        response = auth_client.get(self.URL)
        assert 'count' in response.data
        assert 'results' in response.data

    def test_filter_by_thread_type_booking(self, auth_client, renter_user, owner_user):
        from tests.factories import ListingFactory, BookingFactory
        listing = ListingFactory(owner=owner_user)
        booking = BookingFactory(renter=renter_user, owner=owner_user, listing=listing)

        booking_thread = Thread.objects.create(listing=listing, booking=booking)
        booking_thread.participants.add(renter_user, owner_user)

        inquiry_thread = Thread.objects.create(listing=listing)
        inquiry_thread.participants.add(renter_user, owner_user)

        response = auth_client.get(f'{self.URL}?thread_type=booking')
        ids = [t['id'] for t in response.data['results']]
        assert str(booking_thread.id) in ids
        assert str(inquiry_thread.id) not in ids

    def test_filter_unread_returns_only_unread_threads(
        self, auth_client, renter_user, owner_user
    ):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)

        thread_with_unread = Thread.objects.create(listing=listing)
        thread_with_unread.participants.add(renter_user, owner_user)
        Message.objects.create(
            thread=thread_with_unread, sender=owner_user, body='Unread msg', is_read=False
        )

        thread_all_read = Thread.objects.create(listing=listing)
        thread_all_read.participants.add(renter_user, owner_user)
        Message.objects.create(
            thread=thread_all_read, sender=owner_user, body='Read msg', is_read=True
        )

        response = auth_client.get(f'{self.URL}?unread=true')
        ids = [t['id'] for t in response.data['results']]
        assert str(thread_with_unread.id) in ids
        assert str(thread_all_read.id) not in ids

    def test_create_inquiry_thread(self, auth_client, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, status='active')
        response = auth_client.post(self.URL, {
            'listing_id': str(listing.id),
            'initial_message': 'Is this available next week?',
        }, format='json')
        assert response.status_code == 201

    def test_cannot_send_inquiry_to_own_listing(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, status='active')
        response = owner_client.post(self.URL, {
            'listing_id': str(listing.id),
            'initial_message': 'Testing',
        }, format='json')
        assert response.status_code == 400


@pytest.mark.django_db
class TestThreadDetail:
    def test_participant_can_view_thread(self, auth_client, renter_user, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        thread = Thread.objects.create(listing=listing)
        thread.participants.add(renter_user, owner_user)
        response = auth_client.get(f'/api/v1/threads/{thread.id}/')
        assert response.status_code == 200
        assert 'messages' in response.data

    def test_non_participant_cannot_view_thread(self, auth_client, create_user, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        thread = Thread.objects.create(listing=listing)
        stranger = create_user(email='stranger2@msg.com', phone='08066663333')
        thread.participants.add(owner_user, stranger)
        response = auth_client.get(f'/api/v1/threads/{thread.id}/')
        assert response.status_code == 404

    def test_viewing_thread_marks_messages_read(
        self, auth_client, renter_user, owner_user
    ):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        thread = Thread.objects.create(listing=listing)
        thread.participants.add(renter_user, owner_user)
        Message.objects.create(
            thread=thread, sender=owner_user, body='Hello', is_read=False
        )
        auth_client.get(f'/api/v1/threads/{thread.id}/')
        assert Message.objects.filter(thread=thread, is_read=False, sender=owner_user).count() == 0


@pytest.mark.django_db
class TestSendMessage:
    def test_participant_can_send_message(self, auth_client, renter_user, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        thread = Thread.objects.create(listing=listing)
        thread.participants.add(renter_user, owner_user)
        response = auth_client.post(
            f'/api/v1/threads/{thread.id}/messages/',
            {'body': 'Hello, is this available?'},
        )
        assert response.status_code == 201
        assert response.data['data']['body'] == 'Hello, is this available?'

    def test_non_participant_cannot_send(self, auth_client, create_user, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        thread = Thread.objects.create(listing=listing)
        stranger = create_user(email='stranger3@msg.com', phone='08066664444')
        thread.participants.add(owner_user, stranger)
        response = auth_client.post(
            f'/api/v1/threads/{thread.id}/messages/',
            {'body': 'Hacking message'},
        )
        assert response.status_code == 404

    def test_empty_message_rejected(self, auth_client, renter_user, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        thread = Thread.objects.create(listing=listing)
        thread.participants.add(renter_user, owner_user)
        response = auth_client.post(
            f'/api/v1/threads/{thread.id}/messages/',
            {'body': ''},
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestMarkThreadRead:
    def test_marks_all_messages_read(self, auth_client, renter_user, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        thread = Thread.objects.create(listing=listing)
        thread.participants.add(renter_user, owner_user)
        Message.objects.create(thread=thread, sender=owner_user, body='msg1', is_read=False)
        Message.objects.create(thread=thread, sender=owner_user, body='msg2', is_read=False)
        response = auth_client.patch(f'/api/v1/threads/{thread.id}/read/')
        assert response.status_code == 200
        assert response.data['messages_marked_read'] == 2

    def test_does_not_mark_own_messages_read(self, auth_client, renter_user, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        thread = Thread.objects.create(listing=listing)
        thread.participants.add(renter_user, owner_user)
        Message.objects.create(thread=thread, sender=renter_user, body='own msg', is_read=False)
        response = auth_client.patch(f'/api/v1/threads/{thread.id}/read/')
        assert response.data['messages_marked_read'] == 0
```

---

## Step 3: Create owner app tests

**Create `owner/tests/__init__.py`** (empty)

**Create `owner/tests/test_views.py`:**

```python
import pytest
from datetime import date, timedelta
from decimal import Decimal
from bookings.models import BookingStatus


@pytest.mark.django_db
class TestOwnerDashboard:
    URL = '/api/v1/owner/dashboard/'

    def test_non_owner_gets_403(self, auth_client):
        response = auth_client.get(self.URL)
        assert response.status_code == 403

    def test_unauthenticated_gets_401(self, api_client):
        response = api_client.get(self.URL)
        assert response.status_code == 401

    def test_dashboard_returns_all_stat_keys(self, owner_client):
        response = owner_client.get(self.URL)
        assert response.status_code == 200
        stats = response.data['data']['stats']
        assert 'total_listings' in stats
        assert 'active_listings' in stats
        assert 'pending_booking_requests' in stats
        assert 'active_bookings' in stats
        assert 'unread_messages' in stats
        assert 'revenue_this_month' in stats

    def test_pending_requests_limited_to_5(self, owner_client, owner_user, renter_user):
        from tests.factories import ListingFactory, BookingFactory
        listing = ListingFactory(owner=owner_user)
        for _ in range(7):
            BookingFactory(renter=renter_user, owner=owner_user, listing=listing, status='pending')
        response = owner_client.get(self.URL)
        assert len(response.data['data']['pending_requests']) <= 5

    def test_pending_count_matches_actual(self, owner_client, owner_user, renter_user):
        from tests.factories import ListingFactory, BookingFactory
        listing = ListingFactory(owner=owner_user)
        BookingFactory(renter=renter_user, owner=owner_user, listing=listing, status='pending')
        BookingFactory(renter=renter_user, owner=owner_user, listing=listing, status='pending')
        BookingFactory(renter=renter_user, owner=owner_user, listing=listing, status='confirmed')
        response = owner_client.get(self.URL)
        assert response.data['data']['stats']['pending_booking_requests'] == 2

    def test_active_listings_count(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        ListingFactory(owner=owner_user, status='active')
        ListingFactory(owner=owner_user, status='active')
        ListingFactory(owner=owner_user, status='draft')
        response = owner_client.get(self.URL)
        assert response.data['data']['stats']['active_listings'] == 2


@pytest.mark.django_db
class TestBookingCalendar:
    URL = '/api/v1/owner/bookings/calendar/'

    def test_requires_start_and_end_date(self, owner_client):
        response = owner_client.get(self.URL)
        assert response.status_code == 400

    def test_rejects_range_over_90_days(self, owner_client):
        response = owner_client.get(
            f'{self.URL}?start_date=2026-01-01&end_date=2026-12-31'
        )
        assert response.status_code == 400

    def test_rejects_end_before_start(self, owner_client):
        response = owner_client.get(
            f'{self.URL}?start_date=2026-07-31&end_date=2026-07-01'
        )
        assert response.status_code == 400

    def test_returns_listings_with_bookings(self, owner_client, owner_user, renter_user):
        from tests.factories import ListingFactory, ConfirmedBookingFactory
        listing = ListingFactory(owner=owner_user, status='active')
        start = date(2026, 7, 1)
        end = date(2026, 7, 10)
        ConfirmedBookingFactory(
            renter=renter_user, owner=owner_user, listing=listing,
            start_date=start, end_date=end,
        )
        response = owner_client.get(
            f'{self.URL}?start_date=2026-07-01&end_date=2026-07-31'
        )
        assert response.status_code == 200
        assert response.data['listing_count'] >= 1
        listing_data = next(
            (l for l in response.data['data'] if str(l['id']) == str(listing.id)), None
        )
        assert listing_data is not None
        assert len(listing_data['bookings']) == 1

    def test_listings_outside_range_have_empty_bookings(
        self, owner_client, owner_user, renter_user
    ):
        from tests.factories import ListingFactory, ConfirmedBookingFactory
        listing = ListingFactory(owner=owner_user, status='active')
        ConfirmedBookingFactory(
            renter=renter_user, owner=owner_user, listing=listing,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 10),
        )
        response = owner_client.get(
            f'{self.URL}?start_date=2026-07-01&end_date=2026-07-31'
        )
        listing_data = next(
            (l for l in response.data['data'] if str(l['id']) == str(listing.id)), None
        )
        if listing_data:
            assert len(listing_data['bookings']) == 0

    def test_non_owner_gets_403(self, auth_client):
        response = auth_client.get(
            f'{self.URL}?start_date=2026-07-01&end_date=2026-07-31'
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestAnalyticsRevenue:
    URL = '/api/v1/owner/analytics/revenue/'

    def test_non_owner_gets_403(self, auth_client):
        response = auth_client.get(self.URL)
        assert response.status_code == 403

    def test_returns_required_keys(self, owner_client):
        response = owner_client.get(self.URL)
        assert response.status_code == 200
        data = response.data['data']
        assert 'gross_total' in data
        assert 'commission_total' in data
        assert 'payout_total' in data
        assert 'booking_count' in data
        assert 'avg_booking_value' in data
        assert 'by_listing' in data
        assert 'monthly_trend' in data

    def test_zero_revenue_when_no_bookings(self, owner_client):
        response = owner_client.get(self.URL)
        assert response.data['data']['gross_total'] == '0.00'
        assert response.data['data']['booking_count'] == 0

    def test_revenue_includes_confirmed_bookings(self, owner_client, owner_user, renter_user):
        from tests.factories import ListingFactory, ConfirmedBookingFactory
        listing = ListingFactory(owner=owner_user)
        ConfirmedBookingFactory(
            renter=renter_user, owner=owner_user, listing=listing,
            gross_amount=Decimal('100000'),
            commission_amount=Decimal('10000'),
            owner_payout_amount=Decimal('90000'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5),
        )
        response = owner_client.get(f'{self.URL}?period=all')
        assert Decimal(response.data['data']['gross_total']) == Decimal('100000')

    def test_cancelled_bookings_excluded(self, owner_client, owner_user, renter_user):
        from tests.factories import ListingFactory, BookingFactory
        listing = ListingFactory(owner=owner_user)
        BookingFactory(
            renter=renter_user, owner=owner_user, listing=listing,
            gross_amount=Decimal('100000'),
            status='cancelled',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5),
        )
        response = owner_client.get(f'{self.URL}?period=all')
        assert Decimal(response.data['data']['gross_total']) == Decimal('0.00')

    def test_period_month_filter(self, owner_client):
        response = owner_client.get(
            f'{self.URL}?period=month&year=2026&month=5'
        )
        assert response.status_code == 200
        assert response.data['period_label'] == 'May 2026'

    def test_period_all(self, owner_client):
        response = owner_client.get(f'{self.URL}?period=all')
        assert response.status_code == 200
        assert response.data['period_label'] == 'All Time'


@pytest.mark.django_db
class TestAnalyticsPerformance:
    URL = '/api/v1/owner/analytics/performance/'

    def test_non_owner_gets_403(self, auth_client):
        response = auth_client.get(self.URL)
        assert response.status_code == 403

    def test_returns_required_keys(self, owner_client):
        response = owner_client.get(self.URL)
        assert response.status_code == 200
        data = response.data['data']
        assert 'total_views' in data
        assert 'total_inquiries' in data
        assert 'total_booking_requests' in data
        assert 'total_confirmed' in data
        assert 'overall_conversion_rate' in data
        assert 'by_listing' in data

    def test_occupancy_rate_between_0_and_100(self, owner_client, owner_user, renter_user):
        from tests.factories import ListingFactory, ConfirmedBookingFactory
        listing = ListingFactory(owner=owner_user, status='active')
        ConfirmedBookingFactory(
            renter=renter_user, owner=owner_user, listing=listing,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() - timedelta(days=5),
        )
        response = owner_client.get(self.URL)
        for item in response.data['data']['by_listing']:
            assert 0 <= item['occupancy_rate'] <= 100


@pytest.mark.django_db
class TestListingStats:
    def test_owner_gets_own_listing_stats(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, view_count=42)
        response = owner_client.get(f'/api/v1/owner/listings/{listing.id}/stats/')
        assert response.status_code == 200
        assert response.data['data']['view_count'] == 42

    def test_cannot_get_stats_for_another_owners_listing(
        self, second_owner_client, owner_user
    ):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        response = second_owner_client.get(
            f'/api/v1/owner/listings/{listing.id}/stats/'
        )
        assert response.status_code == 404

    def test_stats_include_all_required_fields(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        response = owner_client.get(f'/api/v1/owner/listings/{listing.id}/stats/')
        data = response.data['data']
        required_fields = [
            'view_count', 'inquiry_count', 'booking_request_count',
            'confirmed_booking_count', 'conversion_rate', 'occupancy_rate_90d',
            'total_gross_revenue', 'total_payout',
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


@pytest.mark.django_db
class TestDuplicateListing:
    def test_duplicate_creates_draft_copy(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        from listings.models import Listing
        listing = ListingFactory(owner=owner_user, status='active', title='Original Crane')
        response = owner_client.post(
            f'/api/v1/owner/listings/{listing.id}/duplicate/'
        )
        assert response.status_code == 201
        assert response.data['data']['status'] == 'draft'
        assert 'Copy' in response.data['data']['title']
        assert Listing.objects.filter(owner=owner_user).count() == 2

    def test_duplicate_resets_view_count(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, view_count=150)
        response = owner_client.post(
            f'/api/v1/owner/listings/{listing.id}/duplicate/'
        )
        assert response.data['data']['view_count'] == 0

    def test_cannot_duplicate_another_owners_listing(
        self, second_owner_client, owner_user
    ):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        response = second_owner_client.post(
            f'/api/v1/owner/listings/{listing.id}/duplicate/'
        )
        assert response.status_code == 404

    def test_non_owner_cannot_duplicate(self, auth_client):
        from tests.factories import ListingFactory
        listing = ListingFactory()
        response = auth_client.post(
            f'/api/v1/owner/listings/{listing.id}/duplicate/'
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestBulkListingActions:
    URL = '/api/v1/owner/listings/bulk/'

    def test_non_owner_gets_403(self, auth_client):
        response = auth_client.post(self.URL, {'ids': [], 'action': 'pause'}, format='json')
        assert response.status_code == 403

    def test_empty_ids_returns_400(self, owner_client):
        response = owner_client.post(self.URL, {'ids': [], 'action': 'pause'}, format='json')
        assert response.status_code == 400

    def test_invalid_action_returns_400(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        response = owner_client.post(self.URL, {
            'ids': [str(listing.id)],
            'action': 'delete',
        }, format='json')
        assert response.status_code == 400

    def test_bulk_pause(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        from listings.models import Listing
        l1 = ListingFactory(owner=owner_user, status='active')
        l2 = ListingFactory(owner=owner_user, status='active')
        response = owner_client.post(self.URL, {
            'ids': [str(l1.id), str(l2.id)],
            'action': 'pause',
        }, format='json')
        assert response.status_code == 200
        l1.refresh_from_db()
        l2.refresh_from_db()
        assert l1.status == 'paused'
        assert l2.status == 'paused'

    def test_bulk_activate_skips_listings_without_location(
        self, owner_client, owner_user
    ):
        from tests.factories import ListingFactory
        from listings.models import Listing
        good = ListingFactory(owner=owner_user, status='draft')
        bad = ListingFactory(owner=owner_user, location=None, status='draft')
        response = owner_client.post(self.URL, {
            'ids': [str(good.id), str(bad.id)],
            'action': 'activate',
        }, format='json')
        assert response.status_code == 200
        good.refresh_from_db()
        bad.refresh_from_db()
        assert bad.status == 'draft'
        assert response.data['skipped'] == 1

    def test_cannot_action_more_than_50_listings(self, owner_client):
        import uuid
        ids = [str(uuid.uuid4()) for _ in range(51)]
        response = owner_client.post(self.URL, {
            'ids': ids,
            'action': 'pause',
        }, format='json')
        assert response.status_code == 400

    def test_ignores_other_owners_listings(self, owner_client, owner_user, second_owner_user):
        from tests.factories import ListingFactory
        own_listing = ListingFactory(owner=owner_user, status='active')
        other_listing = ListingFactory(owner=second_owner_user, status='active')
        response = owner_client.post(self.URL, {
            'ids': [str(own_listing.id), str(other_listing.id)],
            'action': 'pause',
        }, format='json')
        assert response.status_code == 200
        other_listing.refresh_from_db()
        assert other_listing.status == 'active'


@pytest.mark.django_db
class TestOwnerSettings:
    def test_non_owner_cannot_access_business_profile(self, auth_client):
        response = auth_client.get('/api/v1/owner/business-profile/')
        assert response.status_code == 403

    def test_owner_can_get_business_profile(self, owner_client):
        response = owner_client.get('/api/v1/owner/business-profile/')
        assert response.status_code == 200

    def test_owner_can_update_business_profile(self, owner_client):
        response = owner_client.patch('/api/v1/owner/business-profile/', {
            'business_name': 'Updated Company Ltd',
            'business_description': 'We lease heavy equipment.',
        })
        assert response.status_code == 200

    def test_bank_account_validation_10_digits(self, owner_client):
        response = owner_client.patch('/api/v1/owner/bank-account/', {
            'bank_name': 'GTBank',
            'bank_account_number': '123',
            'bank_account_name': 'Test User',
        })
        assert response.status_code == 400

    def test_bank_account_validation_digits_only(self, owner_client):
        response = owner_client.patch('/api/v1/owner/bank-account/', {
            'bank_name': 'GTBank',
            'bank_account_number': 'abcdefghij',
            'bank_account_name': 'Test User',
        })
        assert response.status_code == 400

    def test_valid_bank_account_update(self, owner_client):
        response = owner_client.patch('/api/v1/owner/bank-account/', {
            'bank_name': 'Zenith Bank',
            'bank_account_number': '2012345678',
            'bank_account_name': 'OWNER NAME',
        })
        assert response.status_code == 200

    def test_notification_preferences_update(self, owner_client):
        response = owner_client.patch('/api/v1/owner/notifications/', {
            'notify_new_booking_request': False,
            'notify_new_message': True,
        })
        assert response.status_code == 200

    def test_get_notifications_returns_all_preference_fields(self, owner_client):
        response = owner_client.get('/api/v1/owner/notifications/')
        data = response.data['data']
        assert 'notify_new_booking_request' in data
        assert 'notify_booking_confirmed' in data
        assert 'notify_new_message' in data
        assert 'notify_booking_cancelled' in data
```

---

## Step 4: Add missing factory to tests/factories.py

Open `tests/factories.py` and add this import at the top with the others, then add `ListingMediaFactory` to the factory list. **Append only — do not replace existing content:**

```python
from listings.models import ListingMedia
from django.core.files.uploadedfile import SimpleUploadedFile


class ListingMediaFactory(DjangoModelFactory):
    class Meta:
        model = ListingMedia

    listing = factory.SubFactory(ListingFactory)
    file = factory.LazyAttribute(
        lambda _: SimpleUploadedFile('photo.jpg', b'imgcontent', content_type='image/jpeg')
    )
    is_primary = False
    display_order = 0
```

Also update `ListingFactory` to produce listings with at least one media item when used in activation tests. Add this helper at the bottom of `tests/factories.py`:

```python
def make_publishable_listing(owner, **kwargs):
    """
    Creates a listing that satisfies all publish requirements:
    has a location and at least one photo.
    """
    listing = ListingFactory(
        owner=owner,
        status='draft',
        location=Point(3.3792, 6.5244, srid=4326),
        **kwargs,
    )
    ListingMediaFactory(listing=listing, is_primary=True)
    return listing
```

---

## Step 5: Run the full test suite

```bash
pytest --tb=short -v
```

All tests must pass. If any test fails, fix the underlying code or test before proceeding. Do not comment out failing tests.

Generate the coverage report:

```bash
pytest --cov=. --cov-report=html
```

This creates `htmlcov/index.html`. Open it and verify coverage for each app.

**Minimum coverage targets:**
- `accounts/` — 80%
- `listings/` — 80%
- `search/` — 85%
- `bookings/` — 85%
- `messaging/` — 80%
- `owner/` — 80%
- `core/` — 90%

---

## Step 6: Final commit

```bash
git add .
git commit -m "test: Wave 06 Part 2 — bookings, messaging, owner test suite complete"
git tag backend-tested-v1.0
git push origin main --tags
```

---

## Complete Definition of Done (Both Parts)

**Test infrastructure:**
- [ ] `pytest.ini` configured correctly
- [ ] `conftest.py` has all shared fixtures: `api_client`, `auth_client`, `owner_client`, `second_owner_client`, `dual_client`, `create_user`, `renter_user`, `owner_user`, `second_owner_user`, `dual_user`
- [ ] `tests/factories.py` has factories for all models: `UserFactory`, `OwnerUserFactory`, `RenterUserFactory`, `DualUserFactory`, `ListingFactory`, `WarehouseListingFactory`, `VehicleListingFactory`, `DraftListingFactory`, `ListingNoLocationFactory`, `BookingFactory`, `ConfirmedBookingFactory`, `ThreadFactory`, `MessageFactory`, `OwnerProfileFactory`, `ListingMediaFactory`

**Core tests:**
- [ ] `BaseModel` abstract, id, timestamps tested
- [ ] `IsOwnerRole`, `IsRenterRole`, `IsObjectOwner` — all branches tested
- [ ] `StandardPagination` config tested

**Accounts tests:**
- [ ] User model: email uniqueness, phone uniqueness, full_name, str, defaults
- [ ] OwnerProfile auto-created signal tested
- [ ] OTP generate, create, verify — all cases including expired and used
- [ ] KYC auto-approve simulation tested
- [ ] All auth endpoints: register, login, logout, verify phone, password reset
- [ ] JWT payload contains role fields
- [ ] User profile endpoints: get, update, role switch, public profile

**Listings tests:**
- [ ] Listing model: str, primary_photo_url, lat/lng properties
- [ ] ListingMedia: setting primary unsets others
- [ ] CreateListingSerializer: lat/lng → Point, no location, invalid type
- [ ] UpdateListingStatusSerializer: cannot activate without location or photos
- [ ] All listing endpoints with permission checks (owner vs renter vs public)
- [ ] View count increment tested
- [ ] Report: cannot report own, cannot report twice

**Search tests:**
- [ ] Missing lat/lng → 400
- [ ] Invalid coords → 400
- [ ] Results within radius include distance_km
- [ ] Results ordered by distance ascending
- [ ] Draft listings excluded
- [ ] Filter by resource_type works
- [ ] Unavailable listings excluded by default
- [ ] Unauthenticated users can search

**Bookings tests:**
- [ ] `calculate_booking_amounts`: daily, weekly, monthly, 10% commission, missing price error
- [ ] CreateBookingSerializer: cannot book own listing, past dates, end before start
- [ ] Booking creation creates thread automatically
- [ ] Booking response includes thread_id
- [ ] Date conflict detection: confirmed blocks, pending does NOT block
- [ ] All state transitions: accept, decline, cancel, mark paid
- [ ] Signal: accepting marks listing unavailable, cancelling restores availability
- [ ] `[DEV PAYMENT]` printed on mark paid
- [ ] Non-participant cannot view booking (403)

**Messaging tests:**
- [ ] Thread model str, is_booking_thread, get_other_participant
- [ ] Services: get_or_create_booking_thread idempotent, inquiry thread reused for same renter
- [ ] `[DEV ABLY]` printed when no key configured
- [ ] Thread list: only own threads, paginated, filtered by type and unread
- [ ] Cannot send inquiry to own listing
- [ ] Viewing thread marks messages read
- [ ] Non-participant cannot view or send (404)
- [ ] Empty message body rejected (400)
- [ ] Mark thread read does not mark own messages read

**Owner app tests:**
- [ ] Dashboard: 403 for non-owner, all stat keys present, pending count accurate
- [ ] Calendar: missing dates → 400, range > 90 days → 400, end before start → 400
- [ ] Revenue analytics: zero when no bookings, cancelled excluded, period filters work
- [ ] Performance analytics: occupancy rate between 0–100
- [ ] Listing stats: cannot view another owner's stats (404)
- [ ] Duplicate: creates draft, resets view_count, title has "Copy", cannot duplicate others' listings
- [ ] Bulk actions: empty ids → 400, > 50 ids → 400, invalid action → 400, activate skips no-location, ignores other owners' listings
- [ ] Settings: business profile CRUD, bank account 10-digit validation, notification preferences

**Coverage:**
- [ ] `accounts/` ≥ 80%
- [ ] `listings/` ≥ 80%
- [ ] `search/` ≥ 85%
- [ ] `bookings/` ≥ 85%
- [ ] `messaging/` ≥ 80%
- [ ] `owner/` ≥ 80%
- [ ] `core/` ≥ 90%

**Final:**
- [ ] `pytest` runs with **0 failures, 0 errors**
- [ ] Coverage report generated at `htmlcov/index.html`
- [ ] Tag `backend-tested-v1.0` created and pushed
- [ ] Git commit made with message `test: Wave 06 Part 2 — bookings, messaging, owner test suite complete`
