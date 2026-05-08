# TERMINAL — WAVE 00: PROJECT SETUP
> Agent task file. Execute every instruction in order. Do not skip steps.
> Do not proceed to Wave 01 until the Definition of Done checklist is fully complete.

---

## Context

You are building **Terminal** — a Django REST API backend for a heavy asset leasing marketplace. The platform connects owners of heavy equipment, vehicles, warehouses, terminals, and container yards with renters. It is a facilitation platform only — it does not own or operate any assets.

This wave sets up the entire project skeleton. All subsequent waves build on top of this.

---

## Step 1: Create the Django project

Run the following commands exactly:

```bash
mkdir terminal && cd terminal
python -m venv venv
source venv/bin/activate
pip install django djangorestframework djangorestframework-simplejwt django-environ django-cors-headers django-unfold drf-spectacular django-storages boto3 django-q2 django-filter Pillow sentry-sdk ably
pip freeze > requirements/base.txt
django-admin startproject config .
```

---

## Step 2: Create the app directory structure

Create the following Django apps by running exactly:

```bash
python manage.py startapp core
python manage.py startapp accounts
python manage.py startapp listings
python manage.py startapp search
python manage.py startapp bookings
python manage.py startapp messaging
```

---

## Step 3: Create requirements files

Create `requirements/base.txt` with the following content exactly:

```
django>=5.0,<6.0
djangorestframework>=3.15
djangorestframework-simplejwt>=5.3
django-environ>=0.11
django-cors-headers>=4.3
django-unfold>=0.30
drf-spectacular>=0.27
django-storages>=1.14
boto3>=1.34
django-q2>=1.6
django-filter>=23.5
Pillow>=10.2
sentry-sdk[django]>=1.40
ably>=2.0
```

Create `requirements/development.txt` with:

```
-r base.txt
django-debug-toolbar>=4.3
```

Create `requirements/production.txt` with:

```
-r base.txt
gunicorn>=21.2
psycopg2-binary>=2.9
```

---

## Step 4: Create settings files

Delete the file `config/settings.py`.

Create the directory `config/settings/` and create three files inside it.

**File: `config/settings/__init__.py`**
Leave this file empty.

**File: `config/settings/base.py`**

```python
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)

environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

DJANGO_APPS = [
    'unfold',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'django_q',
    'storages',
]

LOCAL_APPS = [
    'core',
    'accounts',
    'listings',
    'search',
    'bookings',
    'messaging',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'TOKEN_OBTAIN_SERIALIZER': 'accounts.serializers.CustomTokenObtainPairSerializer',
}

# DRF Spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'Terminal API',
    'DESCRIPTION': 'Heavy asset leasing marketplace API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# CORS
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_ALL_ORIGINS = env.bool('CORS_ALLOW_ALL_ORIGINS', default=False)

# Storage - Cloudflare R2
AWS_ACCESS_KEY_ID = env('R2_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = env('R2_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = env('R2_BUCKET_NAME', default='terminal-uploads')
AWS_S3_ENDPOINT_URL = env('R2_ENDPOINT_URL', default='')
AWS_S3_CUSTOM_DOMAIN = env('R2_CUSTOM_DOMAIN', default='')
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
AWS_QUERYSTRING_AUTH = False

# Django Q
Q_CLUSTER = {
    'name': 'terminal',
    'workers': 2,
    'recycle': 500,
    'timeout': 60,
    'compress': True,
    'save_limit': 250,
    'queue_limit': 500,
    'cpu_affinity': 1,
    'label': 'Django Q',
    'orm': 'default',
}

# Ably
ABLY_API_KEY = env('ABLY_API_KEY', default='')

# Mapbox
MAPBOX_ACCESS_TOKEN = env('MAPBOX_ACCESS_TOKEN', default='')
```

**File: `config/settings/development.py`**

```python
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']
CORS_ALLOW_ALL_ORIGINS = True

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': env('DB_NAME', default='terminal_dev'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default='postgres'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**File: `config/settings/production.py`**

```python
from .base import *

DEBUG = False
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

import sentry_sdk
sentry_sdk.init(
    dsn=env('SENTRY_DSN', default=''),
    traces_sample_rate=0.1,
)

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

---

## Step 5: Update `config/urls.py`

Replace the entire content of `config/urls.py` with:

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/auth/', include('accounts.urls.auth')),
    path('api/v1/users/', include('accounts.urls.users')),
    path('api/v1/listings/', include('listings.urls')),
    path('api/v1/search/', include('search.urls')),
    path('api/v1/bookings/', include('bookings.urls')),
    path('api/v1/threads/', include('messaging.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## Step 6: Update `manage.py`

Replace the `os.environ.setdefault` line in `manage.py` with:

```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
```

---

## Step 7: Create the `.env` file

Create `.env` in the project root with:

```
SECRET_KEY=django-insecure-change-this-in-production-use-50-chars-minimum
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOW_ALL_ORIGINS=True

DB_NAME=terminal_dev
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=terminal-uploads
R2_ENDPOINT_URL=
R2_CUSTOM_DOMAIN=

ABLY_API_KEY=
MAPBOX_ACCESS_TOKEN=
SENTRY_DSN=
```

Create `.env.example` with the same content. Add `.env` to `.gitignore`.

---

## Step 8: Create `core` app files

**File: `core/models.py`**

```python
import uuid
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

**File: `core/permissions.py`**

```python
from rest_framework.permissions import BasePermission


class IsOwnerRole(BasePermission):
    """Allows access only to users who have the owner role enabled."""
    message = 'You must enable the owner role to perform this action.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_owner)


class IsRenterRole(BasePermission):
    """Allows access only to users who have the renter role enabled."""
    message = 'You must enable the renter role to perform this action.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_renter)


class IsObjectOwner(BasePermission):
    """Allows access only to the owner of the specific object."""
    message = 'You do not have permission to modify this object.'

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
```

**File: `core/pagination.py`**

```python
from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
```

**File: `core/exceptions.py`**

```python
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            'success': False,
            'errors': response.data,
            'status_code': response.status_code,
        }

    return response
```

Add to `config/settings/base.py` inside `REST_FRAMEWORK` dict:
```python
'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
```

**File: `core/admin.py`**

```python
from django.contrib import admin
```

**File: `core/apps.py`** — ensure `name = 'core'`

---

## Step 9: Create placeholder `urls.py` in each app

For each app that is not yet built — `listings`, `search`, `bookings`, `messaging` — create a `urls.py` with:

```python
from django.urls import path

urlpatterns = []
```

For `accounts`, create two files:

**`accounts/urls/__init__.py`** — empty

**`accounts/urls/auth.py`**

```python
from django.urls import path

urlpatterns = []
```

**`accounts/urls/users.py`**

```python
from django.urls import path

urlpatterns = []
```

---

## Step 10: Verify the setup runs

Run:

```bash
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py check
```

This must return `System check identified no issues (0 silenced).`

If it fails due to missing database — that is expected and acceptable. If it fails due to import errors or misconfiguration — fix before proceeding.

---

## Step 11: Create `.gitignore`

Create `.gitignore` in the project root:

```
venv/
__pycache__/
*.pyc
*.pyo
.env
*.sqlite3
media/
staticfiles/
.DS_Store
*.egg-info/
dist/
build/
.pytest_cache/
htmlcov/
.coverage
```

---

## Step 12: Initialize git

```bash
git init
git add .
git commit -m "chore: initial project setup — Wave 00"
```

---

## Definition of Done

Verify every item before handing back to supervisor.

- [ ] `python manage.py check` runs with 0 issues (database errors acceptable)
- [ ] Directory structure matches exactly: `config/`, `core/`, `accounts/`, `listings/`, `search/`, `bookings/`, `messaging/`
- [ ] `config/settings/` contains `__init__.py`, `base.py`, `development.py`, `production.py`
- [ ] `requirements/` contains `base.txt`, `development.txt`, `production.txt`
- [ ] `core/models.py` contains `BaseModel` with `id` (UUID), `created_at`, `updated_at`
- [ ] `core/permissions.py` contains `IsOwnerRole`, `IsRenterRole`, `IsObjectOwner`
- [ ] `core/pagination.py` contains `StandardPagination`
- [ ] `core/exceptions.py` contains `custom_exception_handler`
- [ ] `config/urls.py` includes all six app URL namespaces
- [ ] `.env` file exists and is in `.gitignore`
- [ ] `.env.example` exists and is committed
- [ ] Initial git commit is made with message `chore: initial project setup — Wave 00`
