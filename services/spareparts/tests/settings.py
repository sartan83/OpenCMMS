from spareparts_service.settings import *

DATABASES['monolith'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': ':memory:',
}
