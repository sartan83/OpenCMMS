from __future__ import annotations

from jsonschema import validate as jsonschema_validate


def _string(nullable: bool = False) -> dict:
    schema = {'type': ['string', 'null'] if nullable else 'string'}
    return schema


def _integer(nullable: bool = False) -> dict:
    return {'type': ['integer', 'null'] if nullable else 'integer'}


def _event_schema(properties: dict, required: list[str]) -> dict:
    return {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        'type': 'object',
        'properties': properties,
        'required': required,
        'additionalProperties': False,
    }


_asset_properties = {
    'asset_id': _integer(),
    'code': _string(),
    'name': _string(),
    'status': _string(),
    'process': _string(),
    'factory': _string(),
    'workshop': _string(),
    'line': _string(),
    'station': _string(),
}
_asset_required = list(_asset_properties)

_workorder_properties = {
    'work_order_id': _integer(),
    'wo_code': _string(),
    'asset_id': _integer(),
    'status': _string(),
    'wo_type': _string(),
    'assignee_id': _integer(nullable=True),
    'actor_id': _integer(),
    'maintenance_plan_id': _integer(nullable=True),
}

SCHEMAS = {
    'audit.recorded': _event_schema(
        {
            'actor_id': _integer(),
            'actor_username': _string(),
            'action': _string(),
            'entity_type': _string(),
            'entity_id': _integer(),
            'entity_repr': _string(),
            'diff': {'type': 'object'},
            'ip_address': _string(nullable=True),
            'user_agent': _string(),
            'service': _string(),
        },
        [
            'actor_id', 'actor_username', 'action', 'entity_type', 'entity_id',
            'entity_repr', 'diff', 'ip_address', 'user_agent', 'service',
        ],
    ),
    'asset.created': _event_schema(_asset_properties, _asset_required),
    'asset.updated': _event_schema(_asset_properties, _asset_required),
    'workorder.requested': _event_schema(
        {
            'request_id': _string(),
            'source': {'enum': ['maintenance', 'inspection']},
            'asset_id': _integer(),
            'asset_code': _string(),
            'wo_type': {'enum': ['PM', 'CM']},
            'priority': _string(),
            'summary': _string(),
            'description': _string(),
            'maintenance_plan_id': _integer(nullable=True),
            'inspection_record_id': _integer(nullable=True),
            'requested_by_id': _integer(nullable=True),
            'due_date': _string(nullable=True),
        },
        [
            'request_id', 'source', 'asset_id', 'asset_code', 'wo_type',
            'priority', 'summary', 'description', 'maintenance_plan_id',
            'inspection_record_id', 'requested_by_id', 'due_date',
        ],
    ),
    'workorder.created': _event_schema(
        {
            **_workorder_properties,
            'created_at': _string(),
            'request_id': _string(nullable=True),
        },
        [*_workorder_properties, 'created_at'],
    ),
    'workorder.assigned': _event_schema(
        {**_workorder_properties, 'assigned_at': _string()},
        [*_workorder_properties, 'assigned_at'],
    ),
    'workorder.completed': _event_schema(
        {**_workorder_properties, 'completed_at': _string()},
        [*_workorder_properties, 'completed_at'],
    ),
    'workorder.closed': _event_schema(
        {**_workorder_properties, 'closed_at': _string()},
        [*_workorder_properties, 'closed_at'],
    ),
    'inspection.failed': _event_schema(
        {
            'inspection_record_id': _integer(),
            'asset_id': _integer(),
            'work_order_id': _integer(nullable=True),
            'failed_items': {'type': 'array'},
            'inspector_id': _integer(),
        },
        [
            'inspection_record_id', 'asset_id', 'work_order_id',
            'failed_items', 'inspector_id',
        ],
    ),
    'part.consumed': _event_schema(
        {
            'transaction_id': _integer(),
            'part_id': _integer(),
            'part_code': _string(),
            'quantity': {'type': ['number', 'string']},
            'unit_cost': {'type': ['number', 'string', 'null']},
            'work_order_id': _integer(nullable=True),
            'actor_id': _integer(),
        },
        [
            'transaction_id', 'part_id', 'part_code', 'quantity', 'unit_cost',
            'work_order_id', 'actor_id',
        ],
    ),
    'user.created': _event_schema(
        {
            'user_id': _integer(),
            'username': _string(),
            'role': _string(),
            'full_name': _string(),
        },
        ['user_id', 'username', 'role', 'full_name'],
    ),
}


def validate(event) -> bool:
    schema = SCHEMAS.get(event.type)
    if schema is not None:
        jsonschema_validate(instance=event.payload, schema=schema)
    return True
