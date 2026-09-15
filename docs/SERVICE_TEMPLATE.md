# Service template

Use `services/audit/` as the starting layout for a new service. Keep the
service's Django project, app, tests, Dockerfile, and `compose.yml` under
`services/<name>/`.

## Settings

Define `<NAME>_POSTGRES_DB`, `<NAME>_POSTGRES_USER`,
`<NAME>_POSTGRES_PASSWORD`, `<NAME>_POSTGRES_HOST`, and
`<NAME>_POSTGRES_PORT`, with a SQLite fallback for local development. When
`SOURCE_DATABASE_URL` is set, add a `DATABASES['monolith']` alias for import
commands that read legacy data.

Use `JWKSAuthentication` by default, and expose `/health/` and `/metrics`.
Call `configure_telemetry('<name>')` from the service WSGI module.

## Compose and tests

Fill in the service's own `compose.yml` from its root stub with the service,
database, and (when needed) consumer. Add a service-local `pytest.ini` and
tests; the CI service discovery job runs every directory containing one.

## Importing legacy data

Add a `manage.py import_from_monolith` command that reads through
`connections['monolith']`. Keep imports explicit and repeatable so they can be
run during a staged migration.

## Events and contracts

Publish events with the shared bus:

```python
from cmms_common.events.bus import Event, get_event_bus

get_event_bus().publish(Event(
    type='asset.created',
    payload={'asset_id': 1},
    source='assets',
))
```

Consume events with a `consume_events` management command patterned after the
audit service. Add a contract test using
`cmms_common.contracts.assert_matches_contract` for every API serializer the
service exposes.
