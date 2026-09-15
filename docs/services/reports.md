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
