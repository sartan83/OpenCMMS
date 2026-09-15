# Inspections service

Standalone Django/DRF service under `services/inspections/` owning inspection
records, templates and routes (extracted from the monolith `inspections` app,
which had models only; the REST API is new). Django project
`inspections_service`, app `inspection`.

## Endpoints (`/api/inspections/`)

| Method | Path | Notes |
| --- | --- | --- |
| GET, POST | `/api/inspections/` | Inspection records (list/create). Filters: `equipment`, `result`, `inspector`, `route` |
| GET, PUT, PATCH | `/api/inspections/<id>/` | No delete |
| GET, POST | `/api/inspections/templates/` | Inspection templates |
| GET, PUT, PATCH, DELETE | `/api/inspections/templates/<id>/` | |
| GET, POST | `/api/inspections/routes/` | Inspection routes |
| GET, PUT, PATCH, DELETE | `/api/inspections/routes/<id>/` | |
| GET | `/health/`, `/metrics` | |

Serializer contracts: `contracts/api/inspections/*.json`.

`InspectionRecord.result` is derived from `items[].ok` on every save
(`fail` if any item has `ok: false`, else `pass`). `inspector`/`inspector_name`
are taken from the JWT user.

## Soft references

| Monolith FK | Service column(s) |
| --- | --- |
| `InspectionRecord.equipment` → `assets.Asset` | `equipment` (int), cached `equipment_code`, `equipment_name` (from `AssetProjection`) |
| `InspectionRecord.inspector` → `users.User` | `inspector_id`, `inspector_name` (API: `inspector`, `inspector_name`) |
| `InspectionRecord.triggered_work_order` → `workorders.WorkOrder` | `triggered_work_order_id` (API: `triggered_work_order`), plus `work_order_request_id` |
| `InspectionRoute.inspector` → `users.User` | `inspector_id`, `inspector_name` |

## Events

Published (source `inspections`), after commit, when a record is saved with
`result == fail` and no triggered work order yet:

- `inspection.failed` — `failed_items` = items with `ok: false`, `work_order_id: null`.
- `workorder.requested` — `source: inspection`, `wo_type: CM`, `priority: high`,
  `inspection_record_id`, `request_id` (stored on the record as
  `work_order_request_id`).
- `audit.recorded` via `cmms_common.audit.audit_log` for create/update/delete.

Consumed (`manage.py consume_events`, queue `inspections-service`, deduped on
event id in `inspection_processed_events`):

- `asset.created`, `asset.updated` → upsert `AssetProjection`, refresh cached
  `equipment_code`/`equipment_name` on records.
- `workorder.created` → when `request_id` matches a record's
  `work_order_request_id`, set `triggered_work_order_id`.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `LOG_FORMAT` | Django |
| `INSPECTIONS_POSTGRES_DB/USER/PASSWORD/HOST/PORT` | Own database (SQLite fallback when `HOST` unset) |
| `JWKS_URL` | Identity JWKS endpoint |
| `EVENT_BUS_URL` | RabbitMQ URL (in-memory bus when unset) |
| `SERVICE_NAME` | `inspections` |
| `SOURCE_DATABASE_URL` | Monolith Postgres URL; enables `DATABASES['monolith']` for import |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Optional tracing |

## Import procedure

```bash
export SOURCE_DATABASE_URL=postgres://cmms:cmms@db:5432/cmms
python services/inspections/manage.py migrate --noinput
python services/inspections/manage.py import_from_monolith
```

Reads `assets`, `users`, `inspection_records`, `inspection_templates`,
`inspection_routes` from the monolith, preserves primary keys, fills the cached
code/name columns via joins, and is idempotent (safe to re-run). Importing does
not publish events.

## Gateway cutover (Phase 4)

In `gateway/nginx.conf` replace the `inspections_backend` upstream with:

```
upstream inspections_backend { server inspections:8000; }
```
