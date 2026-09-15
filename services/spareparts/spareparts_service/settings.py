import os
from pathlib import Path
import sys
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

REPO_ROOT = Path(__file__).resolve().parents[3]
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from cmms_common.logging import build_logging_config

DEBUG = (os.environ.get('DEBUG') or 'True').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-spareparts-dev-key'
    else:
        raise ImproperlyConfigured('SECRET_KEY must be set when DEBUG is false')
ALLOWED_HOSTS = (os.environ.get('ALLOWED_HOSTS') or '*').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_prometheus',
    'django_filters',
    'inventory',
]
MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]
ROOT_URLCONF = 'spareparts_service.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]
WSGI_APPLICATION = 'spareparts_service.wsgi.application'

if os.environ.get('SPAREPARTS_POSTGRES_HOST'):
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('SPAREPARTS_POSTGRES_DB') or 'spareparts',
        'USER': os.environ.get('SPAREPARTS_POSTGRES_USER') or 'spareparts',
        'PASSWORD': os.environ.get('SPAREPARTS_POSTGRES_PASSWORD') or 'spareparts',
        'HOST': os.environ.get('SPAREPARTS_POSTGRES_HOST') or 'localhost',
        'PORT': os.environ.get('SPAREPARTS_POSTGRES_PORT') or '5432',
    }}
else:
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }}

source_database_url = os.environ.get('SOURCE_DATABASE_URL') or None
if source_database_url:
    parsed = urlparse(source_database_url)
    if parsed.scheme not in {'postgres', 'postgresql'}:
        raise ImproperlyConfigured('SOURCE_DATABASE_URL must use postgres or postgresql')
    DATABASES['monolith'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': parsed.path.lstrip('/'),
        'USER': unquote(parsed.username or ''),
        'PASSWORD': unquote(parsed.password or ''),
        'HOST': parsed.hostname or '',
        'PORT': str(parsed.port or 5432),
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
JWKS_URL = os.environ.get('JWKS_URL') or None
EVENT_BUS_URL = os.environ.get('EVENT_BUS_URL') or None
SERVICE_NAME = 'spareparts'
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'cmms_common.auth.jwks.JWKSAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
LOGGING = build_logging_config((os.environ.get('LOG_FORMAT') or '').lower() == 'json')
