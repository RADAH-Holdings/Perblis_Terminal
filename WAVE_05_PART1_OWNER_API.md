# TERMINAL — WAVE 05: OWNER WEB APP ENDPOINTS (Part 1 of 2)
> Agent task file. Execute every instruction in order. Do not skip steps.
> Wave 04 must be complete before starting this wave.
> Complete Part 1 fully before starting Part 2.
> Do not proceed to Wave 06 (Frontend) until both parts are done and the Definition of Done is complete.

---

## Context

This wave adds all backend endpoints required by the Owner Web App. It does not change any existing endpoint behaviour — it only adds new endpoints and extends existing ones with filters. Nothing built in Waves 01–04 is modified except where explicitly stated.

**What this wave covers (Part 1):**
1. New `OwnerProfile` model on the accounts app
2. Filter classes added to listings, bookings, and threads
3. Pagination confirmed active on all list endpoints
4. New `owner/` app to house dashboard, calendar, analytics, and settings endpoints

**What Part 2 covers:**
5. All new endpoint views and URLs
6. Django Admin registration for new models
7. Migrations and seed update

---

## Step 1: Create the `OwnerProfile` model

This model stores business-level information for owner users. It is separate from the `User` model to keep personal and business data cleanly separated.

**Open `accounts/models.py` and append the following class at the bottom of the file, after the `UserDocument` class:**

```python
class OwnerProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='owner_profile',
    )

    # Business identity
    business_name = models.CharField(max_length=200, blank=True, default='')
    business_description = models.TextField(blank=True, default='')
    business_logo = models.ImageField(upload_to='business_logos/', blank=True, null=True)

    # Bank details — stored for future payout integration
    bank_name = models.CharField(max_length=100, blank=True, default='')
    bank_account_number = models.CharField(max_length=20, blank=True, default='')
    bank_account_name = models.CharField(max_length=200, blank=True, default='')

    # Notification preferences
    notify_new_booking_request = models.BooleanField(default=True)
    notify_booking_confirmed = models.BooleanField(default=True)
    notify_new_message = models.BooleanField(default=True)
    notify_booking_cancelled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'owner_profiles'

    def __str__(self):
        return f"OwnerProfile: {self.user.email}"
```

---

## Step 2: Auto-create OwnerProfile when owner role is enabled

**Open `accounts/signals.py`** — this file does not exist yet, create it:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def create_owner_profile(sender, instance, created, **kwargs):
    """
    Auto-create an OwnerProfile whenever a user has is_owner=True.
    Safe to call multiple times — uses get_or_create.
    """
    if instance.is_owner:
        from .models import OwnerProfile
        OwnerProfile.objects.get_or_create(user=instance)
```

**Open `accounts/apps.py`** and update to connect signals:

```python
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        import accounts.signals  # noqa
```

---

## Step 3: Add OwnerProfile to accounts admin

**Open `accounts/admin.py`** and add the following import at the top:

```python
from .models import User, OTPCode, UserDocument, OwnerProfile
```

Append the following admin class at the bottom of the file:

```python
@admin.register(OwnerProfile)
class OwnerProfileAdmin(ModelAdmin):
    list_display = ['user', 'business_name', 'bank_name', 'created_at']
    search_fields = ['user__email', 'business_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
```

---

## Step 4: Add filter classes to listings

Install `django-filter` is already in requirements. Now create the filter class file.

**Create `listings/filters.py`:**

```python
import django_filters
from .models import Listing, ResourceType, ListingStatus


class ListingFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=ListingStatus.choices)
    resource_type = django_filters.ChoiceFilter(choices=ResourceType.choices)
    city = django_filters.CharFilter(
        field_name='location_city',
        lookup_expr='icontains',
    )
    is_available = django_filters.BooleanFilter()
    min_price_daily = django_filters.NumberFilter(
        field_name='price_daily',
        lookup_expr='gte',
    )
    max_price_daily = django_filters.NumberFilter(
        field_name='price_daily',
        lookup_expr='lte',
    )
    created_after = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date__gte',
    )
    created_before = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date__lte',
    )

    class Meta:
        model = Listing
        fields = [
            'status', 'resource_type', 'city',
            'is_available', 'min_price_daily', 'max_price_daily',
            'created_after', 'created_before',
        ]
```

---

## Step 5: Update the listings view to use filters, ordering, and pagination

**Open `listings/views.py`** and replace the `listing_list_create` function entirely with:

```python
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from core.pagination import StandardPagination
from .filters import ListingFilter


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def listing_list_create(request):
    """
    GET: Return the authenticated owner's own listings with filtering,
         ordering, and pagination.
    POST: Create a new listing (owner role required).
    """
    if request.method == 'GET':
        queryset = Listing.objects.filter(
            owner=request.user
        ).prefetch_related('media').order_by('-created_at')

        # Apply filters
        filterset = ListingFilter(request.query_params, queryset=queryset)
        if not filterset.is_valid():
            return Response(
                {'success': False, 'errors': filterset.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = filterset.qs

        # Apply ordering
        ordering = request.query_params.get('ordering', '-created_at')
        allowed_orderings = [
            'created_at', '-created_at',
            'view_count', '-view_count',
            'price_daily', '-price_daily',
            'title', '-title',
        ]
        if ordering in allowed_orderings:
            queryset = queryset.order_by(ordering)

        # Paginate
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ListingSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    # POST — requires owner role
    if not request.user.is_owner:
        return Response(
            {'success': False, 'errors': 'You must enable the owner role to create listings.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = CreateListingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    listing = serializer.save(owner=request.user)

    return Response(
        {'success': True, 'data': ListingSerializer(listing, context={'request': request}).data},
        status=status.HTTP_201_CREATED,
    )
```

---

## Step 6: Add filter classes to bookings

**Create `bookings/filters.py`:**

```python
import django_filters
from .models import Booking, BookingStatus, PaymentStatus


class BookingFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=BookingStatus.choices)
    payment_status = django_filters.ChoiceFilter(choices=PaymentStatus.choices)
    listing_id = django_filters.UUIDFilter(field_name='listing__id')
    listing_title = django_filters.CharFilter(
        field_name='listing__title',
        lookup_expr='icontains',
    )
    renter_email = django_filters.CharFilter(
        field_name='renter__email',
        lookup_expr='icontains',
    )
    start_date_from = django_filters.DateFilter(
        field_name='start_date',
        lookup_expr='gte',
    )
    start_date_to = django_filters.DateFilter(
        field_name='start_date',
        lookup_expr='lte',
    )
    end_date_from = django_filters.DateFilter(
        field_name='end_date',
        lookup_expr='gte',
    )
    end_date_to = django_filters.DateFilter(
        field_name='end_date',
        lookup_expr='lte',
    )
    created_after = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date__gte',
    )
    created_before = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date__lte',
    )
    min_amount = django_filters.NumberFilter(
        field_name='gross_amount',
        lookup_expr='gte',
    )
    max_amount = django_filters.NumberFilter(
        field_name='gross_amount',
        lookup_expr='lte',
    )

    class Meta:
        model = Booking
        fields = [
            'status', 'payment_status', 'listing_id', 'listing_title',
            'renter_email', 'start_date_from', 'start_date_to',
            'end_date_from', 'end_date_to',
            'created_after', 'created_before',
            'min_amount', 'max_amount',
        ]
```

---

## Step 7: Update the bookings view to use filters, ordering, and pagination

**Open `bookings/views.py`** and replace the `booking_list_create` function's GET handler section with:

```python
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def booking_list_create(request):
    """
    GET: Return user's bookings with filtering, ordering, and pagination.
    POST: Create a booking request (renter role required).
    """
    from .filters import BookingFilter
    from core.pagination import StandardPagination

    if request.method == 'GET':
        role = request.query_params.get('role', 'renter')

        if role == 'owner':
            queryset = Booking.objects.filter(
                owner=request.user
            ).select_related('renter', 'owner', 'listing')
        elif role == 'both':
            from django.db.models import Q
            queryset = Booking.objects.filter(
                Q(renter=request.user) | Q(owner=request.user)
            ).select_related('renter', 'owner', 'listing')
        else:
            queryset = Booking.objects.filter(
                renter=request.user
            ).select_related('renter', 'owner', 'listing')

        # Apply filters
        filterset = BookingFilter(request.query_params, queryset=queryset)
        if not filterset.is_valid():
            return Response(
                {'success': False, 'errors': filterset.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = filterset.qs

        # Apply ordering
        ordering = request.query_params.get('ordering', '-created_at')
        allowed_orderings = [
            'created_at', '-created_at',
            'start_date', '-start_date',
            'end_date', '-end_date',
            'gross_amount', '-gross_amount',
        ]
        if ordering in allowed_orderings:
            queryset = queryset.order_by(ordering)

        # Paginate
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = BookingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    # POST — create booking request (unchanged from Wave 03)
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

    from messaging.services import get_or_create_booking_thread
    get_or_create_booking_thread(booking)

    return Response(
        {'success': True, 'data': BookingSerializer(booking).data},
        status=status.HTTP_201_CREATED,
    )
```

---

## Step 8: Add filter classes to messaging threads

**Create `messaging/filters.py`:**

```python
import django_filters
from .models import Thread


class ThreadFilter(django_filters.FilterSet):
    listing_id = django_filters.UUIDFilter(field_name='listing__id')
    thread_type = django_filters.CharFilter(method='filter_thread_type')
    unread = django_filters.BooleanFilter(method='filter_unread')

    class Meta:
        model = Thread
        fields = ['listing_id', 'thread_type', 'unread']

    def filter_thread_type(self, queryset, name, value):
        if value == 'booking':
            return queryset.filter(booking__isnull=False)
        elif value == 'inquiry':
            return queryset.filter(booking__isnull=True)
        return queryset

    def filter_unread(self, queryset, name, value):
        user = self.request.user
        if value is True:
            from .models import Message
            thread_ids_with_unread = Message.objects.filter(
                is_read=False,
            ).exclude(
                sender=user,
            ).values_list('thread_id', flat=True).distinct()
            return queryset.filter(id__in=thread_ids_with_unread)
        return queryset
```

---

## Step 9: Update the messaging threads view to use filters and pagination

**Open `messaging/views.py`** and replace the `thread_list_create` GET section with:

```python
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def thread_list_create(request):
    """
    GET: List all threads the user is a participant in,
         with filtering and pagination.
    POST: Start an inquiry thread from a listing page.
    """
    from .filters import ThreadFilter
    from core.pagination import StandardPagination

    if request.method == 'GET':
        queryset = (
            Thread.objects
            .filter(participants=request.user)
            .prefetch_related('participants', 'messages')
            .select_related('listing', 'booking')
            .order_by('-updated_at')
        )

        # Apply filters — pass request for user-aware filters
        filterset = ThreadFilter(
            request.query_params,
            queryset=queryset,
            request=request,
        )
        if not filterset.is_valid():
            return Response(
                {'success': False, 'errors': filterset.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = filterset.qs

        # Paginate
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ThreadSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    # POST — start an inquiry thread (unchanged from Wave 03)
    serializer = CreateInquiryThreadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    listing_id = serializer.validated_data['listing_id']
    initial_message = serializer.validated_data['initial_message']

    listing = get_object_or_404(Listing, id=listing_id, status='active')

    if listing.owner == request.user:
        return Response(
            {'success': False, 'errors': 'You cannot send an inquiry to your own listing.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    thread, created = get_or_create_inquiry_thread(listing, request.user)

    message = Message.objects.create(
        thread=thread,
        sender=request.user,
        body=initial_message,
    )

    from django.utils import timezone
    Thread.objects.filter(id=thread.id).update(updated_at=timezone.now())

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
```

---

## Step 10: Add mark-thread-read endpoint to messaging views

**Open `messaging/views.py`** and append the following function at the bottom of the file:

```python
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_thread_read(request, thread_id):
    """Mark all messages in a thread as read for the current user."""
    thread = get_object_or_404(
        Thread,
        id=thread_id,
        participants=request.user,
    )

    updated_count = Message.objects.filter(
        thread=thread,
        is_read=False,
    ).exclude(sender=request.user).update(is_read=True)

    return Response({
        'success': True,
        'messages_marked_read': updated_count,
    })
```

**Open `messaging/urls.py`** and add the import and URL pattern:

Add to imports:
```python
from . import views
```

Add to `urlpatterns`:
```python
path('<uuid:thread_id>/read/', views.mark_thread_read, name='thread-mark-read'),
```

The full `messaging/urls.py` should now be:

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.thread_list_create, name='thread-list-create'),
    path('<uuid:thread_id>/', views.thread_detail, name='thread-detail'),
    path('<uuid:thread_id>/messages/', views.send_message, name='send-message'),
    path('<uuid:thread_id>/read/', views.mark_thread_read, name='thread-mark-read'),
    path('token/', views.get_messaging_token, name='messaging-token'),
]
```

---

## Step 11: Create the `owner` app

```bash
python manage.py startapp owner
```

Add `'owner'` to `LOCAL_APPS` in `config/settings/base.py`.

Add to `config/urls.py` urlpatterns:
```python
path('api/v1/owner/', include('owner.urls')),
```

---

## Step 12: Run migrations for the new OwnerProfile model

```bash
python manage.py makemigrations accounts
python manage.py migrate
```

---

## Step 13: Commit Part 1

```bash
git add .
git commit -m "feat(owner-api): Wave 05 Part 1 — OwnerProfile model, filters, pagination"
```

---

## Part 1 Definition of Done

Verify every item before starting Part 2.

**OwnerProfile model:**
- [ ] `OwnerProfile` exists in `accounts/models.py` with all fields as specified
- [ ] Migration created and applied with no errors
- [ ] Signal auto-creates `OwnerProfile` when `is_owner=True` on a User save
- [ ] `OwnerProfile` visible in Django Admin under Accounts

**Listings filter + pagination:**
- [ ] `GET /api/v1/listings/?status=active` returns only active listings
- [ ] `GET /api/v1/listings/?resource_type=equipment` returns only equipment
- [ ] `GET /api/v1/listings/?city=Lagos` returns listings in Lagos (case-insensitive)
- [ ] `GET /api/v1/listings/?ordering=-view_count` returns sorted by view count desc
- [ ] `GET /api/v1/listings/` response shape includes `count`, `next`, `previous`, `results`

**Bookings filter + pagination:**
- [ ] `GET /api/v1/bookings/?role=owner&status=pending` returns only pending owner bookings
- [ ] `GET /api/v1/bookings/?role=owner&listing_id={uuid}` returns bookings for one listing
- [ ] `GET /api/v1/bookings/?role=owner&start_date_from=2026-06-01` filters by start date
- [ ] `GET /api/v1/bookings/?role=owner&payment_status=unpaid` filters by payment status
- [ ] `GET /api/v1/bookings/` response shape includes `count`, `next`, `previous`, `results`

**Thread filter + pagination:**
- [ ] `GET /api/v1/threads/?unread=true` returns only threads with unread messages
- [ ] `GET /api/v1/threads/?thread_type=booking` returns only booking threads
- [ ] `GET /api/v1/threads/?thread_type=inquiry` returns only inquiry threads
- [ ] `GET /api/v1/threads/?listing_id={uuid}` returns threads for one listing
- [ ] `GET /api/v1/threads/` response shape includes `count`, `next`, `previous`, `results`
- [ ] `PATCH /api/v1/threads/{id}/read/` marks all unread messages as read

**Owner app:**
- [ ] `owner` app created and added to `INSTALLED_APPS`
- [ ] `api/v1/owner/` URL prefix registered in root `config/urls.py`

**Git:**
- [ ] Commit made with message `feat(owner-api): Wave 05 Part 1 — OwnerProfile model, filters, pagination`
