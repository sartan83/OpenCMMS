# Work Order Service (`services/workorders/`)

Standalone Django/DRF service extracted from the monolith `workorders` app
(Phase 2). The monolith app is unchanged and keeps serving `/api/workorders/`
until the Phase 4 gateway cutover.

## Endpoints

Mounted at `/api/workorders/` (same prefix as the monolith).

| Method | Path | Notes |
| --- | --- | --- |
| GET/POST | `/api/workorders/` | list / create (create requires supervisor+) |
| GET/PUT/PATCH/DELETE | `/api/workorders/{id}/` | |
| POST | `/api/workorders/{id}/assign/` | body `{"assignee_id": int, "assignee_name": str?}`; name falls back to the id as a string |
| POST | `/api/workorders/{id}/start/` | |
| POST | `/api/workorders/{id}/complete/` | body: `actions_taken` (required), `root_cause`, `downtime_minutes`, `labor_hours`, `parts_cost` |
| POST | `/api/workorders/{id}/close/` | supervisor+ |
| GET | `/api/workorders/my_orders/` | work orders assigned to the caller |
| GET | `/api/workorders/overdue/` | |
| GET | `/api/workorders/download_template/` | xlsx import template |
| POST | `/api/workorders/import_excel/` | multipart `file` (xlsx/xls/csv); equipment resolved via `AssetProjection.code` |
| GET | `/api/workorders/export_csv/` | xlsx export |
| CRUD | `/api/workorders/comments/` | `WorkOrderComment` (`author`/`author_name` set from the JWT) |
| CRUD | `/api/workorders/parts/` | `WorkOrderPart` |
| GET | `/health/`, `/metrics` | |

Response field names match `contracts/api/workorders/*.json`. Soft references
keep the monolith names: `equipment` holds the asset id, `requested_by`,
`assignee`, `assigned_by`, `completed_by`, `closed_by`, `maintenance_plan` and
comment `author` hold integer ids.

Note: the service registers `comments/` and `parts/` before the root router so
they are not shadowed by the `{id}` detail route (a latent bug in the monolith
URL order).

## Data model

| Monolith FK | Service column(s) |
| --- | --- |
| `WorkOrder.equipment` -> `assets.Asset` | `equipment` (int) + cached `equipment_code`, `equipment_name` |
| `WorkOrder.maintenance_plan` | `maintenance_plan_id` (int) |
| `WorkOrder.requested_by` -> `users.User` | `requested_by_id`, `requested_by_name` |
| `WorkOrder.assignee` | `assignee_id`, `assignee_name` |
| `WorkOrder.assigned_by` / `completed_by` / `closed_by` | `assigned_by_id` / `completed_by_id` / `closed_by_id` |
| `WorkOrderComment.author` | `author_id`, `author_name` |
| `WorkOrderComment.work_order`, `WorkOrderPart.work_order` | real FKs (intra-service) |

Additional tables: `AssetProjection` (filled from `asset.*` events; used for
cached equipment columns and Excel import lookups), `ProcessedEvent` (consumer
idempotency), and `WorkOrder.request_id` (unique, nullable; dedupe for
`workorder.requested`).

## Events

Published (after commit, validated against `cmms_common.events.schemas`):

- `workorder.created` – from `perform_create`, Excel import, and fulfilled `workorder.requested` (`request_id` set, `actor_id=0`)
- `workorder.assigned` – `assign/`
- `workorder.completed` – `complete/`
- `workorder.closed` – `close/`

All four carry the optional reporting fields (`asset_code`, `asset_name`,
`priority`, `title`, `assignee_name`, `planned_*`, `actual_*`,
`downtime_minutes`, `labor_hours`, `parts_cost`, `total_cost`), null when
unknown. Audit entries are emitted via `cmms_common.audit.audit_log`
(`service='workorders'`).

Consumed (`manage.py consume_events`, queue `workorders-service`):

- `asset.created`, `asset.updated` -> upsert `AssetProjection`, refresh cached `equipment_code`/`equipment_name`
- `workorder.requested` (`source=maintenance` -> PM, `source=inspection` -> CM, via payload `wo_type`) -> create work order (`PM-`/`CM-` code), dedupe on `request_id`, then publish `workorder.created`

## Environment variables

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | required when `DEBUG` is false |
| `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` | standard |
| `WORKORDERS_POSTGRES_DB/USER/PASSWORD/HOST/PORT` | service database (SQLite fallback when `HOST` unset) |
| `JWKS_URL` | identity JWKS endpoint (`http://identity:8000/.well-known/jwks.json`) |
| `EVENT_BUS_URL` | RabbitMQ URL; in-memory bus when unset |
| `SERVICE_NAME` | `workorders` |
| `SOURCE_DATABASE_URL` | monolith postgres URL; enables the `monolith` DB alias for import |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | optional tracing |

## Import procedure

1. Set `SOURCE_DATABASE_URL=postgresql://cmms:cmms@db:5432/cmms` on the `workorders` container.
2. `python services/workorders/manage.py migrate`
3. `python services/workorders/manage.py import_from_monolith`

The command reads `assets`, `users`, `work_orders`, `work_order_comments` and
`work_order_parts` with raw SQL through `connections['monolith']`, preserves
primary keys, joins assets/users to fill cached code/name columns, and uses
`update_or_create`, so it can be re-run safely. After the import, reset the
Postgres sequences if further rows will be created locally
(`python manage.py sqlsequencereset workorders_api | python manage.py dbshell`).

## Gateway cutover (Phase 4, not done here)

Add to `gateway/nginx.conf`:

```
upstream workorders_backend { server workorders:8000; }
```

and point the `/api/workorders/` location at `workorders_backend`.
