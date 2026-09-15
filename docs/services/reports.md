# Reporting service

The Reporting service is a CQRS read side. It owns denormalized analytics
tables and does not call domain services synchronously.

## Event projections

| Event | Projection |
| --- | --- |
| `asset.created`, `asset.updated` | `AssetProjection` |
| `workorder.created`, `workorder.assigned`, `workorder.completed`, `workorder.closed` | `WorkOrderFact` |
| `part.consumed` | `PartConsumptionFact` |
| `inspection.failed` | `InspectionFact` |

Every event is recorded in `ProcessedEvent` in the same transaction as its
projection write. Re-delivery is therefore safe and returns a duplicate result
without changing the read model.

## API

All endpoints are under `/api/reports/` and require a valid RS256 bearer token:

- `GET /workorders/`
- `GET /downtime/`
- `GET /spareparts-usage/`
- `GET /maintenance-compliance/`
- `GET /cost-analysis/`
- `GET /technician-performance/`
- `GET /equipment-availability/`
- `GET /run/?type=<report_type>`
- `GET|POST|PATCH|DELETE /scheduled/`
- `GET /runs/`

The report endpoints accept `date_from`, `date_to`, `asset_id`, `wo_type`, and
`status` where relevant. The run endpoint uses the same report builders as the
individual endpoints and stores the completed result in `ReportRun`.

## Configuration

The service uses `REPORTS_DATABASE_URL` or the `REPORTS_POSTGRES_*` variables
for its database, with a local SQLite fallback. Set `SOURCE_DATABASE_URL` to
add the legacy database as the `monolith` connection for
`manage.py import_from_monolith`.

`EVENT_BUS_URL` selects RabbitMQ; when unset, the shared in-memory bus is used
for development and tests. `JWKS_URL` configures token verification.
`OTEL_EXPORTER_OTLP_ENDPOINT` enables optional OpenTelemetry tracing.

Run the service locally with:

```bash
../../.venv/bin/python manage.py migrate
../../.venv/bin/python manage.py runserver
```

The event consumer runs separately:

```bash
../../.venv/bin/python manage.py consume_events
```

## Endpoint response shapes

All API paths below are relative to `/api/reports/` and require a JWKS
authenticated bearer token. The list endpoints accept `date_from`, `date_to`,
`asset_id`, `wo_type`, and `status` filters when those fields apply.

- `GET /workorders/` returns `total`, `by_status`, `by_type`, `by_priority`,
  `completed`, `overdue`, `avg_completion_hours`, `total_cost`, and up to 100
  newest serialized work-order `items`.
- `GET /downtime/` returns `total_downtime_minutes`, descending `by_asset`
  aggregates, and serialized work-order `items`.
- `GET /spareparts-usage/` returns `total_quantity`, `total_cost`, `by_part`
  aggregates, and serialized consumption `items`.
- `GET /maintenance-compliance/` returns PM `total`, `completed_on_time`,
  `late`, `compliance_rate`, and `by_plan` aggregates.
- `GET /cost-analysis/` returns work-order `parts_cost`, `labor_hours`, and
  `total_cost`, `parts_consumption_total`, `by_type`, the top 20 `by_asset`,
  and `by_month` values keyed by `YYYY-MM`.
- `GET /technician-performance/` returns `by_technician` entries containing
  assignee, assigned/completed counts, average completion hours, and labor
  hours.
- `GET /equipment-availability/` returns the reporting window, clamped
  availability metrics, downtime, work-order counts, and failed inspection
  counts in `items`. Without dates it uses the previous 30 days.
- `GET /run/?type=<report_type>` dispatches to the same builders, returns the
  builder response, and records a completed or failed `ReportRun`.
- `GET|POST|PATCH|DELETE /scheduled/` manages scheduled report definitions.
  Creation records `created_by_id` and `created_by_name` from the remote user.
- `GET /runs/` exposes read-only report-run history.

## Compose services

`services/reports/compose.yml` defines isolated `reports-db` (PostgreSQL 16),
`reports` (the authenticated HTTP API with migrations enabled), and
`reports-consumer` (the RabbitMQ projection consumer). The API and consumer
wait for the database and required identity/RabbitMQ services to be healthy.

## Legacy import

Set `SOURCE_DATABASE_URL` to the legacy database URL. This creates Django's
`monolith` connection alias. After applying the reports migrations, run:

```bash
../../.venv/bin/python manage.py import_from_monolith
```

The command reads the legacy `assets`, `work_orders`, `part_transactions`,
`scheduled_reports`, and `report_runs` tables with raw SQL and upserts their
read-side equivalents. Re-running it is safe.

## Environment variables

- `REPORTS_DATABASE_URL` or `REPORTS_POSTGRES_DB`, `REPORTS_POSTGRES_USER`,
  `REPORTS_POSTGRES_PASSWORD`, `REPORTS_POSTGRES_HOST`, and
  `REPORTS_POSTGRES_PORT` configure the reports database. Without them, the
  service uses `services/reports/db.sqlite3`.
- `SOURCE_DATABASE_URL` configures the optional legacy `monolith` connection.
- `JWKS_URL` configures RS256 bearer-token verification.
- `EVENT_BUS_URL` selects RabbitMQ; if unset, the in-memory bus is used.
- `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` configure Django runtime safety.
- `OTEL_EXPORTER_OTLP_ENDPOINT` enables OpenTelemetry export when set.
- `LOG_FORMAT=json` enables structured JSON logs; the default is plain text.
