from .settings import *

DATABASES['monolith'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'monolith_test.sqlite3',
}
EVENT_BUS_URL = None
