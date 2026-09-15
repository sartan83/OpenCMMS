from assets_service.settings import *  # noqa: F401,F403

DATABASES['monolith'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'monolith_test.sqlite3',
}


class MonolithRouter:
    """Keep service migrations off the legacy alias so tests can create monolith tables there."""

    def allow_migrate(self, db, app_label, **hints):
        return db != 'monolith'


DATABASE_ROUTERS = ['tests.settings.MonolithRouter']
