from .settings import *  # noqa: F401,F403

DATABASES['monolith'] = {  # noqa: F405
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'monolith_test.sqlite3',  # noqa: F405
}
DATABASE_ROUTERS = ['workorders_service.test_settings.DefaultOnlyRouter']
EVENT_BUS_URL = None
JWKS_URL = None


class DefaultOnlyRouter:
    """Keep service migrations out of the simulated monolith database."""

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == 'default'
