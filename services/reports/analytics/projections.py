from datetime import datetime, timezone
from decimal import Decimal

from django.db import IntegrityError, transaction

from cmms_common.events.bus import Event

from .models import (
    AssetProjection,
    InspectionFact,
    PartConsumptionFact,
    ProcessedEvent,
    WorkOrderFact,
)

LIFECYCLE_RANKS = {
    'workorder.created': 0,
    'workorder.assigned': 1,
    'workorder.completed': 2,
    'workorder.closed': 3,
}


def _event(value):
    return Event.from_dict(value) if isinstance(value, dict) else value


def _timestamp(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace('Z', '+00:00'))


def _decimal(value):
    return None if value is None else Decimal(str(value))


def _start_event(event):
    event = _event(event)
    if ProcessedEvent.objects.filter(event_id=event.id).exists():
        return None
    try:
        with transaction.atomic():
            ProcessedEvent.objects.create(event_id=event.id, event_type=event.type)
    except IntegrityError:
        return None
    return event


def handle_asset_event(event):
    event = _event(event)
    with transaction.atomic():
        event = _start_event(event)
        if event is None:
            return False
        payload = event.payload
        AssetProjection.objects.update_or_create(
            asset_id=payload['asset_id'],
            defaults={
                'asset_code': payload['code'],
                'asset_name': payload['name'],
                'category': payload.get('process'),
                'status': payload.get('status'),
                'updated_at': _timestamp(event.occurred_at),
            },
        )
    return True


def _workorder_defaults(payload, event):
    asset = AssetProjection.objects.filter(asset_id=payload['asset_id']).first()
    defaults = {
        'wo_code': payload['wo_code'],
        'asset_id': payload['asset_id'],
        'asset_code': payload.get('asset_code') or (asset.asset_code if asset else None),
        'asset_name': payload.get('asset_name') or (asset.asset_name if asset else None),
        'wo_type': payload['wo_type'],
        'status': payload['status'],
        'updated_at': _timestamp(event.occurred_at),
    }
    if payload.get('maintenance_plan_id') is not None:
        defaults['maintenance_plan_id'] = payload['maintenance_plan_id']
    for key in (
        'priority', 'title', 'assignee_id', 'assignee_name', 'request_id',
        'planned_start', 'planned_end', 'actual_start', 'actual_end',
        'downtime_minutes', 'labor_hours', 'parts_cost', 'total_cost',
    ):
        if payload.get(key) is not None:
            value = payload[key]
            if key in {'labor_hours', 'parts_cost', 'total_cost'}:
                value = _decimal(value)
            defaults[key] = value
    return defaults


def _current_lifecycle_rank(fact):
    for event_type, rank in reversed(LIFECYCLE_RANKS.items()):
        field = event_type.rsplit('.', 1)[1] + '_at'
        if getattr(fact, field):
            return rank
    return -1


def handle_workorder_event(event):
    event = _event(event)
    with transaction.atomic():
        event = _start_event(event)
        if event is None:
            return False
        payload = event.payload
        existing = WorkOrderFact.objects.filter(
            work_order_id=payload['work_order_id']
        ).first()
        defaults = _workorder_defaults(payload, event)
        if existing and _current_lifecycle_rank(existing) > LIFECYCLE_RANKS[event.type]:
            defaults.pop('status', None)
        timestamp_field = {
            'workorder.created': 'created_at',
            'workorder.assigned': 'assigned_at',
            'workorder.completed': 'completed_at',
            'workorder.closed': 'closed_at',
        }[event.type]
        timestamp_value = payload.get(timestamp_field) or event.occurred_at
        defaults[timestamp_field] = _timestamp(timestamp_value)
        if event.type == 'workorder.created' and payload.get('created_at'):
            defaults['created_at'] = _timestamp(payload['created_at'])
        WorkOrderFact.objects.update_or_create(
            work_order_id=payload['work_order_id'],
            defaults=defaults,
        )
    return True


def handle_part_event(event):
    event = _event(event)
    with transaction.atomic():
        event = _start_event(event)
        if event is None:
            return False
        payload = event.payload
        quantity = _decimal(payload['quantity'])
        unit_cost = _decimal(payload.get('unit_cost'))
        total_cost = quantity * unit_cost if quantity is not None and unit_cost is not None else None
        PartConsumptionFact.objects.update_or_create(
            transaction_id=payload['transaction_id'],
            defaults={
                'part_id': payload['part_id'],
                'part_code': payload['part_code'],
                'quantity': quantity,
                'unit_cost': unit_cost,
                'total_cost': total_cost,
                'work_order_id': payload.get('work_order_id'),
                'actor_id': payload['actor_id'],
                'occurred_at': _timestamp(event.occurred_at),
            },
        )
    return True


def handle_inspection_event(event):
    event = _event(event)
    with transaction.atomic():
        event = _start_event(event)
        if event is None:
            return False
        payload = event.payload
        failed_items = payload.get('failed_items', [])
        InspectionFact.objects.update_or_create(
            inspection_record_id=payload['inspection_record_id'],
            defaults={
                'asset_id': payload['asset_id'],
                'work_order_id': payload.get('work_order_id'),
                'inspector_id': payload['inspector_id'],
                'failed_items': failed_items,
                'failed_item_count': len(failed_items),
                'occurred_at': _timestamp(event.occurred_at),
            },
        )
    return True


HANDLERS = {
    'asset.created': handle_asset_event,
    'asset.updated': handle_asset_event,
    'workorder.created': handle_workorder_event,
    'workorder.assigned': handle_workorder_event,
    'workorder.completed': handle_workorder_event,
    'workorder.closed': handle_workorder_event,
    'part.consumed': handle_part_event,
    'inspection.failed': handle_inspection_event,
}
