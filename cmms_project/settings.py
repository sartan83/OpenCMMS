"""
Django settings for CMMS project.
Computerized Maintenance Management System / Total Productive Maintenance
"""

from pathlib import Path
from datetime import timedelta
import os
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

from cmms_common.auth.keys import load_private_key, load_public_key
from cmms_common.logging import build_logging_config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = (os.environ.get('DEBUG') or 'True').lower() == 'true'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-cmms-dev-key-change-in-production'
    else:
        raise ImproperlyConfigured('SECRET_KEY must be set when DEBUG is false')

ALLOWED_HOSTS = (os.environ.get('ALLOWED_HOSTS') or '*').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_celery_beat',
    # Local apps
    'assets',
    'maintenance',
    'workorders',
    'inspections',
    'spareparts',
    'users',
    'reports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cmms_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'cmms_project.wsgi.application'

# Database
database_url = os.environ.get('DATABASE_URL') or None
if database_url:
    parsed_database_url = urlparse(database_url)
    if parsed_database_url.scheme not in {'postgres', 'postgresql'}:
        raise ImproperlyConfigured('DATABASE_URL must use postgres or postgresql')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed_database_url.path.lstrip('/'),
            'USER': unquote(parsed_database_url.username or ''),
            'PASSWORD': unquote(parsed_database_url.password or ''),
            'HOST': parsed_database_url.hostname or '',
            'PORT': str(parsed_database_url.port or 5432),
        }
    }
elif os.environ.get('POSTGRES_HOST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB') or 'cmms',
            'USER': os.environ.get('POSTGRES_USER') or 'cmms',
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD') or 'cmms',
            'HOST': os.environ.get('POSTGRES_HOST') or 'localhost',
            'PORT': os.environ.get('POSTGRES_PORT') or '5432',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 20,
            },
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}
if os.environ.get('JWT_PUBLIC_KEY_PATH'):
    SIMPLE_JWT.update({
        'ALGORITHM': 'RS256',
        'VERIFYING_KEY': load_public_key(),
        'SIGNING_KEY': load_private_key() if os.environ.get('JWT_PRIVATE_KEY_PATH') else None,
    })

# CORS Settings - Allow all origins for development/deployment flexibility
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = (os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,'
    'http://127.0.0.1:8080,http://localhost:8000,http://127.0.0.1:8000',
) or '').split(',')

# Celery Configuration
REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or REDIS_URL
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Shared service settings
AUDIT_LOCAL_WRITE = (os.environ.get('AUDIT_LOCAL_WRITE') or 'True').lower() == 'true'
EVENT_BUS_URL = os.environ.get('EVENT_BUS_URL') or None
JWKS_URL = os.environ.get('JWKS_URL') or None
SERVICE_NAME = os.environ.get('SERVICE_NAME') or 'monolith'

STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}
# Logging
LOGGING = build_logging_config(os.environ.get('LOG_FORMAT', '').lower() == 'json')

# CMMS Specific Settings
CMMS_SETTINGS = {
    'PM_AUTO_GENERATION_ENABLED': True,
    'PM_OVERDUE_ALERT_DAYS': 7,
    'SPAREPART_LOW_STOCK_ALERT': True,
}
