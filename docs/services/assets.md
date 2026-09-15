# Assets service

Standalone Django/DRF service extracted from the monolith `assets` app
(Phase 2, Track A). Lives in `services/assets/`; Django project
`assets_service`, app `assetregistry`, table `assets` (same name as the
monolith so `import_from_monolith` maps 1:1).

## Endpoints

Mounted at `/api/assets/` (router registered at `''`), identical to the
monolith paths and payloads:

| Method | Path | Notes |
| --- | --- | --- |
| GET, POST | `/api/assets/` | list (`AssetListSerializer`, paginated, `page_size` up to 1000) / create (admin only) |
| GET, PUT, PATCH, DELETE | `/api/assets/{id}/` | `AssetSerializer`; writes admin only |
| GET | `/api/assets/tree/` | root assets with active children (`AssetTreeSerializer`) |
| GET | `/api/assets/{id}/children/` | direct children |
| GET | `/api/assets/overdue/` | assets past `next_maintenance_date` |
| GET | `/api/assets/download_template/` | xlsx import template |
| POST | `/api/assets/import_excel/` | multipart `file` (xlsx/xls/csv) |
| GET | `/api/assets/export_csv/` | xlsx export honouring list filters |
| GET | `/health/`, `/metrics` | health / Prometheus |

Filters: `status`, `factory`, `workshop`, `line`, `criticality`; `search`
over code/name/equipment_id/serial_number/vendor; `ordering` by
code/name/created_at.

Authentication is `cmms_common.auth.jwks.JWKSAuthentication`; the request
user is a `RemoteUser`. Writes require `role == 'admin'`.

### Soft references

| Monolith column | Service column(s) | API field |
| --- | --- | --- |
| `assets.created_by_id` → `users.User` | `created_by_id` (int, indexed), `created_by_name` (cached `full_name`, falls back to `username`) | `created_by` (id, read-only), `created_by_name` (read-only, additive) |
| `assets.parent_id` → `assets` | real FK (intra-service) | `parent` |

`is_overdue` is now a model property so the field is actually rendered
(the monolith serializer declared it but silently dropped it).

## Events

Published (`source='assets'`, payload per `contracts/events/asset.*.v1.json`,
validated with `cmms_common.events.schemas.validate` before publishing,
emitted via `transaction.on_commit`):

| Event | When |
| --- | --- |
| `asset.created` | `POST /api/assets/`, one per row created by `import_excel` |
| `asset.updated` | `PUT`/`PATCH /api/assets/{id}/` |

Nullable location fields (`process`, `factory`, `workshop`, `line`,
`station`) are sent as `''` because the contract requires strings.

Consumed: none.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `LOG_FORMAT` | standard Django settings (SECRET_KEY required when `DEBUG=False`) |
| `ASSETS_POSTGRES_DB/USER/PASSWORD/HOST/PORT` | own database; SQLite fallback when `ASSETS_POSTGRES_HOST` is unset |
| `SOURCE_DATABASE_URL` | postgres URL of the monolith DB; adds `DATABASES['monolith']` for the import command |
| `JWKS_URL` | identity JWKS endpoint |
| `EVENT_BUS_URL` | RabbitMQ URL; in-memory bus when unset |
| `SERVICE_NAME` | `assets` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | optional tracing (see `cmms_common.telemetry`) |

## Import procedure

```bash
export SOURCE_DATABASE_URL=postgres://cmms:cmms@db:5432/cmms
python services/assets/manage.py migrate --noinput
python services/assets/manage.py import_from_monolith
```

The command reads `assets LEFT JOIN users` through
`connections['monolith']`, upserts by primary key (ids preserved so
downstream soft references keep working), fills `created_by_name` from the
user row and keeps the original `created_at`/`updated_at`. It is idempotent
and can be re-run at any point during the staged migration.

## Compose

`services/assets/compose.yml` defines `assets-db` (postgres:16, volume
`assets_pgdata`) and `assets` (migrate then gunicorn, `/health/` healthcheck,
depends on `identity`, `rabbitmq`, `assets-db`). It is included from the root
`docker-compose.yml`.

## Gateway cutover (Phase 4)

`gateway/nginx.conf` already routes `/api/assets/` through
`assets_backend`; the cutover is the one-line upstream change:

```nginx
upstream assets_backend { server assets:8000; }
```
