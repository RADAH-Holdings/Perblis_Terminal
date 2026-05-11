# TERMINAL — WAVE 06: COMPREHENSIVE TESTING (Part 1 of 2)
> Agent task file. Execute every instruction in order. Do not skip steps.
> Wave 05 must be fully complete before starting this wave.
> Complete Part 1 fully before starting Part 2.
> Do not proceed to Wave 07 (Frontend) until both parts pass with 0 failures.

---

## Context

This wave adds a comprehensive test suite covering all six Django apps. Tests use **pytest** and **pytest-django**.

**Two types of tests per app:**
- **Unit tests** — model methods, serializer validation, service functions, permission classes, in isolation
- **Integration tests** — full request/response cycle through every API endpoint

**Every endpoint is tested for:**
- Happy path (correct response, correct data shape)
- Unauthenticated request (expect 401)
- Wrong role (expect 403)
- Not found (expect 404)
- Invalid input (expect 400)
- Permission boundary (cannot act on another user's resource)

---

## Step 1: Install test dependencies

Add to `requirements/development.txt`:

```
-r base.txt
pytest>=8.0
pytest-django>=4.8
pytest-cov>=5.0
factory-boy>=3.3
faker>=24.0
django-debug-toolbar>=4.3
```

Install:

```bash
pip install pytest pytest-django pytest-cov factory-boy faker
```

---

## Step 2: Create pytest configuration

**Create `pytest.ini` in the project root:**

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.development
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --tb=short
    -v
    --cov=.
    --cov-report=term-missing
    --cov-omit=*/migrations/*,*/admin.py,manage.py,scripts/*,config/settings/*
markers =
    unit: Unit tests (no database)
    integration: Integration tests (with database)
    slow: Tests that take more than 1 second
```

---

## Step 3: Create root conftest.py

**Create `conftest.py` in the project root:**

```python
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def _create_user(**kwargs):
        defaults = {
            'email': 'test@example.com',
            'phone': '08000000001',
            'first_name': 'Test',
            'last_name': 'User',
            'is_renter': True,
            'is_owner': False,
            'is_email_verified': True,
            'is_phone_verified': True,
        }
        defaults.update(kwargs)
        password = defaults.pop('password', 'testpass123!')
        user = User(**defaults)
        user.set_password(password)
        user.save()
        return user
    return _create_user


@pytest.fixture
def renter_user(create_user):
    return create_user(
        email='renter@test.com',
        phone='08011111111',
        is_renter=True,
        is_owner=False,
    )


@pytest.fixture
def owner_user(create_user):
    return create_user(
        email='owner@test.com',
        phone='08022222222',
        is_renter=False,
        is_owner=True,
    )


@pytest.fixture
def second_owner_user(create_user):
    return create_user(
        email='owner2@test.com',
        phone='08044444444',
        is_renter=False,
        is_owner=True,
    )


@pytest.fixture
def dual_user(create_user):
    return create_user(
        email='dual@test.com',
        phone='08033333333',
        is_renter=True,
        is_owner=True,
    )


@pytest.fixture
def auth_client(api_client, renter_user):
    api_client.force_authenticate(user=renter_user)
    return api_client


@pytest.fixture
def owner_client(api_client, owner_user):
    api_client.force_authenticate(user=owner_user)
    return api_client


@pytest.fixture
def second_owner_client(api_client, second_owner_user):
    api_client.force_authenticate(user=second_owner_user)
    return api_client


@pytest.fixture
def dual_client(api_client, dual_user):
    api_client.force_authenticate(user=dual_user)
    return api_client
```

---

## Step 4: Create test factories

**Create `tests/` directory in the project root:**

```bash
mkdir tests
touch tests/__init__.py
```

**Create `tests/factories.py`:**

```python
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from faker import Faker
import random

fake = Faker()
User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('email',)

    email = factory.LazyAttribute(lambda _: fake.unique.email())
    phone = factory.LazyAttribute(lambda _: f"080{random.randint(10000000, 99999999)}")
    first_name = factory.LazyAttribute(lambda _: fake.first_name())
    last_name = factory.LazyAttribute(lambda _: fake.last_name())
    is_renter = True
    is_owner = False
    is_email_verified = True
    is_phone_verified = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop('password', 'testpass123!')
        obj = super()._create(model_class, *args, **kwargs)
        obj.set_password(password)
        obj.save()
        return obj


class OwnerUserFactory(UserFactory):
    is_renter = False
    is_owner = True


class RenterUserFactory(UserFactory):
    is_renter = True
    is_owner = False


class DualUserFactory(UserFactory):
    is_renter = True
    is_owner = True


class ListingFactory(DjangoModelFactory):
    class Meta:
        model = 'listings.Listing'

    owner = factory.SubFactory(OwnerUserFactory)
    resource_type = 'equipment'
    title = factory.LazyAttribute(lambda _: f"{fake.word().title()} Equipment")
    description = factory.LazyAttribute(lambda _: fake.paragraph())
    category = 'Mobile Crane'
    price_daily = factory.LazyAttribute(lambda _: random.randint(20000, 100000))
    price_weekly = factory.LazyAttribute(lambda _: random.randint(100000, 500000))
    price_monthly = factory.LazyAttribute(lambda _: random.randint(400000, 2000000))
    specs = factory.LazyAttribute(lambda _: {'tonnage': 50, 'fuel_type': 'diesel'})
    # Lagos coordinates with slight randomisation
    location = factory.LazyAttribute(
        lambda _: Point(
            3.3792 + random.uniform(-0.05, 0.05),
            6.5244 + random.uniform(-0.05, 0.05),
            srid=4326,
        )
    )
    location_address = factory.LazyAttribute(lambda _: fake.street_address())
    location_city = 'Lagos'
    status = 'active'
    is_available = True
    verification_tier = 'basic'


class WarehouseListingFactory(ListingFactory):
    resource_type = 'warehouse'
    category = 'General Warehouse'
    specs = {'floor_area_sqm': 2000, 'height_clearance_m': 8, 'loading_bays': 2}


class VehicleListingFactory(ListingFactory):
    resource_type = 'vehicle'
    category = 'Flatbed Truck'
    specs = {'payload_tonnes': 20, 'axles': 3}


class DraftListingFactory(ListingFactory):
    status = 'draft'


class ListingNoLocationFactory(ListingFactory):
    location = None
    status = 'draft'


class BookingFactory(DjangoModelFactory):
    class Meta:
        model = 'bookings.Booking'

    renter = factory.SubFactory(RenterUserFactory)
    owner = factory.LazyAttribute(lambda obj: obj.listing.owner)
    listing = factory.SubFactory(ListingFactory)
    start_date = factory.LazyAttribute(
        lambda _: fake.future_date(end_date='+30d')
    )
    end_date = factory.LazyAttribute(
        lambda obj: fake.date_between(
            start_date=obj.start_date,
            end_date='+60d',
        )
    )
    duration_type = 'daily'
    gross_amount = factory.LazyAttribute(lambda _: random.randint(50000, 500000))
    commission_rate = 0.10
    commission_amount = factory.LazyAttribute(
        lambda obj: round(float(obj.gross_amount) * 0.10, 2)
    )
    owner_payout_amount = factory.LazyAttribute(
        lambda obj: round(float(obj.gross_amount) * 0.90, 2)
    )
    status = 'pending'
    payment_status = 'unpaid'


class ConfirmedBookingFactory(BookingFactory):
    status = 'confirmed'


class ThreadFactory(DjangoModelFactory):
    class Meta:
        model = 'messaging.Thread'

    listing = factory.SubFactory(ListingFactory)


class MessageFactory(DjangoModelFactory):
    class Meta:
        model = 'messaging.Message'

    thread = factory.SubFactory(ThreadFactory)
    sender = factory.SubFactory(UserFactory)
    body = factory.LazyAttribute(lambda _: fake.sentence())
    is_read = False


class OwnerProfileFactory(DjangoModelFactory):
    class Meta:
        model = 'accounts.OwnerProfile'
        django_get_or_create = ('user',)

    user = factory.SubFactory(OwnerUserFactory)
    business_name = factory.LazyAttribute(lambda _: f"{fake.company()} Ltd")
    bank_name = 'First Bank'
    bank_account_number = '3012345678'
    bank_account_name = factory.LazyAttribute(lambda _: fake.name().upper())
```

---

## Step 5: Create core app tests

**Create `core/tests/__init__.py`** (empty)

**Create `core/tests/test_models.py`:**

```python
import pytest
from core.models import BaseModel
from django.db import models


@pytest.mark.unit
class TestBaseModel:
    def test_base_model_is_abstract(self):
        assert BaseModel._meta.abstract is True

    def test_base_model_has_uuid_id(self):
        field = BaseModel._meta.get_field('id')
        assert field.primary_key is True
        assert field.editable is False

    def test_base_model_has_created_at(self):
        field = BaseModel._meta.get_field('created_at')
        assert field.auto_now_add is True

    def test_base_model_has_updated_at(self):
        field = BaseModel._meta.get_field('updated_at')
        assert field.auto_now is True
```

**Create `core/tests/test_permissions.py`:**

```python
import pytest
from unittest.mock import MagicMock
from core.permissions import IsOwnerRole, IsRenterRole, IsObjectOwner


@pytest.mark.unit
class TestIsOwnerRole:
    def setup_method(self):
        self.permission = IsOwnerRole()
        self.view = MagicMock()

    def _make_request(self, is_authenticated=True, is_owner=False):
        request = MagicMock()
        request.user.is_authenticated = is_authenticated
        request.user.is_owner = is_owner
        return request

    def test_allows_owner_user(self):
        request = self._make_request(is_authenticated=True, is_owner=True)
        assert self.permission.has_permission(request, self.view) is True

    def test_denies_non_owner(self):
        request = self._make_request(is_authenticated=True, is_owner=False)
        assert self.permission.has_permission(request, self.view) is False

    def test_denies_unauthenticated(self):
        request = self._make_request(is_authenticated=False, is_owner=False)
        assert self.permission.has_permission(request, self.view) is False


@pytest.mark.unit
class TestIsRenterRole:
    def setup_method(self):
        self.permission = IsRenterRole()
        self.view = MagicMock()

    def _make_request(self, is_authenticated=True, is_renter=False):
        request = MagicMock()
        request.user.is_authenticated = is_authenticated
        request.user.is_renter = is_renter
        return request

    def test_allows_renter_user(self):
        request = self._make_request(is_authenticated=True, is_renter=True)
        assert self.permission.has_permission(request, self.view) is True

    def test_denies_non_renter(self):
        request = self._make_request(is_authenticated=True, is_renter=False)
        assert self.permission.has_permission(request, self.view) is False

    def test_denies_unauthenticated(self):
        request = self._make_request(is_authenticated=False)
        assert self.permission.has_permission(request, self.view) is False


@pytest.mark.unit
class TestIsObjectOwner:
    def setup_method(self):
        self.permission = IsObjectOwner()
        self.view = MagicMock()

    def test_allows_object_owner(self):
        user = MagicMock()
        obj = MagicMock()
        obj.owner = user
        request = MagicMock()
        request.user = user
        assert self.permission.has_object_permission(request, self.view, obj) is True

    def test_denies_non_owner(self):
        user = MagicMock()
        other_user = MagicMock()
        obj = MagicMock()
        obj.owner = other_user
        request = MagicMock()
        request.user = user
        assert self.permission.has_object_permission(request, self.view, obj) is False
```

**Create `core/tests/test_pagination.py`:**

```python
import pytest
from core.pagination import StandardPagination


@pytest.mark.unit
class TestStandardPagination:
    def test_default_page_size(self):
        p = StandardPagination()
        assert p.page_size == 20

    def test_max_page_size(self):
        p = StandardPagination()
        assert p.max_page_size == 100

    def test_page_size_query_param(self):
        p = StandardPagination()
        assert p.page_size_query_param == 'page_size'
```

---

## Step 6: Create accounts app tests

**Create `accounts/tests/__init__.py`** (empty)

**Create `accounts/tests/test_models.py`:**

```python
import pytest
from django.contrib.auth import get_user_model
from accounts.models import OTPCode, UserDocument, OwnerProfile

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_user_uses_email_as_username(self):
        assert User.USERNAME_FIELD == 'email'

    def test_user_default_is_renter(self, create_user):
        user = create_user(email='newuser@test.com', phone='08077777771')
        assert user.is_renter is True
        assert user.is_owner is False

    def test_user_full_name(self, create_user):
        user = create_user(
            email='fullname@test.com',
            phone='08077777772',
            first_name='John',
            last_name='Doe',
        )
        assert user.full_name == 'John Doe'

    def test_user_str(self, create_user):
        user = create_user(
            email='str@test.com',
            phone='08077777773',
            first_name='Jane',
            last_name='Smith',
        )
        assert str(user) == 'Jane Smith <str@test.com>'

    def test_user_email_is_unique(self, create_user):
        create_user(email='unique@test.com', phone='08077777774')
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            create_user(email='unique@test.com', phone='08077777775')

    def test_user_phone_is_unique(self, create_user):
        create_user(email='phone1@test.com', phone='08077777776')
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            create_user(email='phone2@test.com', phone='08077777776')

    def test_owner_profile_auto_created_when_owner(self, create_user):
        user = create_user(
            email='owner_signal@test.com',
            phone='08077777777',
            is_owner=True,
        )
        assert OwnerProfile.objects.filter(user=user).exists()

    def test_owner_profile_not_created_for_renter(self, create_user):
        user = create_user(
            email='renter_signal@test.com',
            phone='08077777778',
            is_renter=True,
            is_owner=False,
        )
        assert not OwnerProfile.objects.filter(user=user).exists()

    def test_owner_profile_created_when_role_switched(self, create_user):
        user = create_user(
            email='switch_signal@test.com',
            phone='08077777779',
            is_renter=True,
            is_owner=False,
        )
        assert not OwnerProfile.objects.filter(user=user).exists()
        user.is_owner = True
        user.save()
        assert OwnerProfile.objects.filter(user=user).exists()


@pytest.mark.django_db
class TestOTPCodeModel:
    def test_otp_str(self, create_user):
        from django.utils import timezone
        user = create_user(email='otp@test.com', phone='08066666661')
        otp = OTPCode.objects.create(
            user=user,
            code='123456',
            otp_type=OTPCode.OTP_TYPE_PHONE,
            expires_at=timezone.now(),
        )
        assert 'phone_verification' in str(otp)
        assert user.email in str(otp)


@pytest.mark.django_db
class TestOwnerProfileModel:
    def test_owner_profile_str(self, owner_user):
        from accounts.models import OwnerProfile
        profile, _ = OwnerProfile.objects.get_or_create(user=owner_user)
        assert owner_user.email in str(profile)
```

**Create `accounts/tests/test_services.py`:**

```python
import pytest
from unittest.mock import patch
from django.utils import timezone
from datetime import timedelta
from accounts.models import OTPCode
from accounts.services import (
    generate_otp_code,
    create_otp,
    verify_otp,
    process_document_upload,
)


@pytest.mark.unit
class TestGenerateOTPCode:
    def test_generates_6_digits(self):
        code = generate_otp_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_generates_different_codes(self):
        codes = {generate_otp_code() for _ in range(20)}
        assert len(codes) > 1


@pytest.mark.django_db
class TestCreateOTP:
    def test_creates_otp_record(self, create_user):
        user = create_user(email='otp_create@test.com', phone='08055551111')
        otp = create_otp(user, OTPCode.OTP_TYPE_PHONE)
        assert OTPCode.objects.filter(user=user, otp_type=OTPCode.OTP_TYPE_PHONE).exists()
        assert otp.is_used is False

    def test_invalidates_previous_otps(self, create_user):
        user = create_user(email='otp_inv@test.com', phone='08055551112')
        otp1 = create_otp(user, OTPCode.OTP_TYPE_PHONE)
        otp2 = create_otp(user, OTPCode.OTP_TYPE_PHONE)
        otp1.refresh_from_db()
        assert otp1.is_used is True
        assert otp2.is_used is False

    def test_prints_to_console(self, create_user, capsys):
        user = create_user(email='otp_print@test.com', phone='08055551113')
        create_otp(user, OTPCode.OTP_TYPE_PHONE)
        captured = capsys.readouterr()
        assert '[DEV OTP]' in captured.out
        assert user.email in captured.out

    def test_otp_expires_in_10_minutes(self, create_user):
        user = create_user(email='otp_exp@test.com', phone='08055551114')
        before = timezone.now()
        otp = create_otp(user, OTPCode.OTP_TYPE_PHONE)
        after = timezone.now()
        expected_min = before + timedelta(minutes=9, seconds=59)
        expected_max = after + timedelta(minutes=10, seconds=1)
        assert expected_min <= otp.expires_at <= expected_max


@pytest.mark.django_db
class TestVerifyOTP:
    def test_valid_otp_returns_true(self, create_user):
        user = create_user(email='otp_v1@test.com', phone='08055551121')
        otp = create_otp(user, OTPCode.OTP_TYPE_PHONE)
        assert verify_otp(user, otp.code, OTPCode.OTP_TYPE_PHONE) is True

    def test_valid_otp_marks_as_used(self, create_user):
        user = create_user(email='otp_v2@test.com', phone='08055551122')
        otp = create_otp(user, OTPCode.OTP_TYPE_PHONE)
        verify_otp(user, otp.code, OTPCode.OTP_TYPE_PHONE)
        otp.refresh_from_db()
        assert otp.is_used is True

    def test_wrong_code_returns_false(self, create_user):
        user = create_user(email='otp_v3@test.com', phone='08055551123')
        create_otp(user, OTPCode.OTP_TYPE_PHONE)
        assert verify_otp(user, '000000', OTPCode.OTP_TYPE_PHONE) is False

    def test_expired_otp_returns_false(self, create_user):
        user = create_user(email='otp_v4@test.com', phone='08055551124')
        otp = create_otp(user, OTPCode.OTP_TYPE_PHONE)
        otp.expires_at = timezone.now() - timedelta(minutes=1)
        otp.save()
        assert verify_otp(user, otp.code, OTPCode.OTP_TYPE_PHONE) is False

    def test_used_otp_returns_false(self, create_user):
        user = create_user(email='otp_v5@test.com', phone='08055551125')
        otp = create_otp(user, OTPCode.OTP_TYPE_PHONE)
        verify_otp(user, otp.code, OTPCode.OTP_TYPE_PHONE)
        assert verify_otp(user, otp.code, OTPCode.OTP_TYPE_PHONE) is False

    def test_wrong_type_returns_false(self, create_user):
        user = create_user(email='otp_v6@test.com', phone='08055551126')
        otp = create_otp(user, OTPCode.OTP_TYPE_PHONE)
        assert verify_otp(user, otp.code, OTPCode.OTP_TYPE_PASSWORD_RESET) is False


@pytest.mark.django_db
class TestProcessDocumentUpload:
    def test_auto_approves_document(self, owner_user):
        from django.core.files.uploadedfile import SimpleUploadedFile
        fake_file = SimpleUploadedFile('id.pdf', b'content', content_type='application/pdf')
        doc = process_document_upload(owner_user, fake_file, 'government_id')
        assert doc.status == 'approved'

    def test_sets_user_id_verified(self, owner_user):
        from django.core.files.uploadedfile import SimpleUploadedFile
        fake_file = SimpleUploadedFile('id2.pdf', b'content', content_type='application/pdf')
        process_document_upload(owner_user, fake_file, 'government_id')
        owner_user.refresh_from_db()
        assert owner_user.is_id_verified is True
        assert owner_user.verification_level == 1

    def test_prints_dev_kyc_to_console(self, owner_user, capsys):
        from django.core.files.uploadedfile import SimpleUploadedFile
        fake_file = SimpleUploadedFile('id3.pdf', b'content', content_type='application/pdf')
        process_document_upload(owner_user, fake_file, 'government_id')
        captured = capsys.readouterr()
        assert '[DEV KYC]' in captured.out


@pytest.mark.django_db
class TestAuthAPI:
    BASE_URL = '/api/v1/auth'

    def test_register_success(self, api_client):
        response = api_client.post(f'{self.BASE_URL}/register/', {
            'email': 'newuser@test.com',
            'phone': '08099998881',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'securepass123!',
            'password_confirm': 'securepass123!',
        })
        assert response.status_code == 201
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']

    def test_register_auto_verifies_email(self, api_client):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        api_client.post(f'{self.BASE_URL}/register/', {
            'email': 'autoverify@test.com',
            'phone': '08099998882',
            'first_name': 'Auto',
            'last_name': 'Verify',
            'password': 'securepass123!',
            'password_confirm': 'securepass123!',
        })
        user = User.objects.get(email='autoverify@test.com')
        assert user.is_email_verified is True

    def test_register_prints_otp(self, api_client, capsys):
        api_client.post(f'{self.BASE_URL}/register/', {
            'email': 'otpprint@test.com',
            'phone': '08099998883',
            'first_name': 'OTP',
            'last_name': 'Print',
            'password': 'securepass123!',
            'password_confirm': 'securepass123!',
        })
        captured = capsys.readouterr()
        assert '[DEV OTP]' in captured.out

    def test_register_password_mismatch(self, api_client):
        response = api_client.post(f'{self.BASE_URL}/register/', {
            'email': 'mismatch@test.com',
            'phone': '08099998884',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'securepass123!',
            'password_confirm': 'wrongpass123!',
        })
        assert response.status_code == 400

    def test_register_duplicate_email(self, api_client, renter_user):
        response = api_client.post(f'{self.BASE_URL}/register/', {
            'email': renter_user.email,
            'phone': '08099998885',
            'first_name': 'Dup',
            'last_name': 'User',
            'password': 'securepass123!',
            'password_confirm': 'securepass123!',
        })
        assert response.status_code == 400

    def test_login_success(self, api_client, renter_user):
        response = api_client.post(f'{self.BASE_URL}/login/', {
            'email': renter_user.email,
            'password': 'testpass123!',
        })
        assert response.status_code == 200
        assert 'access' in response.data

    def test_login_wrong_password(self, api_client, renter_user):
        response = api_client.post(f'{self.BASE_URL}/login/', {
            'email': renter_user.email,
            'password': 'wrongpassword',
        })
        assert response.status_code == 401

    def test_login_jwt_contains_role_fields(self, api_client, owner_user):
        response = api_client.post(f'{self.BASE_URL}/login/', {
            'email': owner_user.email,
            'password': 'testpass123!',
        })
        import jwt as pyjwt
        token = response.data['access']
        payload = pyjwt.decode(token, options={"verify_signature": False})
        assert 'is_owner' in payload
        assert 'is_renter' in payload
        assert payload['is_owner'] is True

    def test_logout_blacklists_token(self, auth_client, renter_user):
        login_response = APIClient().post(f'{self.BASE_URL}/login/', {
            'email': renter_user.email,
            'password': 'testpass123!',
        })
        refresh_token = login_response.data['refresh']
        response = auth_client.post(f'{self.BASE_URL}/logout/', {
            'refresh': refresh_token,
        })
        assert response.status_code == 200

    def test_verify_phone_with_correct_otp(self, auth_client, renter_user, capsys):
        create_response = APIClient()
        create_response.force_authenticate(user=renter_user)
        create_response.post(f'{self.BASE_URL}/resend-otp/')
        capsys.readouterr()

        from accounts.models import OTPCode
        otp = OTPCode.objects.filter(
            user=renter_user,
            otp_type=OTPCode.OTP_TYPE_PHONE,
            is_used=False,
        ).last()

        response = auth_client.post(f'{self.BASE_URL}/verify-phone/', {
            'otp_code': otp.code,
        })
        assert response.status_code == 200
        renter_user.refresh_from_db()
        assert renter_user.is_phone_verified is True

    def test_verify_phone_with_wrong_otp(self, auth_client):
        response = auth_client.post(f'{self.BASE_URL}/verify-phone/', {
            'otp_code': '000000',
        })
        assert response.status_code == 400

    def test_password_reset_request_does_not_reveal_email_existence(self, api_client):
        response = api_client.post(f'{self.BASE_URL}/password/reset/', {
            'email': 'nonexistent@example.com',
        })
        assert response.status_code == 200

    def test_password_reset_confirm_success(self, api_client, create_user):
        from accounts.services import create_otp
        from accounts.models import OTPCode
        user = create_user(email='reset@test.com', phone='08099998886')
        otp = create_otp(user, OTPCode.OTP_TYPE_PASSWORD_RESET)
        response = api_client.post(f'{self.BASE_URL}/password/reset/confirm/', {
            'email': user.email,
            'otp_code': otp.code,
            'new_password': 'newpassword123!',
        })
        assert response.status_code == 200

    def test_unauthenticated_cannot_access_protected_route(self, api_client):
        response = api_client.get('/api/v1/users/me/')
        assert response.status_code == 401


from rest_framework.test import APIClient


@pytest.mark.django_db
class TestUserAPI:
    BASE_URL = '/api/v1/users'

    def test_get_own_profile(self, auth_client, renter_user):
        response = auth_client.get(f'{self.BASE_URL}/me/')
        assert response.status_code == 200
        assert response.data['data']['email'] == renter_user.email

    def test_profile_includes_unread_messages(self, auth_client):
        response = auth_client.get(f'{self.BASE_URL}/me/')
        assert 'unread_messages' in response.data['data']

    def test_update_profile(self, auth_client):
        response = auth_client.patch(f'{self.BASE_URL}/me/', {
            'first_name': 'Updated',
            'bio': 'New bio',
        })
        assert response.status_code == 200

    def test_update_role_to_owner(self, auth_client, renter_user):
        response = auth_client.patch(f'{self.BASE_URL}/me/role/', {
            'is_owner': True,
        })
        assert response.status_code == 200
        renter_user.refresh_from_db()
        assert renter_user.is_owner is True

    def test_cannot_disable_both_roles(self, dual_client):
        response = dual_client.patch('/api/v1/users/me/role/', {
            'is_owner': False,
            'is_renter': False,
        })
        assert response.status_code == 400

    def test_public_profile_is_accessible_without_auth(self, api_client, renter_user):
        response = api_client.get(f'{self.BASE_URL}/{renter_user.id}/')
        assert response.status_code == 200
        assert 'email' not in response.data['data']

    def test_public_profile_excludes_sensitive_fields(self, api_client, renter_user):
        response = api_client.get(f'{self.BASE_URL}/{renter_user.id}/')
        data = response.data['data']
        assert 'phone' not in data
        assert 'email' not in data

    def test_public_profile_404_for_nonexistent(self, api_client):
        import uuid
        response = api_client.get(f'{self.BASE_URL}/{uuid.uuid4()}/')
        assert response.status_code == 404

    def test_unauthenticated_cannot_get_own_profile(self, api_client):
        response = api_client.get(f'{self.BASE_URL}/me/')
        assert response.status_code == 401
```

---

## Step 7: Create listings app tests

**Create `listings/tests/__init__.py`** (empty)

**Create `listings/tests/test_models.py`:**

```python
import pytest
from django.contrib.gis.geos import Point
from listings.models import Listing, ListingMedia, ListingStatus, ResourceType


@pytest.mark.django_db
class TestListingModel:
    def test_listing_str(self, owner_user):
        listing = Listing.objects.create(
            owner=owner_user,
            resource_type=ResourceType.EQUIPMENT,
            title='Test Crane',
            status='draft',
        )
        assert 'Test Crane' in str(listing)
        assert 'equipment' in str(listing)

    def test_primary_photo_url_returns_none_with_no_media(self, owner_user):
        listing = Listing.objects.create(
            owner=owner_user,
            resource_type='equipment',
            title='No Photo',
            status='draft',
        )
        assert listing.primary_photo_url is None

    def test_latitude_longitude_from_point(self, owner_user):
        listing = Listing.objects.create(
            owner=owner_user,
            resource_type='equipment',
            title='Located Listing',
            location=Point(3.3792, 6.5244, srid=4326),
            status='draft',
        )
        assert listing.latitude == pytest.approx(6.5244, abs=0.001)
        assert listing.longitude == pytest.approx(3.3792, abs=0.001)

    def test_latitude_longitude_none_without_location(self, owner_user):
        listing = Listing.objects.create(
            owner=owner_user,
            resource_type='equipment',
            title='No Location',
            status='draft',
        )
        assert listing.latitude is None
        assert listing.longitude is None

    def test_listing_default_verification_tier_is_basic(self, owner_user):
        listing = Listing.objects.create(
            owner=owner_user,
            resource_type='equipment',
            title='Basic Listing',
            status='draft',
        )
        assert listing.verification_tier == 'basic'

    def test_listing_default_view_count_is_zero(self, owner_user):
        listing = Listing.objects.create(
            owner=owner_user,
            resource_type='equipment',
            title='Zero Views',
            status='draft',
        )
        assert listing.view_count == 0


@pytest.mark.django_db
class TestListingMediaModel:
    def test_setting_primary_unsets_others(self, owner_user):
        from tests.factories import ListingFactory, ListingMediaFactory
        listing = ListingFactory(owner=owner_user)

        from django.core.files.uploadedfile import SimpleUploadedFile
        file1 = SimpleUploadedFile('photo1.jpg', b'content', content_type='image/jpeg')
        file2 = SimpleUploadedFile('photo2.jpg', b'content', content_type='image/jpeg')

        media1 = ListingMedia.objects.create(
            listing=listing, file=file1, is_primary=True
        )
        media2 = ListingMedia.objects.create(
            listing=listing, file=file2, is_primary=True
        )

        media1.refresh_from_db()
        assert media1.is_primary is False
        assert media2.is_primary is True
```

**Create `listings/tests/test_serializers.py`:**

```python
import pytest
from django.contrib.gis.geos import Point
from listings.serializers import CreateListingSerializer, UpdateListingStatusSerializer
from listings.models import Listing


@pytest.mark.django_db
class TestCreateListingSerializer:
    def test_valid_data_creates_point(self, owner_user):
        data = {
            'resource_type': 'equipment',
            'title': 'Test Crane',
            'price_daily': 50000,
            'latitude': 6.5244,
            'longitude': 3.3792,
        }
        serializer = CreateListingSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert 'location' in serializer.validated_data
        assert isinstance(serializer.validated_data['location'], Point)

    def test_no_lat_lng_leaves_location_unset(self):
        data = {
            'resource_type': 'equipment',
            'title': 'No Location Crane',
            'price_daily': 50000,
        }
        serializer = CreateListingSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert 'location' not in serializer.validated_data

    def test_invalid_resource_type_fails(self):
        data = {
            'resource_type': 'invalid_type',
            'title': 'Bad Type',
        }
        serializer = CreateListingSerializer(data=data)
        assert not serializer.is_valid()
        assert 'resource_type' in serializer.errors


@pytest.mark.django_db
class TestUpdateListingStatusSerializer:
    def test_cannot_activate_without_location(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, location=None, status='draft')
        serializer = UpdateListingStatusSerializer(
            listing, data={'status': 'active'}, partial=True
        )
        assert not serializer.is_valid()
        assert 'status' in serializer.errors

    def test_cannot_activate_without_photos(self, owner_user):
        from django.contrib.gis.geos import Point
        from tests.factories import ListingFactory
        listing = ListingFactory(
            owner=owner_user,
            location=Point(3.3792, 6.5244, srid=4326),
            status='draft',
        )
        serializer = UpdateListingStatusSerializer(
            listing, data={'status': 'active'}, partial=True
        )
        assert not serializer.is_valid()

    def test_can_pause_active_listing(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, status='active')
        serializer = UpdateListingStatusSerializer(
            listing, data={'status': 'paused'}, partial=True
        )
        assert serializer.is_valid(), serializer.errors
```

**Create `listings/tests/test_views.py`:**

```python
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.gis.geos import Point
from listings.models import Listing, ListingReport


@pytest.mark.django_db
class TestListingListCreate:
    URL = '/api/v1/listings/'

    def test_unauthenticated_cannot_list(self, api_client):
        response = api_client.get(self.URL)
        assert response.status_code == 401

    def test_owner_gets_own_listings_only(self, owner_client, owner_user, second_owner_user):
        from tests.factories import ListingFactory
        ListingFactory(owner=owner_user)
        ListingFactory(owner=owner_user)
        ListingFactory(owner=second_owner_user)
        response = owner_client.get(self.URL)
        assert response.status_code == 200
        assert response.data['count'] == 2

    def test_response_is_paginated(self, owner_client):
        response = owner_client.get(self.URL)
        assert 'count' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data
        assert 'results' in response.data

    def test_filter_by_status(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        ListingFactory(owner=owner_user, status='active')
        ListingFactory(owner=owner_user, status='paused')
        response = owner_client.get(f'{self.URL}?status=active')
        assert response.data['count'] == 1

    def test_filter_by_resource_type(self, owner_client, owner_user):
        from tests.factories import ListingFactory, WarehouseListingFactory
        ListingFactory(owner=owner_user, resource_type='equipment')
        WarehouseListingFactory(owner=owner_user, resource_type='warehouse')
        response = owner_client.get(f'{self.URL}?resource_type=equipment')
        assert response.data['count'] == 1

    def test_ordering_by_view_count(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        l1 = ListingFactory(owner=owner_user, view_count=10)
        l2 = ListingFactory(owner=owner_user, view_count=50)
        l3 = ListingFactory(owner=owner_user, view_count=5)
        response = owner_client.get(f'{self.URL}?ordering=-view_count')
        results = response.data['results']
        assert str(l2.id) == results[0]['id']
        assert str(l1.id) == results[1]['id']
        assert str(l3.id) == results[2]['id']

    def test_non_owner_cannot_create_listing(self, auth_client):
        response = auth_client.post(self.URL, {
            'resource_type': 'equipment',
            'title': 'Should Fail',
        })
        assert response.status_code == 403

    def test_owner_can_create_listing(self, owner_client):
        response = owner_client.post(self.URL, {
            'resource_type': 'equipment',
            'title': 'New Crane',
            'price_daily': 50000,
            'latitude': 6.5244,
            'longitude': 3.3792,
        }, format='json')
        assert response.status_code == 201
        assert response.data['data']['title'] == 'New Crane'
        assert response.data['data']['status'] == 'draft'

    def test_create_listing_without_location_creates_draft(self, owner_client):
        response = owner_client.post(self.URL, {
            'resource_type': 'warehouse',
            'title': 'No Location Warehouse',
            'price_monthly': 2000000,
        }, format='json')
        assert response.status_code == 201
        assert response.data['data']['latitude'] is None


@pytest.mark.django_db
class TestListingDetail:
    def test_public_can_view_active_listing(self, api_client):
        from tests.factories import ListingFactory
        listing = ListingFactory(status='active')
        response = api_client.get(f'/api/v1/listings/{listing.id}/')
        assert response.status_code == 200

    def test_view_increments_view_count(self, api_client):
        from tests.factories import ListingFactory
        listing = ListingFactory(status='active', view_count=0)
        api_client.get(f'/api/v1/listings/{listing.id}/')
        listing.refresh_from_db()
        assert listing.view_count == 1

    def test_owner_can_update_own_listing(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        response = owner_client.patch(
            f'/api/v1/listings/{listing.id}/',
            {'title': 'Updated Title'},
            format='json',
        )
        assert response.status_code == 200

    def test_non_owner_cannot_update_listing(self, auth_client):
        from tests.factories import ListingFactory
        listing = ListingFactory()
        response = auth_client.patch(
            f'/api/v1/listings/{listing.id}/',
            {'title': 'Hacked Title'},
        )
        assert response.status_code == 403

    def test_delete_archives_listing(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, status='active')
        response = owner_client.delete(f'/api/v1/listings/{listing.id}/')
        assert response.status_code == 200
        listing.refresh_from_db()
        assert listing.status == 'archived'

    def test_cannot_activate_listing_without_location(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user, location=None, status='draft')
        response = owner_client.patch(
            f'/api/v1/listings/{listing.id}/status/',
            {'status': 'active'},
        )
        assert response.status_code == 400

    def test_nonexistent_listing_returns_404(self, api_client):
        import uuid
        response = api_client.get(f'/api/v1/listings/{uuid.uuid4()}/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestListingMedia:
    def test_upload_photo(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        photo = SimpleUploadedFile('test.jpg', b'imgcontent', content_type='image/jpeg')
        response = owner_client.post(
            f'/api/v1/listings/{listing.id}/media/',
            {'file': photo},
            format='multipart',
        )
        assert response.status_code == 201
        assert response.data['data']['is_primary'] is True

    def test_first_photo_is_auto_primary(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        for i in range(3):
            photo = SimpleUploadedFile(f'test{i}.jpg', b'content', content_type='image/jpeg')
            owner_client.post(
                f'/api/v1/listings/{listing.id}/media/',
                {'file': photo},
                format='multipart',
            )
        from listings.models import ListingMedia
        assert ListingMedia.objects.filter(listing=listing, is_primary=True).count() == 1

    def test_non_owner_cannot_upload(self, auth_client):
        from tests.factories import ListingFactory
        listing = ListingFactory()
        photo = SimpleUploadedFile('test.jpg', b'content', content_type='image/jpeg')
        response = auth_client.post(
            f'/api/v1/listings/{listing.id}/media/',
            {'file': photo},
            format='multipart',
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestListingReport:
    def test_renter_can_report_listing(self, auth_client):
        from tests.factories import ListingFactory
        listing = ListingFactory(status='active')
        response = auth_client.post(
            f'/api/v1/listings/{listing.id}/report/',
            {'reason': 'fake', 'description': 'This is fake'},
        )
        assert response.status_code == 201

    def test_cannot_report_own_listing(self, owner_client, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        response = owner_client.post(
            f'/api/v1/listings/{listing.id}/report/',
            {'reason': 'spam'},
        )
        assert response.status_code == 400

    def test_cannot_report_twice(self, auth_client):
        from tests.factories import ListingFactory
        listing = ListingFactory(status='active')
        auth_client.post(f'/api/v1/listings/{listing.id}/report/', {'reason': 'fake'})
        response = auth_client.post(f'/api/v1/listings/{listing.id}/report/', {'reason': 'fake'})
        assert response.status_code == 400
```

---

## Step 8: Create search app tests

**Create `search/tests/__init__.py`** (empty)

**Create `search/tests/test_views.py`:**

```python
import pytest
from django.contrib.gis.geos import Point
from listings.models import Listing


@pytest.mark.django_db
class TestMapSearch:
    URL = '/api/v1/search/map/'
    LAGOS_LAT = 6.5244
    LAGOS_LNG = 3.3792

    def test_requires_lat_and_lng(self, api_client):
        response = api_client.get(self.URL)
        assert response.status_code == 400

    def test_requires_lat(self, api_client):
        response = api_client.get(f'{self.URL}?lng={self.LAGOS_LNG}')
        assert response.status_code == 400

    def test_requires_lng(self, api_client):
        response = api_client.get(f'{self.URL}?lat={self.LAGOS_LAT}')
        assert response.status_code == 400

    def test_invalid_coordinates_rejected(self, api_client):
        response = api_client.get(f'{self.URL}?lat=999&lng=999')
        assert response.status_code == 400

    def test_non_numeric_rejected(self, api_client):
        response = api_client.get(f'{self.URL}?lat=abc&lng=xyz')
        assert response.status_code == 400

    def test_returns_active_listings_in_radius(self, api_client, owner_user):
        from tests.factories import ListingFactory
        close = ListingFactory(
            owner=owner_user,
            status='active',
            location=Point(3.3800, 6.5250, srid=4326),
        )
        far = ListingFactory(
            owner=owner_user,
            status='active',
            location=Point(5.0000, 10.0000, srid=4326),
        )
        response = api_client.get(
            f'{self.URL}?lat={self.LAGOS_LAT}&lng={self.LAGOS_LNG}&radius=10'
        )
        assert response.status_code == 200
        ids = [r['id'] for r in response.data['data']]
        assert str(close.id) in ids
        assert str(far.id) not in ids

    def test_draft_listings_not_returned(self, api_client, owner_user):
        from tests.factories import ListingFactory
        ListingFactory(
            owner=owner_user,
            status='draft',
            location=Point(3.3800, 6.5250, srid=4326),
        )
        response = api_client.get(
            f'{self.URL}?lat={self.LAGOS_LAT}&lng={self.LAGOS_LNG}'
        )
        assert response.status_code == 200
        assert response.data['count'] == 0

    def test_results_include_distance_km(self, api_client, owner_user):
        from tests.factories import ListingFactory
        ListingFactory(
            owner=owner_user,
            status='active',
            location=Point(3.3800, 6.5250, srid=4326),
        )
        response = api_client.get(
            f'{self.URL}?lat={self.LAGOS_LAT}&lng={self.LAGOS_LNG}'
        )
        assert response.status_code == 200
        assert len(response.data['data']) > 0
        assert 'distance_km' in response.data['data'][0]
        assert response.data['data'][0]['distance_km'] is not None

    def test_results_ordered_by_distance(self, api_client, owner_user):
        from tests.factories import ListingFactory
        near = ListingFactory(
            owner=owner_user,
            status='active',
            location=Point(3.3800, 6.5250, srid=4326),
        )
        far = ListingFactory(
            owner=owner_user,
            status='active',
            location=Point(3.4500, 6.5800, srid=4326),
        )
        response = api_client.get(
            f'{self.URL}?lat={self.LAGOS_LAT}&lng={self.LAGOS_LNG}'
        )
        ids = [r['id'] for r in response.data['data']]
        assert ids.index(str(near.id)) < ids.index(str(far.id))

    def test_filter_by_resource_type(self, api_client, owner_user):
        from tests.factories import ListingFactory, WarehouseListingFactory
        ListingFactory(
            owner=owner_user,
            status='active',
            resource_type='equipment',
            location=Point(3.3800, 6.5250, srid=4326),
        )
        WarehouseListingFactory(
            owner=owner_user,
            status='active',
            resource_type='warehouse',
            location=Point(3.3810, 6.5260, srid=4326),
        )
        response = api_client.get(
            f'{self.URL}?lat={self.LAGOS_LAT}&lng={self.LAGOS_LNG}&resource_type=equipment'
        )
        assert response.data['count'] == 1
        assert response.data['data'][0]['resource_type'] == 'equipment'

    def test_invalid_resource_type_returns_400(self, api_client):
        response = api_client.get(
            f'{self.URL}?lat={self.LAGOS_LAT}&lng={self.LAGOS_LNG}&resource_type=invalid'
        )
        assert response.status_code == 400

    def test_unavailable_listings_excluded_by_default(self, api_client, owner_user):
        from tests.factories import ListingFactory
        ListingFactory(
            owner=owner_user,
            status='active',
            is_available=False,
            location=Point(3.3800, 6.5250, srid=4326),
        )
        response = api_client.get(
            f'{self.URL}?lat={self.LAGOS_LAT}&lng={self.LAGOS_LNG}'
        )
        assert response.data['count'] == 0

    def test_available_false_param_includes_all(self, api_client, owner_user):
        from tests.factories import ListingFactory
        ListingFactory(
            owner=owner_user,
            status='active',
            is_available=False,
            location=Point(3.3800, 6.5250, srid=4326),
        )
        response = api_client.get(
            f'{self.URL}?lat={self.LAGOS_LAT}&lng={self.LAGOS_LNG}&available=false'
        )
        assert response.data['count'] == 1

    def test_unauthenticated_user_can_search(self, api_client, owner_user):
        from tests.factories import ListingFactory
        ListingFactory(
            owner=owner_user,
            status='active',
            location=Point(3.3800, 6.5250, srid=4326),
        )
        response = api_client.get(
            f'{self.URL}?lat={self.LAGOS_LAT}&lng={self.LAGOS_LNG}'
        )
        assert response.status_code == 200

    def test_radius_cap_at_500km(self, api_client):
        response = api_client.get(
            f'{self.URL}?lat={self.LAGOS_LAT}&lng={self.LAGOS_LNG}&radius=99999'
        )
        assert response.status_code == 200
        assert response.data['radius_km'] == 500
```

---

## Step 9: Verify Part 1 tests pass

Run Part 1 tests only:

```bash
pytest core/ accounts/ listings/ search/ tests/ -v --tb=short
```

Fix any failures before starting Part 2. All tests in Part 1 must pass with 0 failures before proceeding.

---

## Step 10: Commit Part 1

```bash
git add .
git commit -m "test: Wave 06 Part 1 — core, accounts, listings, search test suite"
```

---

## Part 1 Definition of Done

- [ ] `pytest.ini` exists in project root with correct configuration
- [ ] `conftest.py` exists in project root with all shared fixtures
- [ ] `tests/factories.py` exists with all factory classes
- [ ] `core/tests/` contains `test_models.py`, `test_permissions.py`, `test_pagination.py`
- [ ] `accounts/tests/` contains `test_models.py`, `test_services.py` (includes auth and user API tests)
- [ ] `listings/tests/` contains `test_models.py`, `test_serializers.py`, `test_views.py`
- [ ] `search/tests/` contains `test_views.py`
- [ ] `pytest core/ accounts/ listings/ search/ tests/` runs with **0 failures**
- [ ] Coverage report generated showing per-file coverage
- [ ] Git commit made with message `test: Wave 06 Part 1 — core, accounts, listings, search test suite`
