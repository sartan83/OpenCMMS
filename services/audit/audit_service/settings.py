import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from cmms_common.logging import build_logging_config

DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-audit-dev-key')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'auditlog',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]
ROOT_URLCONF = 'audit_service.urls'
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
WSGI_APPLICATION = 'audit_service.wsgi.application'

if os.environ.get('AUDIT_POSTGRES_HOST'):
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('AUDIT_POSTGRES_DB', 'audit'),
        'USER': os.environ.get('AUDIT_POSTGRES_USER', 'audit'),
        'PASSWORD': os.environ.get('AUDIT_POSTGRES_PASSWORD', 'audit'),
        'HOST': os.environ.get('AUDIT_POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('AUDIT_POSTGRES_PORT', '5432'),
    }}
else:
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
JWKS_URL = os.environ.get('JWKS_URL')
EVENT_BUS_URL = os.environ.get('EVENT_BUS_URL')
SERVICE_NAME = 'audit'
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'cmms_common.auth.jwks.JWKSAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
}
LOGGING = build_logging_config(os.environ.get('LOG_FORMAT', '').lower() == 'json')
