import pytest
from datetime import date, timedelta

from bookings.models import Booking, BookingStatus
from bookings.tasks import complete_expired_bookings


@pytest.mark.django_db
class TestBookingAutoComplete:
    def test_active_booking_past_end_date_is_completed(self, owner_user, renter_user):
        from tests.factories import BookingFactory
        booking = BookingFactory(
            owner=owner_user,
            renter=renter_user,
            status=BookingStatus.ACTIVE,
            start_date=date.today() - timedelta(days=14),
            end_date=date.today() - timedelta(days=1),
        )
        result = complete_expired_bookings()
        booking.refresh_from_db()
        assert booking.status == BookingStatus.COMPLETED
        assert result['completed_count'] == 1

    def test_confirmed_booking_past_end_date_is_completed(self, owner_user, renter_user):
        from tests.factories import BookingFactory
        booking = BookingFactory(
            owner=owner_user,
            renter=renter_user,
            status=BookingStatus.CONFIRMED,
            start_date=date.today() - timedelta(days=14),
            end_date=date.today() - timedelta(days=1),
        )
        result = complete_expired_bookings()
        booking.refresh_from_db()
        assert booking.status == BookingStatus.COMPLETED
        assert result['completed_count'] == 1

    def test_active_booking_future_end_date_not_completed(self, owner_user, renter_user):
        from tests.factories import BookingFactory
        booking = BookingFactory(
            owner=owner_user,
            renter=renter_user,
            status=BookingStatus.ACTIVE,
            start_date=date.today() - timedelta(days=3),
            end_date=date.today() + timedelta(days=4),
        )
        result = complete_expired_bookings()
        booking.refresh_from_db()
        assert booking.status == BookingStatus.ACTIVE
        assert result['completed_count'] == 0

    def test_pending_booking_past_end_date_not_completed(self, owner_user, renter_user):
        from tests.factories import BookingFactory
        booking = BookingFactory(
            owner=owner_user,
            renter=renter_user,
            status=BookingStatus.PENDING,
            start_date=date.today() - timedelta(days=14),
            end_date=date.today() - timedelta(days=1),
        )
        result = complete_expired_bookings()
        booking.refresh_from_db()
        assert booking.status == BookingStatus.PENDING
        assert result['completed_count'] == 0

    def test_multiple_expired_bookings(self, owner_user, renter_user):
        from tests.factories import BookingFactory
        for _ in range(5):
            BookingFactory(
                owner=owner_user,
                renter=renter_user,
                status=BookingStatus.ACTIVE,
                start_date=date.today() - timedelta(days=30),
                end_date=date.today() - timedelta(days=2),
            )
        BookingFactory(
            owner=owner_user,
            renter=renter_user,
            status=BookingStatus.ACTIVE,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )
        result = complete_expired_bookings()
        assert result['completed_count'] == 5
