# TERMINAL — WAVE 04: POLISH, INTEGRATION & DEPLOYMENT
> Agent task file. Execute every instruction in order. Do not skip steps.
> Wave 03 must be complete before starting this wave.
> This is the final wave. After this, Terminal MVP is ready for real users.

---

## Context

This wave does not build new features. It closes every open gap in the existing four waves, wires up cross-module integration points, hardens the API, and produces a deployed, production-ready system.

**What this wave covers:**
1. End-to-end integration verification across all modules
2. Missing API responses and edge case fixes
3. Sentry error tracking
4. Production deployment to Railway
5. Final admin panel configuration
6. A populated seed script for internal testing

---

## Step 1: Add missing cross-module signals

When certain events happen, other modules need to react. These are the integration points that cross app boundaries. Use Django signals.

**Create `bookings/signals.py`**:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Booking, BookingStatus


@receiver(post_save, sender=Booking)
def handle_booking_status_change(sender, instance, created, **kwargs):
    """
    When a booking is confirmed, mark the listing as unavailable
    for the booked period (simple approach: mark is_available=False
    if there is at least one active/confirmed booking).

    When a booking is cancelled/declined, check if listing should
    be marked available again.
    """
    from listings.models import Listing

    listing = instance.listing

    if instance.status in [BookingStatus.CONFIRMED, BookingStatus.ACTIVE]:
        # Check if there are any active confirmed bookings
        has_active = Booking.objects.filter(
            listing=listing,
            status__in=[BookingStatus.CONFIRMED, BookingStatus.ACTIVE],
        ).exists()
        if has_active:
            Listing.objects.filter(id=listing.id).update(is_available=False)

    elif instance.status in [BookingStatus.CANCELLED, BookingStatus.DECLINED, BookingStatus.COMPLETED]:
        # If no more active bookings, mark listing as available again
        has_active = Booking.objects.filter(
            listing=listing,
            status__in=[BookingStatus.CONFIRMED, BookingStatus.ACTIVE],
        ).exists()
        if not has_active:
            Listing.objects.filter(id=listing.id).update(is_available=True)
```

**Update `bookings/apps.py`** to connect signals:

```python
from django.apps import AppConfig


class BookingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookings'

    def ready(self):
        import bookings.signals  # noqa
```

---

## Step 2: Add a health check endpoint

**Add to `config/urls.py`** — insert before the existing urlpatterns list:

```python
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'ok', 'service': 'Terminal API'})
```

Add to `urlpatterns`:

```python
path('health/', health_check, name='health-check'),
```

---

## Step 3: Add `unread_count` to the user profile endpoint

The mobile app needs to show a badge with total unread messages. Add this to the user profile response.

**Update `accounts/views/user_views.py`** — in the `me` view's GET handler, replace the return statement with:

```python
if request.method == 'GET':
    from messaging.models import Message
    unread_count = Message.objects.filter(
        thread__participants=user,
        is_read=False,
    ).exclude(sender=user).count()

    serializer = UserProfileSerializer(user)
    data = serializer.data
    data['unread_messages'] = unread_count
    return Response({'success': True, 'data': data})
```

---

## Step 4: Add booking thread link to booking detail response

**Update `bookings/serializers.py`** — add `thread_id` to `BookingSerializer`:

Add this field to the `BookingSerializer` class:

```python
thread_id = serializers.SerializerMethodField()

def get_thread_id(self, obj):
    try:
        return str(obj.thread.id)
    except Exception:
        return None
```

Add `'thread_id'` to the `fields` list in `BookingSerializer.Meta`.

---

## Step 5: Add `Procfile` for Railway deployment

Create `Procfile` in the project root:

```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2
qcluster: python manage.py qcluster
```

---

## Step 6: Add `railway.toml` for Railway configuration

Create `railway.toml` in the project root:

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2"
healthcheckPath = "/health/"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

---

## Step 7: Add `nixpacks.toml` for GeoDjango system library installation

GeoDjango requires GDAL, GEOS, and PROJ. These must be installed as system libraries. Create `nixpacks.toml` in the project root:

```toml
[phases.setup]
nixPkgs = ["gdal", "geos", "proj", "python311"]

[phases.install]
cmds = ["pip install -r requirements/production.txt"]

[phases.build]
cmds = ["python manage.py collectstatic --noinput"]

[start]
cmd = "python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2"
```

---

## Step 8: Configure Sentry in settings

Sentry is already imported in `production.py`. Verify it is configured with your DSN. If `SENTRY_DSN` env var is not set, Sentry initialises silently with no effect.

Add Sentry to `config/settings/development.py` as well (disabled unless DSN provided):

```python
import sentry_sdk
sentry_sdk.init(
    dsn=env('SENTRY_DSN', default=''),
    traces_sample_rate=0.0,
)
```

---

## Step 9: Create the seed data script

Create `scripts/seed.py`. This is a standalone Django management command that populates the database with test data for internal testing.

First, create the directory:

```bash
mkdir -p scripts
touch scripts/__init__.py
```

Create `scripts/seed.py`:

```python
"""
Seed script for Terminal MVP internal testing.

Run with:
    python manage.py shell < scripts/seed.py

Creates:
    - 2 owner accounts
    - 2 renter accounts
    - 1 dual (owner+renter) account
    - 10 listings across all resource types
    - 3 booking requests
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from listings.models import Listing, ResourceType, ListingStatus

User = get_user_model()

print("Seeding Terminal MVP test data...")

# ── Users ──────────────────────────────────────────────────────────────────

owner1, _ = User.objects.get_or_create(
    email='owner1@test.com',
    defaults={
        'first_name': 'Emeka', 'last_name': 'Okafor',
        'phone': '08011111111', 'is_owner': True, 'is_renter': False,
        'is_email_verified': True, 'is_phone_verified': True,
    }
)
if _:
    owner1.set_password('test1234!')
    owner1.save()
    print(f"  Created owner: {owner1.email}")

owner2, _ = User.objects.get_or_create(
    email='owner2@test.com',
    defaults={
        'first_name': 'Ngozi', 'last_name': 'Adeleke',
        'phone': '08022222222', 'is_owner': True, 'is_renter': False,
        'is_email_verified': True, 'is_phone_verified': True,
    }
)
if _:
    owner2.set_password('test1234!')
    owner2.save()
    print(f"  Created owner: {owner2.email}")

renter1, _ = User.objects.get_or_create(
    email='renter1@test.com',
    defaults={
        'first_name': 'Tunde', 'last_name': 'Bello',
        'phone': '08033333333', 'is_owner': False, 'is_renter': True,
        'is_email_verified': True, 'is_phone_verified': True,
    }
)
if _:
    renter1.set_password('test1234!')
    renter1.save()
    print(f"  Created renter: {renter1.email}")

renter2, _ = User.objects.get_or_create(
    email='renter2@test.com',
    defaults={
        'first_name': 'Aisha', 'last_name': 'Musa',
        'phone': '08044444444', 'is_owner': False, 'is_renter': True,
        'is_email_verified': True, 'is_phone_verified': True,
    }
)
if _:
    renter2.set_password('test1234!')
    renter2.save()
    print(f"  Created renter: {renter2.email}")

dual, _ = User.objects.get_or_create(
    email='dual@test.com',
    defaults={
        'first_name': 'Chidi', 'last_name': 'Eze',
        'phone': '08055555555', 'is_owner': True, 'is_renter': True,
        'is_email_verified': True, 'is_phone_verified': True,
    }
)
if _:
    dual.set_password('test1234!')
    dual.save()
    print(f"  Created dual user: {dual.email}")

# ── Listings ──────────────────────────────────────────────────────────────

SEED_LISTINGS = [
    {
        'owner': owner1,
        'resource_type': ResourceType.EQUIPMENT,
        'title': '50T Liebherr Mobile Crane',
        'description': 'Well-maintained 50-tonne mobile crane available for short and long-term lease. Suitable for heavy construction and industrial lifting.',
        'category': 'Mobile Crane',
        'price_daily': 85000,
        'price_weekly': 500000,
        'price_monthly': 1800000,
        'specs': {'tonnage': 50, 'boom_length_m': 42, 'fuel_type': 'diesel'},
        'location': Point(3.3792, 6.5244, srid=4326),  # Lagos Island
        'location_address': '14 Marina Road, Lagos Island',
        'location_city': 'Lagos',
    },
    {
        'owner': owner1,
        'resource_type': ResourceType.EQUIPMENT,
        'title': 'Caterpillar 320 Excavator',
        'description': '20-tonne excavator in excellent condition. Hydraulic thumb available. Suitable for earthmoving, demolition, and foundation work.',
        'category': 'Excavator',
        'price_daily': 55000,
        'price_weekly': 320000,
        'price_monthly': 1100000,
        'specs': {'tonnage': 20, 'bucket_capacity_m3': 0.9, 'fuel_type': 'diesel'},
        'location': Point(3.3547, 6.4698, srid=4326),  # Apapa
        'location_address': '8 Wharf Road, Apapa, Lagos',
        'location_city': 'Lagos',
    },
    {
        'owner': owner2,
        'resource_type': ResourceType.VEHICLE,
        'title': '30T Flatbed Low-Loader Truck',
        'description': 'Heavy-duty low-loader flatbed truck for equipment transport. 30-tonne payload. Available with or without driver.',
        'category': 'Low-Loader Truck',
        'price_daily': 45000,
        'price_weekly': 260000,
        'price_monthly': 900000,
        'specs': {'payload_tonnes': 30, 'axles': 3, 'driver_available': True},
        'location': Point(3.3488, 6.4654, srid=4326),  # Apapa
        'location_address': 'Tin Can Island Port Road, Apapa',
        'location_city': 'Lagos',
    },
    {
        'owner': owner2,
        'resource_type': ResourceType.VEHICLE,
        'title': '20ft ISO Tipper Truck',
        'description': 'Heavy-duty tipper truck for construction aggregates and bulk material. Available for daily and weekly hire.',
        'category': 'Tipper Truck',
        'price_daily': 28000,
        'price_weekly': 160000,
        'specs': {'payload_tonnes': 15, 'body_type': 'rear_tipper'},
        'location': Point(3.3792, 6.4550, srid=4326),  # Victoria Island
        'location_address': 'Ozumba Mbadiwe Avenue, Victoria Island',
        'location_city': 'Lagos',
    },
    {
        'owner': owner1,
        'resource_type': ResourceType.WAREHOUSE,
        'title': 'Bonded Warehouse — Apapa (5,000 sqm)',
        'description': 'Customs-bonded dry goods warehouse near Apapa port. Security, CCTV, 3 loading bays. Ideal for importers.',
        'category': 'Bonded Warehouse',
        'price_monthly': 4500000,
        'specs': {'floor_area_sqm': 5000, 'height_clearance_m': 9, 'loading_bays': 3, 'temperature_controlled': False, 'bonded': True},
        'location': Point(3.3605, 6.4425, srid=4326),  # Near Apapa port
        'location_address': 'Creek Road, Apapa, Lagos',
        'location_city': 'Lagos',
    },
    {
        'owner': owner2,
        'resource_type': ResourceType.WAREHOUSE,
        'title': 'Cold Storage Facility — Ikeja (1,200 sqm)',
        'description': 'Temperature-controlled cold storage. -18°C to +4°C range. Suitable for food, pharma, and perishables. 24/7 power backup.',
        'category': 'Cold Storage',
        'price_monthly': 3200000,
        'specs': {'floor_area_sqm': 1200, 'temperature_range': '-18 to +4°C', 'loading_bays': 2, 'power_backup': True},
        'location': Point(3.3436, 6.6018, srid=4326),  # Ikeja
        'location_address': '45 Oba Akran Avenue, Ikeja',
        'location_city': 'Lagos',
    },
    {
        'owner': owner1,
        'resource_type': ResourceType.TERMINAL,
        'title': 'Container Depot — Tin Can Island (500 TEU)',
        'description': 'Inland container depot adjacent to Tin Can Island Port. RTG crane available. 24/7 access. Gate in/out tracking.',
        'category': 'Container Depot',
        'price_monthly': 12000000,
        'specs': {'capacity_teu': 500, 'crane_available': True, 'crane_type': 'RTG', 'shore_power': False},
        'location': Point(3.3159, 6.4478, srid=4326),  # Tin Can Island
        'location_address': 'Tin Can Island Port, Apapa, Lagos',
        'location_city': 'Lagos',
    },
    {
        'owner': owner2,
        'resource_type': ResourceType.TERMINAL,
        'title': 'Open Container Yard — Ikorodu (200 TEU)',
        'description': 'Secured open container yard in Ikorodu. Suitable for staging, storage, and temporary container holding. Good road access.',
        'category': 'Container Yard',
        'price_monthly': 2800000,
        'specs': {'capacity_teu': 200, 'covered': False, 'security': '24hr guards + CCTV'},
        'location': Point(3.5000, 6.6194, srid=4326),  # Ikorodu
        'location_address': 'Lagos-Ikorodu Road, Ikorodu',
        'location_city': 'Lagos',
    },
    {
        'owner': dual,
        'resource_type': ResourceType.FACILITY,
        'title': 'Secured Equipment Yard — Ojota (2 acres)',
        'description': '2-acre secured compound for equipment parking and staging. Perimeter fencing, gate access control, and 24/7 security. Suitable for construction companies.',
        'category': 'Equipment Yard',
        'price_monthly': 1500000,
        'price_weekly': 420000,
        'specs': {'area_acres': 2, 'fenced': True, 'security': '24hr', 'hardstanding': True},
        'location': Point(3.3833, 6.5800, srid=4326),  # Ojota
        'location_address': '12 Lagos-Ibadan Expressway Service Road, Ojota',
        'location_city': 'Lagos',
    },
    {
        'owner': dual,
        'resource_type': ResourceType.EQUIPMENT,
        'title': 'Manitowoc 999 Crawler Crane — 300T',
        'description': '300-tonne Manitowoc crawler crane for heavy industrial lifts. Fully certified, operator available. Mobilisation costs apply for distances over 100km.',
        'category': 'Crawler Crane',
        'price_daily': 350000,
        'price_weekly': 2000000,
        'specs': {'tonnage': 300, 'type': 'crawler', 'boom_length_m': 90, 'operator_included': True},
        'location': Point(3.3669, 6.5833, srid=4326),  # Oregun
        'location_address': 'Oregun Industrial Estate, Ikeja',
        'location_city': 'Lagos',
    },
]

created_count = 0
for listing_data in SEED_LISTINGS:
    title = listing_data['title']
    if not Listing.objects.filter(title=title).exists():
        Listing.objects.create(
            **listing_data,
            status=ListingStatus.ACTIVE,
            is_available=True,
        )
        created_count += 1
        print(f"  Created listing: {title}")
    else:
        print(f"  Skipped (exists): {title}")

print(f"\nSeed complete.")
print(f"  Users created: 5 (owner1, owner2, renter1, renter2, dual)")
print(f"  Listings created: {created_count}")
print(f"\nTest credentials (all passwords: test1234!):")
print(f"  owner1@test.com  — Owner")
print(f"  owner2@test.com  — Owner")
print(f"  renter1@test.com — Renter")
print(f"  renter2@test.com — Renter")
print(f"  dual@test.com    — Owner + Renter")
print(f"  admin@terminal.app — Django Admin (password: admin1234!)")
```

Run the seed script:

```bash
python manage.py shell < scripts/seed.py
```

---

## Step 10: Final Admin Panel configuration

Update `config/settings/base.py` to add the Unfold admin customisation. Add this block after the `INSTALLED_APPS` definition:

```python
# Django Unfold Admin configuration
UNFOLD = {
    "SITE_TITLE": "Terminal Admin",
    "SITE_HEADER": "Terminal",
    "SITE_SUBHEADER": "Heavy Asset Leasing Platform",
    "SITE_URL": "/",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "COLORS": {
        "primary": {
            "50": "240 249 255",
            "100": "224 242 254",
            "200": "186 230 253",
            "300": "125 211 252",
            "400": "56 189 248",
            "500": "14 165 233",
            "600": "2 132 199",
            "700": "3 105 161",
            "800": "7 89 133",
            "900": "12 74 110",
            "950": "8 47 73",
        },
    },
    "TABS": [
        {
            "models": ["accounts.user"],
            "items": [
                {"title": "All Users", "link": "/admin/accounts/user/"},
                {"title": "Documents", "link": "/admin/accounts/userdocument/"},
            ],
        },
        {
            "models": ["listings.listing"],
            "items": [
                {"title": "All Listings", "link": "/admin/listings/listing/"},
                {"title": "Reports", "link": "/admin/listings/listingreport/"},
            ],
        },
        {
            "models": ["bookings.booking"],
            "items": [
                {"title": "All Bookings", "link": "/admin/bookings/booking/"},
            ],
        },
        {
            "models": ["messaging.thread"],
            "items": [
                {"title": "Threads", "link": "/admin/messaging/thread/"},
            ],
        },
    ],
}
```

---

## Step 11: Run the full integration test

Perform each of these tests manually using Postman, curl, or a REST client. Document any failures and fix before proceeding to deployment.

**Test 1: Full Owner Flow**
```
1. POST /api/v1/auth/register/ with is_owner fields
   → expect 201, tokens returned, OTP printed to console

2. PATCH /api/v1/users/me/role/ with {"is_owner": true}
   → expect 200, role updated

3. POST /api/v1/listings/ with resource_type=equipment, title, price_daily, lat, lng
   → expect 201, listing created with status=draft

4. POST /api/v1/listings/{id}/media/ with a file
   → expect 201, photo uploaded, is_primary=true

5. PATCH /api/v1/listings/{id}/status/ with {"status": "active"}
   → expect 200, listing now active

6. GET /api/v1/search/map/?lat=6.5244&lng=3.3792
   → expect 200, new listing appears in results with distance_km
```

**Test 2: Full Renter + Booking Flow**
```
1. POST /api/v1/auth/register/ as renter
   → expect 201, tokens returned

2. GET /api/v1/search/map/?lat=6.5244&lng=3.3792&resource_type=equipment
   → expect 200, listings returned with distance_km

3. GET /api/v1/listings/{id}/ for a listing from search results
   → expect 200, view_count incremented

4. POST /api/v1/bookings/ with listing_id, start_date (future), end_date, duration_type=daily
   → expect 201, booking created with status=pending
   → check that a thread was automatically created

5. GET /api/v1/threads/ (as renter)
   → expect 200, booking thread appears

6. POST /api/v1/threads/{id}/messages/ with a message body
   → expect 201, message stored
   → check console for [DEV ABLY] output (if no Ably key configured)
```

**Test 3: Owner Accepts Booking**
```
1. Login as the owner of the listing from Test 2

2. GET /api/v1/bookings/?role=owner
   → expect the pending booking to appear

3. PATCH /api/v1/bookings/{id}/accept/
   → expect 200, booking status becomes confirmed
   → check that listing is_available is now False

4. PATCH /api/v1/bookings/{id}/pay/
   → expect 200, payment_status becomes simulated_paid
   → check console for [DEV PAYMENT] output

5. GET /api/v1/threads/{id}/
   → expect 200, thread messages accessible to owner
```

**Test 4: Cancellation and Re-availability**
```
1. PATCH /api/v1/bookings/{id}/cancel/ (as either party)
   → expect 200, booking status becomes cancelled
   → check that listing is_available is now True again

2. GET /api/v1/search/map/?lat=6.5244&lng=3.3792
   → expect cancelled listing to appear in results again (is_available=True)
```

**Test 5: Admin Panel**
```
1. Login at /admin/ with admin@terminal.app / admin1234!
   → expect Unfold theme (not default Django admin)
   → expect Terminal branding in sidebar

2. Verify all five sections work:
   - Users: list, detail, suspend action
   - Listings: list, detail with map widget, activate/pause actions
   - Reports: list, mark reviewed / dismiss actions
   - Bookings: list, detail, cancel action
   - Threads: list, detail with inline messages
```

Fix any failures before proceeding to deployment.

---

## Step 12: Deploy to Railway

**Prerequisites:**
- Railway account created at railway.app
- GitHub repository connected to Railway
- Supabase (or another PostgreSQL with PostGIS) database provisioned

**Environment variables to set in Railway dashboard:**

```
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=<generate a 50-character random string>
DEBUG=False
ALLOWED_HOSTS=<your-railway-domain>.railway.app
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com

DB_NAME=<from Supabase>
DB_USER=<from Supabase>
DB_PASSWORD=<from Supabase>
DB_HOST=<from Supabase>
DB_PORT=5432

R2_ACCESS_KEY_ID=<from Cloudflare R2>
R2_SECRET_ACCESS_KEY=<from Cloudflare R2>
R2_BUCKET_NAME=terminal-uploads
R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
R2_CUSTOM_DOMAIN=<optional CDN domain>

ABLY_API_KEY=<from Ably dashboard>
MAPBOX_ACCESS_TOKEN=<from Mapbox dashboard>
SENTRY_DSN=<from Sentry dashboard>
```

**Deployment steps:**
1. Push the final codebase to the connected GitHub repository
2. Railway auto-deploys from the `railway.toml` configuration
3. Monitor the deployment logs for any migration or startup errors
4. Once live, verify the health endpoint: `GET https://<domain>.railway.app/health/`
5. Verify the API docs are accessible: `GET https://<domain>.railway.app/api/docs/`
6. Run the seed script against the production database:
   ```bash
   railway run python manage.py shell < scripts/seed.py
   ```

---

## Step 13: Final commit

```bash
git add .
git commit -m "chore: Wave 04 — Integration, polish, and deployment ready"
git tag mvp-v1.0
git push origin main --tags
```

---

## Definition of Done

All items must be verified before handing back to supervisor.

**Integration signals:**
- [ ] When a booking is confirmed, the listing's `is_available` changes to `False`
- [ ] When a booking is cancelled or declined, the listing's `is_available` changes back to `True` (if no other active bookings exist)
- [ ] Booking detail response includes `thread_id`
- [ ] User profile response (`GET /api/v1/users/me/`) includes `unread_messages` count

**Health check:**
- [ ] `GET /health/` returns `{"status": "ok", "service": "Terminal API"}`

**Seed data:**
- [ ] `python manage.py shell < scripts/seed.py` runs without errors
- [ ] 5 test users created: owner1, owner2, renter1, renter2, dual
- [ ] 10 listings created, all with `status=active`, `location` set, across all 5 resource types
- [ ] All listings appear in `GET /api/v1/search/map/?lat=6.5244&lng=3.3792` results

**Integration tests (all 4 test flows from Step 11):**
- [ ] Test 1: Full owner flow — register, list, publish, appears on map ✓
- [ ] Test 2: Full renter flow — browse map, view listing, create booking, message ✓
- [ ] Test 3: Owner accepts booking — confirmed, listing unavailable, mark paid ✓
- [ ] Test 4: Cancellation — listing becomes available again, reappears on map ✓
- [ ] Test 5: Admin panel — all five sections work with Unfold theme ✓

**Deployment:**
- [ ] `GET https://<domain>.railway.app/health/` returns `{"status": "ok"}`
- [ ] `GET https://<domain>.railway.app/api/docs/` loads Swagger UI
- [ ] Migrations ran automatically on deploy
- [ ] Seed data loaded against production database
- [ ] Photos upload to Cloudflare R2 (test one upload from production)
- [ ] Sentry is receiving errors (trigger a 500 intentionally, verify it appears in Sentry)

**Admin panel:**
- [ ] `/admin/` loads with Unfold theme and Terminal branding
- [ ] All seed listings visible in admin
- [ ] All seed users visible in admin
- [ ] Map widget renders on Listing detail in admin

**Git:**
- [ ] Final commit made with message `chore: Wave 04 — Integration, polish, and deployment ready`
- [ ] Tag `mvp-v1.0` created and pushed

---

## Post-Deploy Handoff Notes for Supervisor

Terminal MVP is now live. The following simulation placeholders are active and will need to be replaced when building Phase 2:

| Simulation | Where it lives | How to identify |
|---|---|---|
| OTP via console | `accounts/services.py` → `create_otp()` | `[DEV OTP]` in logs |
| Auto KYC approval | `accounts/services.py` → `process_document_upload()` | `[DEV KYC]` in logs |
| Simulated payment | `bookings/views.py` → `booking_mark_paid()` | `[DEV PAYMENT]` in logs |
| Ably fallback | `messaging/services.py` → `publish_to_ably()` | `[DEV ABLY]` in logs |

All database schema for post-MVP features (commission tracking, payment status, verification levels) is already in place. No migrations will be needed for Phase 2 financial features.

The API documentation is live at `/api/docs/`. Share this URL with the mobile frontend team.
