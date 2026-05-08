# TERMINAL — WAVE 02: LISTINGS + SEARCH
> Agent task file. Execute every instruction in order. Do not skip steps.
> Wave 01 must be complete before starting this wave.
> Do not proceed to Wave 03 until the Definition of Done checklist is fully complete.

---

## Context

This wave builds the `listings` app (all five resource types) and the `search` app (GeoDjango map search with distance). This is the first wave where Terminal looks and functions like a real product.

**Critical requirement:** The database must have PostGIS enabled before running migrations. Confirm this before starting Step 1. If using Supabase, PostGIS is enabled by default. If using a local PostgreSQL, run `CREATE EXTENSION postgis;` in your database.

**Simulation decisions (do not deviate):**
- All new listings are automatically assigned `verification_tier = 'basic'`. Do not build a moderation or verification queue.
- Listing reports are stored in the database but no automated action is taken.
- The search endpoint queries PostgreSQL + PostGIS directly. Do NOT add Meilisearch, Elasticsearch, or any external search service.

---

## Step 1: Verify PostGIS is available

Run this in your PostgreSQL database before writing any code:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
SELECT PostGIS_Version();
```

The second query must return a version string (e.g., `3.4.0 ...`). If it fails, PostGIS is not installed. Do not proceed until PostGIS is working.

Also verify that `django.contrib.gis` is in `INSTALLED_APPS` (it was set in Wave 00 base settings).

Install the required system libraries if not already installed:

```bash
# Ubuntu/Debian
sudo apt-get install -y gdal-bin libgdal-dev libgeos-dev libproj-dev

# macOS
brew install gdal geos proj
```

---

## Step 2: Create the Listings models

**File: `listings/models.py`**

```python
import uuid
from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models

from core.models import BaseModel


class ResourceType(models.TextChoices):
    EQUIPMENT = 'equipment', 'Heavy Equipment'
    VEHICLE = 'vehicle', 'Vehicle & Transport'
    WAREHOUSE = 'warehouse', 'Warehouse'
    TERMINAL = 'terminal', 'Terminal & Container Yard'
    FACILITY = 'facility', 'Facility & Staging Area'


class ListingStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    ACTIVE = 'active', 'Active'
    PAUSED = 'paused', 'Paused'
    ARCHIVED = 'archived', 'Archived'


class VerificationTier(models.TextChoices):
    BASIC = 'basic', 'Basic'
    VERIFIED = 'verified', 'Verified'
    INSPECTED = 'inspected', 'Inspected'


class Listing(BaseModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings',
    )
    resource_type = models.CharField(
        max_length=20,
        choices=ResourceType.choices,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    category = models.CharField(max_length=100, blank=True, default='')

    # Pricing
    price_daily = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    price_weekly = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    price_monthly = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # Type-specific specifications
    specs = models.JSONField(default=dict, blank=True)

    # Location — required to publish
    # geography=True means distances are calculated in metres (accurate)
    location = gis_models.PointField(geography=True, null=True, blank=True)
    location_address = models.TextField(blank=True, default='')
    location_city = models.CharField(max_length=100, blank=True, default='')

    # Options
    operator_available = models.BooleanField(default=False)
    delivery_available = models.BooleanField(default=False)

    # Status
    status = models.CharField(
        max_length=20,
        choices=ListingStatus.choices,
        default=ListingStatus.DRAFT,
    )
    is_available = models.BooleanField(default=True)
    verification_tier = models.CharField(
        max_length=20,
        choices=VerificationTier.choices,
        default=VerificationTier.BASIC,
    )

    # Metrics
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'listings'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.resource_type}) — {self.owner.email}"

    @property
    def primary_photo_url(self):
        primary = self.media.filter(is_primary=True).first()
        if primary:
            return primary.file.url
        first = self.media.first()
        return first.file.url if first else None

    @property
    def latitude(self):
        return self.location.y if self.location else None

    @property
    def longitude(self):
        return self.location.x if self.location else None


class ListingMedia(BaseModel):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='media',
    )
    file = models.ImageField(upload_to='listings/')
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'listing_media'
        ordering = ['display_order', 'created_at']

    def __str__(self):
        return f"Media for {self.listing.title}"

    def save(self, *args, **kwargs):
        # If this is set as primary, unset all other primary photos for this listing
        if self.is_primary:
            ListingMedia.objects.filter(
                listing=self.listing,
                is_primary=True,
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


class ListingReport(BaseModel):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='reports',
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_reports',
    )

    REASON_FAKE = 'fake'
    REASON_STOLEN = 'stolen'
    REASON_MISLEADING = 'misleading'
    REASON_SPAM = 'spam'
    REASON_OTHER = 'other'
    REASON_CHOICES = [
        (REASON_FAKE, 'Fake listing'),
        (REASON_STOLEN, 'Stolen equipment'),
        (REASON_MISLEADING, 'Misleading information'),
        (REASON_SPAM, 'Spam'),
        (REASON_OTHER, 'Other'),
    ]
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True, default='')

    STATUS_PENDING = 'pending'
    STATUS_REVIEWED = 'reviewed'
    STATUS_DISMISSED = 'dismissed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_REVIEWED, 'Reviewed'),
        (STATUS_DISMISSED, 'Dismissed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    class Meta:
        db_table = 'listing_reports'
        ordering = ['-created_at']
        # One report per user per listing
        unique_together = [['listing', 'reporter']]

    def __str__(self):
        return f"Report: {self.listing.title} by {self.reporter.email}"
```

---

## Step 3: Create the listings serializers

**File: `listings/serializers.py`**

```python
from rest_framework import serializers
from django.contrib.gis.geos import Point

from .models import Listing, ListingMedia, ListingReport, ResourceType


class ListingMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ListingMedia
        fields = ['id', 'file_url', 'is_primary', 'display_order', 'created_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None


class ListingOwnerSerializer(serializers.Serializer):
    """Minimal owner info embedded in listing responses."""
    id = serializers.UUIDField()
    full_name = serializers.CharField()
    profile_photo = serializers.ImageField()
    verification_level = serializers.IntegerField()


class ListingSerializer(serializers.ModelSerializer):
    """Full listing detail — used for detail and owner list views."""
    owner = ListingOwnerSerializer(read_only=True)
    media = ListingMediaSerializer(many=True, read_only=True)
    primary_photo_url = serializers.ReadOnlyField()
    latitude = serializers.ReadOnlyField()
    longitude = serializers.ReadOnlyField()

    class Meta:
        model = Listing
        fields = [
            'id', 'owner', 'resource_type', 'title', 'description', 'category',
            'price_daily', 'price_weekly', 'price_monthly', 'specs',
            'latitude', 'longitude', 'location_address', 'location_city',
            'operator_available', 'delivery_available',
            'status', 'is_available', 'verification_tier',
            'view_count', 'primary_photo_url', 'media',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'verification_tier', 'view_count', 'created_at', 'updated_at']


class CreateListingSerializer(serializers.ModelSerializer):
    """Used for creating and updating listings."""
    latitude = serializers.FloatField(write_only=True, required=False, allow_null=True)
    longitude = serializers.FloatField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Listing
        fields = [
            'resource_type', 'title', 'description', 'category',
            'price_daily', 'price_weekly', 'price_monthly', 'specs',
            'latitude', 'longitude', 'location_address', 'location_city',
            'operator_available', 'delivery_available',
        ]

    def validate(self, attrs):
        lat = attrs.pop('latitude', None)
        lng = attrs.pop('longitude', None)

        if lat is not None and lng is not None:
            attrs['location'] = Point(lng, lat, srid=4326)

        return attrs

    def validate_resource_type(self, value):
        if value not in [choice[0] for choice in ResourceType.choices]:
            raise serializers.ValidationError(f"Invalid resource type: {value}")
        return value


class UpdateListingStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ['status']

    def validate_status(self, value):
        instance = self.instance
        # Cannot publish without a location
        if value == 'active' and not instance.location:
            raise serializers.ValidationError(
                'A listing must have a location set before it can be published.'
            )
        # Cannot publish without at least one photo
        if value == 'active' and not instance.media.exists():
            raise serializers.ValidationError(
                'A listing must have at least one photo before it can be published.'
            )
        return value


class ListingReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingReport
        fields = ['reason', 'description']
```

---

## Step 4: Create listings views

**File: `listings/views.py`**

```python
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from core.permissions import IsOwnerRole, IsObjectOwner
from .models import Listing, ListingMedia, ListingReport
from .serializers import (
    ListingSerializer,
    CreateListingSerializer,
    UpdateListingStatusSerializer,
    ListingReportSerializer,
)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def listing_list_create(request):
    """
    GET: Return the authenticated owner's own listings.
    POST: Create a new listing (owner role required).
    """
    if request.method == 'GET':
        listings = Listing.objects.filter(owner=request.user).prefetch_related('media')
        serializer = ListingSerializer(listings, many=True, context={'request': request})
        return Response({'success': True, 'data': serializer.data})

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


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def listing_detail(request, listing_id):
    """
    GET: Public listing detail (increments view count).
    PUT/PATCH: Update listing (owner only).
    DELETE: Archive listing (owner only).
    """
    listing = get_object_or_404(Listing.objects.prefetch_related('media', 'owner'), id=listing_id)

    if request.method == 'GET':
        # Increment view count
        Listing.objects.filter(id=listing_id).update(view_count=listing.view_count + 1)
        listing.refresh_from_db(fields=['view_count'])
        serializer = ListingSerializer(listing, context={'request': request})
        return Response({'success': True, 'data': serializer.data})

    # Mutating operations — owner only
    if listing.owner != request.user:
        return Response(
            {'success': False, 'errors': 'You do not have permission to modify this listing.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method in ['PUT', 'PATCH']:
        serializer = CreateListingSerializer(
            listing, data=request.data, partial=(request.method == 'PATCH')
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'data': ListingSerializer(listing, context={'request': request}).data,
        })

    if request.method == 'DELETE':
        listing.status = 'archived'
        listing.save(update_fields=['status'])
        return Response({'success': True, 'message': 'Listing archived.'})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def listing_status(request, listing_id):
    """Update listing status (publish, pause, archive)."""
    listing = get_object_or_404(Listing, id=listing_id, owner=request.user)

    serializer = UpdateListingStatusSerializer(listing, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({
        'success': True,
        'message': f"Listing status updated to '{listing.status}'.",
        'data': {'status': listing.status},
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_media(request, listing_id):
    """Upload a photo to a listing. Owner only."""
    listing = get_object_or_404(Listing, id=listing_id, owner=request.user)

    if 'file' not in request.FILES:
        return Response(
            {'success': False, 'errors': 'No file provided.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    media_file = request.FILES['file']
    is_primary = request.data.get('is_primary', 'false').lower() == 'true'

    # First photo uploaded is automatically primary
    if not listing.media.exists():
        is_primary = True

    media = ListingMedia.objects.create(
        listing=listing,
        file=media_file,
        is_primary=is_primary,
        display_order=listing.media.count(),
    )

    return Response({
        'success': True,
        'data': {
            'id': str(media.id),
            'file_url': request.build_absolute_uri(media.file.url),
            'is_primary': media.is_primary,
        },
    }, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_media(request, listing_id, media_id):
    """Delete a photo from a listing. Owner only."""
    listing = get_object_or_404(Listing, id=listing_id, owner=request.user)
    media = get_object_or_404(ListingMedia, id=media_id, listing=listing)
    media.delete()
    return Response({'success': True, 'message': 'Photo removed.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_listing(request, listing_id):
    """Report a listing."""
    listing = get_object_or_404(Listing, id=listing_id)

    # Cannot report your own listing
    if listing.owner == request.user:
        return Response(
            {'success': False, 'errors': 'You cannot report your own listing.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check for existing report
    if ListingReport.objects.filter(listing=listing, reporter=request.user).exists():
        return Response(
            {'success': False, 'errors': 'You have already reported this listing.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ListingReportSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(listing=listing, reporter=request.user)

    return Response({
        'success': True,
        'message': 'Report submitted. Our team will review it.',
    }, status=status.HTTP_201_CREATED)
```

---

## Step 5: Wire up Listings URLs

**File: `listings/urls.py`**

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.listing_list_create, name='listing-list-create'),
    path('<uuid:listing_id>/', views.listing_detail, name='listing-detail'),
    path('<uuid:listing_id>/status/', views.listing_status, name='listing-status'),
    path('<uuid:listing_id>/media/', views.upload_media, name='listing-upload-media'),
    path('<uuid:listing_id>/media/<uuid:media_id>/', views.delete_media, name='listing-delete-media'),
    path('<uuid:listing_id>/report/', views.report_listing, name='listing-report'),
]
```

---

## Step 6: Create Search views

**File: `search/views.py`**

```python
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from listings.models import Listing, ResourceType
from .serializers import MapSearchResultSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def map_search(request):
    """
    Search for active listings within a radius of the given coordinates.

    Query params:
        lat (float, required): User latitude
        lng (float, required): User longitude
        radius (int, optional): Search radius in km. Default: 50. Max: 500.
        resource_type (str, optional): Filter by resource type.
        available (bool, optional): Filter by availability. Default: true.
    """
    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')

    if not lat or not lng:
        return Response(
            {'success': False, 'errors': 'lat and lng query parameters are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        lat = float(lat)
        lng = float(lng)
    except ValueError:
        return Response(
            {'success': False, 'errors': 'lat and lng must be valid numbers.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        return Response(
            {'success': False, 'errors': 'Invalid coordinates.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        radius_km = min(int(request.query_params.get('radius', 50)), 500)
    except ValueError:
        radius_km = 50

    resource_type = request.query_params.get('resource_type')
    available_param = request.query_params.get('available', 'true').lower()
    filter_available = available_param == 'true'

    # Build the user's point
    user_location = Point(lng, lat, srid=4326)

    # Base queryset — only active listings with a location set
    queryset = Listing.objects.filter(
        status='active',
        location__isnull=False,
    ).select_related('owner').prefetch_related('media')

    # Filter by availability
    if filter_available:
        queryset = queryset.filter(is_available=True)

    # Filter by resource type
    if resource_type:
        valid_types = [choice[0] for choice in ResourceType.choices]
        if resource_type not in valid_types:
            return Response(
                {'success': False, 'errors': f"Invalid resource_type. Valid values: {valid_types}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = queryset.filter(resource_type=resource_type)

    # Filter by radius and annotate distance
    queryset = (
        queryset
        .filter(location__distance_lte=(user_location, D(km=radius_km)))
        .annotate(distance=Distance('location', user_location))
        .order_by('distance')
    )

    serializer = MapSearchResultSerializer(
        queryset,
        many=True,
        context={'request': request},
    )

    return Response({
        'success': True,
        'count': queryset.count(),
        'radius_km': radius_km,
        'data': serializer.data,
    })
```

---

## Step 7: Create Search serializers

**File: `search/serializers.py`**

```python
from rest_framework import serializers
from listings.models import Listing


class MapSearchResultSerializer(serializers.ModelSerializer):
    """
    Lightweight listing serializer for map search results.
    Includes distance_km — only present when annotated by the search view.
    """
    distance_km = serializers.SerializerMethodField()
    primary_photo_url = serializers.ReadOnlyField()
    latitude = serializers.ReadOnlyField()
    longitude = serializers.ReadOnlyField()
    owner_name = serializers.SerializerMethodField()
    owner_photo = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'id', 'resource_type', 'title', 'category',
            'price_daily', 'price_weekly', 'price_monthly',
            'latitude', 'longitude', 'location_address', 'location_city',
            'is_available', 'verification_tier',
            'primary_photo_url', 'distance_km',
            'owner_name', 'owner_photo',
        ]

    def get_distance_km(self, obj):
        if hasattr(obj, 'distance') and obj.distance is not None:
            return round(obj.distance.km, 2)
        return None

    def get_owner_name(self, obj):
        return obj.owner.full_name if obj.owner else None

    def get_owner_photo(self, obj):
        request = self.context.get('request')
        if obj.owner and obj.owner.profile_photo:
            if request:
                return request.build_absolute_uri(obj.owner.profile_photo.url)
            return obj.owner.profile_photo.url
        return None
```

---

## Step 8: Wire up Search URLs

**File: `search/urls.py`**

```python
from django.urls import path
from . import views

urlpatterns = [
    path('map/', views.map_search, name='search-map'),
]
```

---

## Step 9: Register Listings in Django Admin

**File: `listings/admin.py`**

```python
from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from unfold.admin import ModelAdmin

from .models import Listing, ListingMedia, ListingReport


class ListingMediaInline(admin.TabularInline):
    model = ListingMedia
    extra = 0
    readonly_fields = ['id', 'created_at']


@admin.register(Listing)
class ListingAdmin(OSMGeoAdmin, ModelAdmin):
    list_display = [
        'title', 'resource_type', 'owner', 'location_city',
        'status', 'is_available', 'verification_tier', 'view_count', 'created_at',
    ]
    list_filter = ['resource_type', 'status', 'is_available', 'verification_tier']
    search_fields = ['title', 'owner__email', 'location_city']
    readonly_fields = ['id', 'view_count', 'created_at', 'updated_at']
    inlines = [ListingMediaInline]
    ordering = ['-created_at']

    actions = ['activate_listings', 'pause_listings', 'archive_listings']

    @admin.action(description='Activate selected listings')
    def activate_listings(self, request, queryset):
        queryset.filter(location__isnull=False).update(status='active')

    @admin.action(description='Pause selected listings')
    def pause_listings(self, request, queryset):
        queryset.update(status='paused')

    @admin.action(description='Archive selected listings')
    def archive_listings(self, request, queryset):
        queryset.update(status='archived')


@admin.register(ListingReport)
class ListingReportAdmin(ModelAdmin):
    list_display = ['listing', 'reporter', 'reason', 'status', 'created_at']
    list_filter = ['reason', 'status']
    search_fields = ['listing__title', 'reporter__email']
    readonly_fields = ['id', 'created_at']

    actions = ['mark_reviewed', 'dismiss_reports']

    @admin.action(description='Mark selected reports as reviewed')
    def mark_reviewed(self, request, queryset):
        queryset.update(status='reviewed')

    @admin.action(description='Dismiss selected reports')
    def dismiss_reports(self, request, queryset):
        queryset.update(status='dismissed')
```

---

## Step 10: Update `listings/apps.py`

```python
from django.apps import AppConfig


class ListingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'listings'
```

---

## Step 11: Update `search/apps.py`

```python
from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'search'
```

---

## Step 12: Create and run migrations

```bash
python manage.py makemigrations listings
python manage.py migrate
```

If migration fails with a PostGIS error, stop and resolve the PostGIS installation before proceeding.

---

## Step 13: Commit

```bash
git add .
git commit -m "feat(listings,search): Wave 02 — Listings and Map Search complete"
```

---

## Definition of Done

Verify every item before handing back to supervisor.

**PostGIS:**
- [ ] `SELECT PostGIS_Version();` returns a version string in the database
- [ ] Migrations ran successfully with no errors

**Listing Model:**
- [ ] `Listing.location` is a `PointField(geography=True)` — not a CharField, not two FloatFields
- [ ] `ResourceType` TextChoices contains exactly: `equipment`, `vehicle`, `warehouse`, `terminal`, `facility`
- [ ] `ListingStatus` TextChoices contains: `draft`, `active`, `paused`, `archived`
- [ ] `Listing.specs` is a `JSONField`
- [ ] `ListingMedia` model exists with `file`, `is_primary`, `display_order`
- [ ] `ListingReport` model exists with `reason`, `status`, `unique_together` on listing+reporter

**Listing API endpoints (test with curl or Postman):**
- [ ] `GET /api/v1/listings/` (authenticated) → returns owner's listings
- [ ] `POST /api/v1/listings/` → creates a listing (owner role required)
- [ ] `GET /api/v1/listings/{id}/` (public) → returns listing detail, increments view_count
- [ ] `PATCH /api/v1/listings/{id}/` → updates listing (owner only, 403 for others)
- [ ] `DELETE /api/v1/listings/{id}/` → archives listing (owner only, 403 for others)
- [ ] `PATCH /api/v1/listings/{id}/status/` → changes status; rejects `active` if no location or no photos
- [ ] `POST /api/v1/listings/{id}/media/` → uploads a photo, first photo is auto-primary
- [ ] `DELETE /api/v1/listings/{id}/media/{media_id}/` → removes a photo
- [ ] `POST /api/v1/listings/{id}/report/` → submits a report, blocks duplicate reports

**Search API:**
- [ ] `GET /api/v1/search/map/?lat=6.5244&lng=3.3792` → returns listings with `distance_km` field
- [ ] `GET /api/v1/search/map/?lat=6.5244&lng=3.3792&radius=20` → respects radius
- [ ] `GET /api/v1/search/map/?lat=6.5244&lng=3.3792&resource_type=equipment` → filters by type
- [ ] Results are ordered by distance ascending (nearest first)
- [ ] Results missing `lat` or `lng` params return 400 with clear error
- [ ] `distance_km` is a rounded float (e.g., `3.24`) not a raw value

**Listing publishing rules:**
- [ ] A listing with no location cannot be set to `active` (returns 400 with clear error)
- [ ] A listing with no photos cannot be set to `active` (returns 400 with clear error)
- [ ] All new listings have `verification_tier = 'basic'` by default

**Django Admin:**
- [ ] Listing list shows: title, resource_type, owner, city, status, view_count
- [ ] Listing detail shows the map widget (OSMGeoAdmin) for the location field
- [ ] Activate / Pause / Archive bulk actions work
- [ ] ListingReport list shows report reason and status
- [ ] Mark reviewed / Dismiss bulk actions work on reports

**General:**
- [ ] `python manage.py check` returns 0 issues
- [ ] Git commit made with message `feat(listings,search): Wave 02 — Listings and Map Search complete`
