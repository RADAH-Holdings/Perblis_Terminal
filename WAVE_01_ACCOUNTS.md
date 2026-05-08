# TERMINAL — WAVE 01: ACCOUNTS (AUTH + USER)
> Agent task file. Execute every instruction in order. Do not skip steps.
> Wave 00 must be complete before starting this wave.
> Do not proceed to Wave 02 until the Definition of Done checklist is fully complete.

---

## Context

This wave builds the `accounts` app — user registration, login, JWT auth, and user profile management. This is the foundation every other module depends on.

**Simulation decisions (do not deviate):**
- Phone OTP: Generate a 6-digit code, print it to the console with `print(f"[DEV OTP] {code}")`. Always mark phone as verified after OTP submission. Do NOT integrate Termii.
- Email verification: Mark email as verified automatically on register. Send a welcome email using Django's console email backend (already configured in development settings).
- KYC documents: Accept uploads and automatically set `verification_level = 1`. Do NOT build an admin review queue.

---

## Step 1: Create the User model

**File: `accounts/models.py`**

```python
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Remove username — use email as the unique identifier
    username = None
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)

    # Profile
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, default='')

    # Roles — a user is renter by default, must explicitly enable owner
    is_renter = models.BooleanField(default=True)
    is_owner = models.BooleanField(default=False)

    # Verification — simulated for MVP
    verification_level = models.IntegerField(default=0)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_id_verified = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"

    @property
    def full_name(self):
        return self.get_full_name()


class OTPCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    code = models.CharField(max_length=6)

    OTP_TYPE_PHONE = 'phone_verification'
    OTP_TYPE_PASSWORD_RESET = 'password_reset'
    OTP_TYPES = [
        (OTP_TYPE_PHONE, 'Phone Verification'),
        (OTP_TYPE_PASSWORD_RESET, 'Password Reset'),
    ]
    otp_type = models.CharField(max_length=30, choices=OTP_TYPES)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'otp_codes'
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP({self.otp_type}) for {self.user.email}"


class UserDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    document_file = models.FileField(upload_to='kyc_documents/')

    DOC_TYPE_GOVERNMENT_ID = 'government_id'
    DOC_TYPE_BUSINESS_REG = 'business_registration'
    DOC_TYPES = [
        (DOC_TYPE_GOVERNMENT_ID, 'Government ID'),
        (DOC_TYPE_BUSINESS_REG, 'Business Registration'),
    ]
    document_type = models.CharField(max_length=30, choices=DOC_TYPES)

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.document_type} for {self.user.email} — {self.status}"
```

---

## Step 2: Create the serializers

**File: `accounts/serializers.py`**

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds user role fields to the JWT payload."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['full_name'] = user.full_name
        token['is_owner'] = user.is_owner
        token['is_renter'] = user.is_renter
        token['verification_level'] = user.verification_level
        return token


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'email', 'phone', 'first_name', 'last_name',
            'password', 'password_confirm',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        # MVP simulation: auto-verify email on register
        user.is_email_verified = True
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'first_name', 'last_name', 'full_name',
            'profile_photo', 'bio', 'is_renter', 'is_owner',
            'verification_level', 'is_phone_verified', 'is_email_verified',
            'is_id_verified', 'created_at',
        ]
        read_only_fields = [
            'id', 'email', 'verification_level', 'is_phone_verified',
            'is_email_verified', 'is_id_verified', 'created_at',
        ]

    def get_full_name(self, obj):
        return obj.full_name


class PublicUserSerializer(serializers.ModelSerializer):
    """Minimal public-facing user profile. No sensitive fields."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'profile_photo', 'bio',
            'is_owner', 'is_renter', 'verification_level', 'created_at',
        ]

    def get_full_name(self, obj):
        return obj.full_name


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'bio', 'profile_photo']


class UpdateRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['is_owner', 'is_renter']

    def validate(self, attrs):
        # At least one role must remain active
        is_owner = attrs.get('is_owner', self.instance.is_owner)
        is_renter = attrs.get('is_renter', self.instance.is_renter)
        if not is_owner and not is_renter:
            raise serializers.ValidationError(
                'A user must have at least one role active (owner or renter).'
            )
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, write_only=True, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp_code = serializers.CharField(required=True, max_length=6)
    new_password = serializers.CharField(
        required=True, write_only=True, validators=[validate_password]
    )


class VerifyPhoneSerializer(serializers.Serializer):
    otp_code = serializers.CharField(required=True, max_length=6)


class DocumentUploadSerializer(serializers.Serializer):
    document_file = serializers.FileField(required=True)
    document_type = serializers.ChoiceField(
        choices=['government_id', 'business_registration'],
        required=True,
    )
```

---

## Step 3: Create the service layer

Create `accounts/services.py`:

```python
import random
import string
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import OTPCode, UserDocument

User = get_user_model()


def generate_otp_code():
    """Generate a 6-digit numeric OTP code."""
    return ''.join(random.choices(string.digits, k=6))


def create_otp(user, otp_type):
    """
    Create an OTP code for the user.
    MVP simulation: prints the code to console instead of sending SMS.
    """
    # Invalidate any existing unused OTPs of the same type
    OTPCode.objects.filter(
        user=user,
        otp_type=otp_type,
        is_used=False,
    ).update(is_used=True)

    code = generate_otp_code()
    otp = OTPCode.objects.create(
        user=user,
        code=code,
        otp_type=otp_type,
        expires_at=timezone.now() + timedelta(minutes=10),
    )

    # MVP simulation: log to console
    print(f"[DEV OTP] User: {user.email} | Type: {otp_type} | Code: {code}")

    return otp


def verify_otp(user, code, otp_type):
    """
    Verify an OTP code. Returns True if valid, False otherwise.
    """
    try:
        otp = OTPCode.objects.get(
            user=user,
            code=code,
            otp_type=otp_type,
            is_used=False,
            expires_at__gt=timezone.now(),
        )
        otp.is_used = True
        otp.save()
        return True
    except OTPCode.DoesNotExist:
        return False


def send_welcome_email(user):
    """Send welcome email. Uses console backend in development."""
    send_mail(
        subject='Welcome to Terminal',
        message=(
            f"Hi {user.first_name},\n\n"
            "Welcome to Terminal — the one-stop platform for heavy asset leasing.\n\n"
            "You can now browse resources, list your assets, and manage bookings.\n\n"
            "The Terminal Team"
        ),
        from_email='noreply@terminal.app',
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_password_reset_email(user, otp_code):
    """Send password reset OTP via email."""
    send_mail(
        subject='Terminal — Password Reset',
        message=(
            f"Hi {user.first_name},\n\n"
            f"Your password reset code is: {otp_code}\n\n"
            "This code expires in 10 minutes.\n\n"
            "If you did not request this, ignore this email.\n\n"
            "The Terminal Team"
        ),
        from_email='noreply@terminal.app',
        recipient_list=[user.email],
        fail_silently=True,
    )


def process_document_upload(user, document_file, document_type):
    """
    Upload a KYC document and auto-approve (MVP simulation).
    Sets user verification_level = 1 and is_id_verified = True.
    """
    doc = UserDocument.objects.create(
        user=user,
        document_file=document_file,
        document_type=document_type,
        status=UserDocument.STATUS_APPROVED,  # MVP: auto-approve
    )

    # MVP simulation: auto-verify
    user.is_id_verified = True
    user.verification_level = 1
    user.save(update_fields=['is_id_verified', 'verification_level'])

    print(f"[DEV KYC] Auto-approved document for {user.email} — {document_type}")

    return doc
```

---

## Step 4: Create auth views

**File: `accounts/views/auth_views.py`**

First create the directory and init:

```
accounts/views/__init__.py   (empty)
accounts/views/auth_views.py
accounts/views/user_views.py
```

**`accounts/views/auth_views.py`**:

```python
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from ..serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    VerifyPhoneSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from ..services import (
    create_otp,
    verify_otp,
    send_welcome_email,
    send_password_reset_email,
)
from ..models import OTPCode

User = get_user_model()


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    # Send welcome email
    send_welcome_email(user)

    # Generate phone OTP and send (MVP: logs to console)
    create_otp(user, OTPCode.OTP_TYPE_PHONE)

    # Issue tokens
    refresh = RefreshToken.for_user(user)

    return Response({
        'success': True,
        'message': 'Registration successful. Check your phone for OTP.',
        'tokens': {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        },
        'user': {
            'id': str(user.id),
            'email': user.email,
            'full_name': user.full_name,
            'is_owner': user.is_owner,
            'is_renter': user.is_renter,
        },
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        pass
    return Response({'success': True, 'message': 'Logged out.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_phone(request):
    serializer = VerifyPhoneSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    code = serializer.validated_data['otp_code']
    user = request.user

    if verify_otp(user, code, OTPCode.OTP_TYPE_PHONE):
        user.is_phone_verified = True
        user.save(update_fields=['is_phone_verified'])
        return Response({'success': True, 'message': 'Phone verified successfully.'})

    return Response(
        {'success': False, 'errors': {'otp_code': 'Invalid or expired OTP.'}},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resend_phone_otp(request):
    create_otp(request.user, OTPCode.OTP_TYPE_PHONE)
    return Response({'success': True, 'message': 'OTP sent to your phone.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user
    if not user.check_password(serializer.validated_data['old_password']):
        return Response(
            {'success': False, 'errors': {'old_password': 'Incorrect password.'}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(serializer.validated_data['new_password'])
    user.save()

    return Response({'success': True, 'message': 'Password changed successfully.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']

    try:
        user = User.objects.get(email=email)
        otp = create_otp(user, OTPCode.OTP_TYPE_PASSWORD_RESET)
        send_password_reset_email(user, otp.code)
    except User.DoesNotExist:
        # Do not reveal whether the email exists
        pass

    return Response({
        'success': True,
        'message': 'If that email is registered, a reset code has been sent.',
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    code = serializer.validated_data['otp_code']
    new_password = serializer.validated_data['new_password']

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {'success': False, 'errors': {'email': 'No account with that email.'}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not verify_otp(user, code, OTPCode.OTP_TYPE_PASSWORD_RESET):
        return Response(
            {'success': False, 'errors': {'otp_code': 'Invalid or expired code.'}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(new_password)
    user.save()

    return Response({'success': True, 'message': 'Password reset successfully.'})
```

---

## Step 5: Create user views

**`accounts/views/user_views.py`**:

```python
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from ..serializers import (
    UserProfileSerializer,
    PublicUserSerializer,
    UpdateProfileSerializer,
    UpdateRoleSerializer,
    DocumentUploadSerializer,
)
from ..services import process_document_upload

User = get_user_model()


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user

    if request.method == 'GET':
        serializer = UserProfileSerializer(user)
        return Response({'success': True, 'data': serializer.data})

    serializer = UpdateProfileSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({
        'success': True,
        'message': 'Profile updated.',
        'data': UserProfileSerializer(user).data,
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_role(request):
    user = request.user
    serializer = UpdateRoleSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({
        'success': True,
        'message': 'Role updated.',
        'data': {
            'is_owner': user.is_owner,
            'is_renter': user.is_renter,
        },
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_document(request):
    serializer = DocumentUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    doc = process_document_upload(
        user=request.user,
        document_file=serializer.validated_data['document_file'],
        document_type=serializer.validated_data['document_type'],
    )

    return Response({
        'success': True,
        'message': 'Document uploaded and verified.',
        'data': {
            'id': str(doc.id),
            'document_type': doc.document_type,
            'status': doc.status,
        },
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_profile(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'success': False, 'errors': 'User not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = PublicUserSerializer(user)
    return Response({'success': True, 'data': serializer.data})
```

---

## Step 6: Wire up URLs

**`accounts/urls/auth.py`**:

```python
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views.auth_views import (
    LoginView,
    register,
    logout,
    verify_phone,
    resend_phone_otp,
    change_password,
    password_reset_request,
    password_reset_confirm,
)

urlpatterns = [
    path('register/', register, name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('logout/', logout, name='auth-logout'),
    path('verify-phone/', verify_phone, name='auth-verify-phone'),
    path('resend-otp/', resend_phone_otp, name='auth-resend-otp'),
    path('password/change/', change_password, name='auth-password-change'),
    path('password/reset/', password_reset_request, name='auth-password-reset'),
    path('password/reset/confirm/', password_reset_confirm, name='auth-password-reset-confirm'),
]
```

**`accounts/urls/users.py`**:

```python
from django.urls import path

from accounts.views.user_views import me, update_role, upload_document, public_profile

urlpatterns = [
    path('me/', me, name='user-me'),
    path('me/role/', update_role, name='user-role'),
    path('me/documents/', upload_document, name='user-documents'),
    path('<uuid:user_id>/', public_profile, name='user-public-profile'),
]
```

---

## Step 7: Create Django Admin registration

**`accounts/admin.py`**:

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import User, OTPCode, UserDocument


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = [
        'email', 'full_name', 'phone', 'is_renter', 'is_owner',
        'verification_level', 'is_active', 'created_at',
    ]
    list_filter = ['is_owner', 'is_renter', 'is_active', 'verification_level']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering = ['-created_at']

    fieldsets = (
        ('Account', {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'bio', 'profile_photo')}),
        ('Roles', {'fields': ('is_renter', 'is_owner')}),
        ('Verification', {'fields': ('is_phone_verified', 'is_email_verified', 'is_id_verified', 'verification_level')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    actions = ['suspend_users', 'activate_users']

    @admin.action(description='Suspend selected users')
    def suspend_users(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)


@admin.register(OTPCode)
class OTPCodeAdmin(ModelAdmin):
    list_display = ['user', 'otp_type', 'is_used', 'expires_at', 'created_at']
    list_filter = ['otp_type', 'is_used']
    search_fields = ['user__email']
    readonly_fields = ['id', 'code', 'created_at']


@admin.register(UserDocument)
class UserDocumentAdmin(ModelAdmin):
    list_display = ['user', 'document_type', 'status', 'created_at']
    list_filter = ['document_type', 'status']
    search_fields = ['user__email']
```

---

## Step 8: Create and run migrations

```bash
python manage.py makemigrations accounts
python manage.py migrate
python manage.py createsuperuser
```

When prompted for createsuperuser, use:
- Email: `admin@terminal.app`
- Phone: `08000000000`
- First name: `Terminal`
- Last name: `Admin`
- Password: `admin1234!`

---

## Step 9: Update `accounts/apps.py`

```python
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
```

---

## Step 10: Commit

```bash
git add .
git commit -m "feat(accounts): Wave 01 — AUTH + USER module complete"
```

---

## Definition of Done

Verify every item before handing back to supervisor.

**Models:**
- [ ] `User` model uses `email` as `USERNAME_FIELD` (not username)
- [ ] `User` has `is_owner` (default False) and `is_renter` (default True)
- [ ] `User` has `verification_level`, `is_phone_verified`, `is_email_verified`, `is_id_verified`
- [ ] `OTPCode` model exists with `otp_type`, `code`, `is_used`, `expires_at`
- [ ] `UserDocument` model exists with `document_type`, `document_file`, `status`
- [ ] `AUTH_USER_MODEL = 'accounts.User'` in base settings

**Auth endpoints (test with curl or Postman):**
- [ ] `POST /api/v1/auth/register/` → creates user, returns tokens, OTP printed to console
- [ ] `POST /api/v1/auth/login/` → returns access + refresh tokens
- [ ] `POST /api/v1/auth/token/refresh/` → returns new access token
- [ ] `POST /api/v1/auth/logout/` → blacklists refresh token
- [ ] `POST /api/v1/auth/verify-phone/` → marks phone verified when correct OTP given
- [ ] `POST /api/v1/auth/password/reset/` → triggers OTP (printed to console)
- [ ] `POST /api/v1/auth/password/reset/confirm/` → resets password with valid OTP

**User endpoints:**
- [ ] `GET /api/v1/users/me/` → returns current user profile
- [ ] `PATCH /api/v1/users/me/` → updates profile fields
- [ ] `PATCH /api/v1/users/me/role/` → toggles is_owner / is_renter
- [ ] `POST /api/v1/users/me/documents/` → uploads document, auto-approves, sets verification_level=1
- [ ] `GET /api/v1/users/{id}/` → returns public profile (unauthenticated allowed)

**JWT:**
- [ ] Access token payload contains: `email`, `full_name`, `is_owner`, `is_renter`, `verification_level`
- [ ] Protected endpoints return 401 without a valid token
- [ ] Role endpoints return correct role in response

**Django Admin:**
- [ ] `/admin/` loads with django-unfold theme (modern UI, not 2008 default)
- [ ] User list shows: email, full_name, phone, is_renter, is_owner, verification_level, is_active
- [ ] Suspend / Activate bulk actions work
- [ ] OTPCode list is readable (not a raw model dump)
- [ ] UserDocument list shows user, type, status

**Simulation behaviour:**
- [ ] OTP code is printed to console: `[DEV OTP] User: ... | Type: ... | Code: ...`
- [ ] New user email is auto-verified on register (no blocking gate)
- [ ] Document upload auto-approves and sets `verification_level = 1`
- [ ] `[DEV KYC]` message is printed to console on document upload

**General:**
- [ ] `python manage.py check` returns 0 issues
- [ ] Migrations are created and applied
- [ ] Superuser `admin@terminal.app` exists and can log into `/admin/`
- [ ] Git commit made with message `feat(accounts): Wave 01 — AUTH + USER module complete`
