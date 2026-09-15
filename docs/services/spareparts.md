# Spareparts Service

## Overview

The spareparts service owns spare part inventory, stock movements, and purchase
request records. It exposes the spare parts API with user and work-order
references represented as cached IDs and names rather than cross-service
foreign keys.

## Endpoints

| Method | Route | Description |
| --- | --- | --- |
| GET | `/health/` | Service health check |
| GET | `/api/spareparts/` | List spare parts |
| POST | `/api/spareparts/` | Create a spare part |
| GET | `/api/spareparts/{id}/` | Retrieve a spare part |
| PUT/PATCH | `/api/spareparts/{id}/` | Update a spare part |
| DELETE | `/api/spareparts/{id}/` | Delete a spare part |
| POST | `/api/spareparts/{id}/stock_in/` | Add stock |
| POST | `/api/spareparts/{id}/stock-in/` | Add stock (hyphenated alias) |
| POST | `/api/spareparts/{id}/stock_out/` | Remove stock |
| POST | `/api/spareparts/{id}/stock-out/` | Remove stock (hyphenated alias) |
| GET | `/api/spareparts/transactions/` | List stock transactions |
| GET | `/api/spareparts/transactions/?part={id}` | Filter transactions by part |
| GET | `/api/spareparts/transactions/?related_work_order={id}` | Filter by work order |
| GET | `/api/spareparts/transactions/?transaction_type=in|out|adjust` | Filter by movement type |

Spare parts support `low_stock=true`, category/supplier filters, search, and
ordering. Transaction results are ordered newest first.

## Events published

- `part.consumed` is published after a successful stock-out and includes the
  transaction, part, quantity, unit cost, work order, and actor IDs.
- `audit.recorded` is published for both stock-in and stock-out operations.
- This service consumes no events.

## Env vars

| Variable | Purpose |
| --- | --- |
| `SPAREPARTS_POSTGRES_DB` | PostgreSQL database name |
| `SPAREPARTS_POSTGRES_USER` | PostgreSQL user |
| `SPAREPARTS_POSTGRES_PASSWORD` | PostgreSQL password |
| `SPAREPARTS_POSTGRES_HOST` | PostgreSQL host |
| `SPAREPARTS_POSTGRES_PORT` | PostgreSQL port |
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Django debug mode |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts |
| `JWKS_URL` | Identity service JWKS endpoint |
| `EVENT_BUS_URL` | RabbitMQ event bus URL |
| `SERVICE_NAME` | Event source/service name |
| `SOURCE_DATABASE_URL` | Monolith PostgreSQL URL used by the import command |
| `LOG_FORMAT` | Set to `json` for JSON logging |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry exporter endpoint |

## Soft-reference mapping

| Monolith FK | Spareparts service columns |
| --- | --- |
| `spare_parts.created_by` | `created_by_id`, `created_by_name` |
| `part_transactions.related_work_order` | `related_work_order` (integer ID) |
| `part_transactions.operator` | `operator_id`, `operator_name` |
| `purchase_requests.requested_by` | `requested_by_id`, `requested_by_name` |
| `purchase_requests.approved_by` | `approved_by_id`, `approved_by_name` |

Part references remain local foreign keys from transactions and purchase
requests to `SparePart`.

## Import procedure

Set `SOURCE_DATABASE_URL` to a PostgreSQL connection string and run:

```sh
SOURCE_DATABASE_URL=postgres://... python services/spareparts/manage.py import_from_monolith
```

The import reads the monolith tables using raw SQL, preserves primary keys, and
is idempotent. It imports parts first, then transactions, then purchase
requests.

## Cutover

Phase 4 gateway work should add this upstream to `gateway/nginx.conf`:

```nginx
upstream spareparts_backend { server spareparts:8000; }
```
