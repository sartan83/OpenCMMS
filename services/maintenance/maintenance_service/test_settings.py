from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
    'monolith': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_monolith.sqlite3',
    },
}
EVENT_BUS_URL = None
JWKS_URL = None
CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_URL = 'memory://'
