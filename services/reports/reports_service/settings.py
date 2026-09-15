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
        SECRET_KEY = 'django-insecure-reports-dev-key'
    else:
        raise ImproperlyConfigured('SECRET_KEY must be set when DEBUG is false')
ALLOWED_HOSTS = (os.environ.get('ALLOWED_HOSTS') or '*').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'corsheaders',
    'django_prometheus',
    'analytics',
]
MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]
ROOT_URLCONF = 'reports_service.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': []},
}]
WSGI_APPLICATION = 'reports_service.wsgi.application'


def _database_config(url, prefix):
    parsed = urlparse(url)
    if parsed.scheme == 'sqlite':
        path = parsed.path or parsed.netloc
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:' if path in {'', '/:memory:', ':memory:'} else path,
        }
    if parsed.scheme not in {'postgres', 'postgresql'}:
        raise ImproperlyConfigured(
            f'{prefix}DATABASE_URL must use sqlite, postgres, or postgresql'
        )
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': parsed.path.lstrip('/'),
        'USER': unquote(parsed.username or ''),
        'PASSWORD': unquote(parsed.password or ''),
        'HOST': parsed.hostname or '',
        'PORT': str(parsed.port or 5432),
    }


reports_database_url = os.environ.get('REPORTS_DATABASE_URL') or None
if reports_database_url:
    DATABASES = {'default': _database_config(reports_database_url, 'REPORTS_')}
elif os.environ.get('REPORTS_POSTGRES_HOST'):
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('REPORTS_POSTGRES_DB') or 'reports',
        'USER': os.environ.get('REPORTS_POSTGRES_USER') or 'reports',
        'PASSWORD': os.environ.get('REPORTS_POSTGRES_PASSWORD') or 'reports',
        'HOST': os.environ.get('REPORTS_POSTGRES_HOST') or 'localhost',
        'PORT': os.environ.get('REPORTS_POSTGRES_PORT') or '5432',
    }}
else:
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }}

source_database_url = os.environ.get('SOURCE_DATABASE_URL') or None
if source_database_url:
    DATABASES['monolith'] = _database_config(source_database_url, 'SOURCE_')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

JWKS_URL = os.environ.get('JWKS_URL') or None
EVENT_BUS_URL = os.environ.get('EVENT_BUS_URL') or None
SERVICE_NAME = 'reports'
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'cmms_common.auth.jwks.JWKSAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
}
LOGGING = build_logging_config((os.environ.get('LOG_FORMAT') or '').lower() == 'json')
