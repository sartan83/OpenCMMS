# Maintenance service

The maintenance service owns preventive-maintenance plans and work-order
requests. It runs at `/api/maintenance/` and exposes `/health/` and
`/metrics`.

## Endpoints

- `GET|POST /api/maintenance/plans/`
- `GET|PATCH|PUT|DELETE /api/maintenance/plans/<id>/`
- `POST /api/maintenance/plans/<id>/activate/`
- `POST /api/maintenance/plans/<id>/deactivate/`
- `POST /api/maintenance/plans/<id>/generate_work_order/`
- `GET|POST /api/maintenance/templates/`
- `GET|PATCH|PUT|DELETE /api/maintenance/templates/<id>/`

Plans support filtering by `equipment`, `trigger_type`, `is_active`, and
`priority`, plus search and ordering fields inherited from the API.

## Events

Published:

- `workorder.requested`
- `audit.recorded`

Consumed:

- `asset.created`
- `asset.updated`
- `workorder.created`

Asset events maintain a local asset projection and refresh cached equipment
names on plans. Work-order-created events fulfil matching pending requests.

## Configuration

The service accepts `MAINTENANCE_POSTGRES_HOST`, `MAINTENANCE_POSTGRES_DB`,
`MAINTENANCE_POSTGRES_USER`, `MAINTENANCE_POSTGRES_PASSWORD`, and
`MAINTENANCE_POSTGRES_PORT`, with SQLite used when no PostgreSQL host is set.
`JWKS_URL` configures JWT authentication; `EVENT_BUS_URL` configures RabbitMQ;
`REDIS_URL` or `CELERY_BROKER_URL` configures Celery. `SERVICE_NAME` defaults
to `maintenance`.

To import legacy data, configure a source database and run:

```sh
SOURCE_DATABASE_URL=postgres://... python services/maintenance/manage.py import_from_monolith
```

The command imports plans, asset projections, and work-order templates
idempotently.

Celery Beat evaluates time-based plans hourly. Counter-based plans are
deferred because this service has no counter source.

## Cutover

```nginx
upstream maintenance_backend {
    server maintenance:8000;
}
```
