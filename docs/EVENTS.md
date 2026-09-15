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
