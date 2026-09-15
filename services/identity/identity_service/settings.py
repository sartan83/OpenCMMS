from datetime import timedelta
import logging
import os
from pathlib import Path
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.core.exceptions import ImproperlyConfigured

REPO_ROOT = Path(__file__).resolve().parents[3]
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from cmms_common.auth.keys import load_private_key, load_public_key
from cmms_common.logging import build_logging_config

DEBUG = (os.environ.get('DEBUG') or 'True').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-identity-dev-key'
    else:
        raise ImproperlyConfigured('SECRET_KEY must be set when DEBUG is false')
ALLOWED_HOSTS = (os.environ.get('ALLOWED_HOSTS') or '*').split(',')

private_pem = load_private_key()
public_pem = load_public_key()
if private_pem is None:
    logging.getLogger(__name__).warning(
        'JWT_PRIVATE_KEY_PATH is not configured; using an ephemeral RSA keypair'
    )
    ephemeral_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = ephemeral_private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = ephemeral_private.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
elif public_pem is None:
    public_pem = serialization.load_pem_private_key(
        private_pem, password=None
    ).public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )

JWT_KID = os.environ.get('JWT_KID') or 'cmms-identity-1'
JWT_PUBLIC_KEY = public_pem
JWT_PRIVATE_KEY = private_pem

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_prometheus',
    'users',
]
MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]
ROOT_URLCONF = 'identity_service.urls'
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
WSGI_APPLICATION = 'identity_service.wsgi.application'

if os.environ.get('IDENTITY_POSTGRES_HOST'):
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('IDENTITY_POSTGRES_DB') or 'identity',
        'USER': os.environ.get('IDENTITY_POSTGRES_USER') or 'identity',
        'PASSWORD': os.environ.get('IDENTITY_POSTGRES_PASSWORD') or 'identity',
        'HOST': os.environ.get('IDENTITY_POSTGRES_HOST') or 'localhost',
        'PORT': os.environ.get('IDENTITY_POSTGRES_PORT') or '5432',
    }}
else:
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }}

AUTH_USER_MODEL = 'users.User'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
}
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'ALGORITHM': 'RS256',
    'SIGNING_KEY': JWT_PRIVATE_KEY,
    'VERIFYING_KEY': JWT_PUBLIC_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}
SERVICE_NAME = 'identity'
AUDIT_LOCAL_WRITE = True
EVENT_BUS_URL = os.environ.get('EVENT_BUS_URL') or None
JWKS_URL = os.environ.get('JWKS_URL') or 'http://identity/.well-known/jwks.json'
LOGGING = build_logging_config((os.environ.get('LOG_FORMAT') or '').lower() == 'json')
