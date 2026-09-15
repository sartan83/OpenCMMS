# Microservices Migration

## Phase 0: Foundations

Run the application stack locally with Docker Compose:

```bash
cp .env.example .env
docker compose up --build
```

The gateway is available at http://localhost/ and exposes the web application,
API, admin, static files, and health endpoint.

## Phase 1: Service boundaries

Phase 1 introduces the shared `cmms_common` kernel and the first service
boundaries. The identity service reuses the existing `users` app while issuing
RS256 access tokens. Its public key is available at
`/.well-known/jwks.json`, and services authenticate remote users through the
shared JWKS authentication class.

Events use RabbitMQ when `EVENT_BUS_URL` is set, and otherwise use the shared
synchronous in-memory bus for local development and tests. Schemas and
versioned contracts are in [`contracts/events`](../contracts/events):

| Event | Contract |
| --- | --- |
| `audit.recorded` | [audit.recorded.v1.json](../contracts/events/audit.recorded.v1.json) |
| `asset.created` | [asset.created.v1.json](../contracts/events/asset.created.v1.json) |
| `asset.updated` | [asset.updated.v1.json](../contracts/events/asset.updated.v1.json) |
| `workorder.requested` | [workorder.requested.v1.json](../contracts/events/workorder.requested.v1.json) |
| `workorder.created` | [workorder.created.v1.json](../contracts/events/workorder.created.v1.json) |
| `workorder.assigned` | [workorder.assigned.v1.json](../contracts/events/workorder.assigned.v1.json) |
| `workorder.completed` | [workorder.completed.v1.json](../contracts/events/workorder.completed.v1.json) |
| `workorder.closed` | [workorder.closed.v1.json](../contracts/events/workorder.closed.v1.json) |
| `inspection.failed` | [inspection.failed.v1.json](../contracts/events/inspection.failed.v1.json) |
| `part.consumed` | [part.consumed.v1.json](../contracts/events/part.consumed.v1.json) |
| `user.created` | [user.created.v1.json](../contracts/events/user.created.v1.json) |

Audit writes are dual-written during the migration: the monolith keeps its
existing `AuditLog` row and publishes `audit.recorded`; the audit service
consumes that event into its own `AuditEntry` table. The identity service keeps
the legacy audit-log endpoint temporarily; the audit service is the future
owner.

Generate local RSA keys and start the full stack with:

```bash
./scripts/gen_jwt_keys.sh
docker compose up --build
```

## Phase 2: Shared contracts and data ownership

## Phase 3: Service extraction

## Phase 4: Gateway cutover
