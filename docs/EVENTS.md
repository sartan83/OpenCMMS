# Event catalog

The shared event catalog is versioned under [`contracts/events`](../contracts/events).

| Event | Purpose |
| --- | --- |
| `audit.recorded` | Records an auditable user action |
| `asset.created`, `asset.updated` | Asset lifecycle changes |
| `workorder.requested`, `workorder.created`, `workorder.assigned`, `workorder.completed`, `workorder.closed` | Work-order lifecycle |
| `inspection.failed` | Inspection failure |
| `part.consumed` | Inventory consumption |
| `user.created` | New identity registration |

## Request correlation

`workorder.created` carries an optional `request_id` echoing the
`workorder.requested.request_id` it fulfils (null for work orders created
directly through the API), so the requesting service can link the resulting
work order without a synchronous call.

### Reporting enrichment on `workorder.*` lifecycle events

`workorder.created/assigned/completed/closed` accept optional, nullable reporting fields
(`asset_code`, `asset_name`, `priority`, `title`, `assignee_name`, `planned_start`,
`planned_end`, `actual_start`, `actual_end`, `downtime_minutes`, `labor_hours`,
`parts_cost`, `total_cost`). The Work Order service populates whatever it knows at emit
time; the Reporting service (Phase 3) builds its denormalized read model from these so it
never has to call back into Work Orders synchronously.
