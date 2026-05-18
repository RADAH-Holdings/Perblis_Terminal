import pytest
from datetime import date, timedelta
from decimal import Decimal
from bookings.serializers import calculate_booking_amounts, CreateBookingSerializer
from bookings.commission import (
    calculate_commission,
    get_commission_rate,
    FLAT_FEE_AMOUNT,
)


@pytest.mark.django_db
class TestCalculateBookingAmounts:
    def test_daily_calculation_equipment(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, resource_type='equipment', price_daily=50000)
        start = date.today() + timedelta(days=5)
        end = date.today() + timedelta(days=10)  # 5 days
        result = calculate_booking_amounts(listing, start, end, 'daily')
        assert result['gross_amount'] == Decimal('250000')
        # Equipment daily rate = 12%
        assert result['commission_amount'] == Decimal('30000.00')
        assert result['owner_payout_amount'] == Decimal('220000.00')
        assert result['commission_rate'] == Decimal('0.12')
        assert result['commission_rate_label'] == '12%'

    def test_daily_calculation_vehicle(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, resource_type='vehicle', price_daily=50000)
        start = date.today() + timedelta(days=5)
        end = date.today() + timedelta(days=10)  # 5 days
        result = calculate_booking_amounts(listing, start, end, 'daily')
        assert result['gross_amount'] == Decimal('250000')
        # Vehicle daily rate = 11%
        assert result['commission_amount'] == Decimal('27500.00')
        assert result['commission_rate'] == Decimal('0.11')
        assert result['commission_rate_label'] == '11%'

    def test_weekly_calculation_uses_ceil(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, resource_type='equipment', price_weekly=300000)
        start = date.today() + timedelta(days=5)
        end = start + timedelta(days=10)  # 10 days → ceil(10/7) = 2 weeks
        result = calculate_booking_amounts(listing, start, end, 'weekly')
        assert result['gross_amount'] == Decimal('600000')
        # Equipment weekly rate = 10%
        assert result['commission_amount'] == Decimal('60000.00')
        assert result['commission_rate'] == Decimal('0.10')
        assert result['commission_rate_label'] == '10%'

    def test_weekly_calculation_exact_week(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, resource_type='warehouse', price_weekly=200000)
        start = date.today() + timedelta(days=5)
        end = start + timedelta(days=7)  # exactly 7 days = 1 week
        result = calculate_booking_amounts(listing, start, end, 'weekly')
        assert result['gross_amount'] == Decimal('200000')
        # Warehouse weekly = 8%
        assert result['commission_amount'] == Decimal('16000.00')
        assert result['commission_rate_label'] == '8%'

    def test_monthly_calculation_uses_ceil_28(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, resource_type='equipment', price_monthly=1500000)
        start = date.today() + timedelta(days=5)
        end = start + timedelta(days=60)  # 60 days → ceil(60/28) = 3 months
        result = calculate_booking_amounts(listing, start, end, 'monthly')
        assert result['gross_amount'] == Decimal('4500000')
        # Equipment monthly = 8%
        assert result['commission_amount'] == Decimal('360000.00')
        assert result['commission_rate_label'] == '8%'

    def test_monthly_exact_28_days(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, resource_type='terminal', price_monthly=500000)
        start = date.today() + timedelta(days=5)
        end = start + timedelta(days=28)  # exactly 28 days = 1 month
        result = calculate_booking_amounts(listing, start, end, 'monthly')
        assert result['gross_amount'] == Decimal('500000')
        # Terminal monthly = 6%
        assert result['commission_amount'] == Decimal('30000.00')
        assert result['commission_rate_label'] == '6%'

    def test_flat_fee_below_threshold(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, resource_type='vehicle', price_daily=4000)
        start = date.today() + timedelta(days=5)
        end = start + timedelta(days=3)  # 3 days × ₦4,000 = ₦12,000 < ₦25,000
        result = calculate_booking_amounts(listing, start, end, 'daily')
        assert result['gross_amount'] == Decimal('12000')
        assert result['commission_amount'] == FLAT_FEE_AMOUNT
        assert result['commission_rate_label'] == '₦2,500 flat'
        assert result['commission_rate'] == Decimal('0')
        assert result['owner_payout_amount'] == Decimal('9500')

    def test_flat_fee_at_exact_threshold(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, resource_type='equipment', price_daily=25000)
        start = date.today() + timedelta(days=5)
        end = start + timedelta(days=1)  # 1 day × ₦25,000 = ₦25,000 (NOT below threshold)
        result = calculate_booking_amounts(listing, start, end, 'daily')
        # At exactly ₦25,000, percentage applies (not flat fee)
        assert result['gross_amount'] == Decimal('25000')
        assert result['commission_amount'] == Decimal('3000.00')  # 12%
        assert result['commission_rate_label'] == '12%'

    def test_payout_equals_gross_minus_commission(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, resource_type='facility', price_daily=75000)
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


class TestCommissionEngine:
    """Unit tests for the commission rate engine itself."""

    def test_equipment_daily_rate(self):
        assert get_commission_rate('equipment', 'daily') == Decimal('0.12')

    def test_equipment_weekly_rate(self):
        assert get_commission_rate('equipment', 'weekly') == Decimal('0.10')

    def test_equipment_monthly_rate(self):
        assert get_commission_rate('equipment', 'monthly') == Decimal('0.08')

    def test_vehicle_daily_rate(self):
        assert get_commission_rate('vehicle', 'daily') == Decimal('0.11')

    def test_vehicle_weekly_rate(self):
        assert get_commission_rate('vehicle', 'weekly') == Decimal('0.09')

    def test_vehicle_monthly_rate(self):
        assert get_commission_rate('vehicle', 'monthly') == Decimal('0.07')

    def test_warehouse_daily_rate(self):
        assert get_commission_rate('warehouse', 'daily') == Decimal('0.10')

    def test_warehouse_weekly_rate(self):
        assert get_commission_rate('warehouse', 'weekly') == Decimal('0.08')

    def test_warehouse_monthly_rate(self):
        assert get_commission_rate('warehouse', 'monthly') == Decimal('0.06')

    def test_terminal_daily_rate(self):
        assert get_commission_rate('terminal', 'daily') == Decimal('0.10')

    def test_facility_daily_rate(self):
        assert get_commission_rate('facility', 'daily') == Decimal('0.10')

    def test_unknown_resource_type_falls_back(self):
        assert get_commission_rate('unknown', 'daily') == Decimal('0.10')

    def test_flat_fee_for_small_transaction(self):
        amount, rate, label = calculate_commission(Decimal('18000'), 'equipment', 'daily')
        assert amount == Decimal('2500')
        assert rate == Decimal('0')
        assert label == '₦2,500 flat'

    def test_percentage_for_large_transaction(self):
        amount, rate, label = calculate_commission(Decimal('80000'), 'equipment', 'daily')
        assert amount == Decimal('9600.00')
        assert rate == Decimal('0.12')
        assert label == '12%'

    def test_fsd_example_truck_1day_18k(self):
        """FSD §4.3 example: Truck rental, 1 day, ₦18,000 → flat fee ₦2,500"""
        amount, rate, label = calculate_commission(Decimal('18000'), 'vehicle', 'daily')
        assert amount == Decimal('2500')
        assert label == '₦2,500 flat'

    def test_fsd_example_warehouse_1week_22k(self):
        """FSD §4.3 example: Small warehouse, 1 week, ₦22,000 → flat fee ₦2,500"""
        amount, rate, label = calculate_commission(Decimal('22000'), 'warehouse', 'weekly')
        assert amount == Decimal('2500')
        assert label == '₦2,500 flat'

    def test_fsd_example_excavator_1day_80k(self):
        """FSD §4.3 example: Excavator, 1 day, ₦80,000 → 12% = ₦9,600"""
        amount, rate, label = calculate_commission(Decimal('80000'), 'equipment', 'daily')
        assert amount == Decimal('9600.00')
        assert label == '12%'

    def test_fsd_example_warehouse_1month_350k(self):
        """FSD §4.3 example: Warehouse, 1 month, ₦350,000 → 6% = ₦21,000"""
        amount, rate, label = calculate_commission(Decimal('350000'), 'warehouse', 'monthly')
        assert amount == Decimal('21000.00')
        assert label == '6%'

    def test_fsd_example_container_1week_120k(self):
        """FSD §4.3 example: Container slot, 1 week, ₦120,000 → 8% = ₦9,600"""
        amount, rate, label = calculate_commission(Decimal('120000'), 'terminal', 'weekly')
        assert amount == Decimal('9600.00')
        assert label == '8%'


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
