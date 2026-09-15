"""Event publishing for the workorders service."""
from django.db import transaction

from cmms_common.events.bus import Event, get_event_bus
from cmms_common.events.schemas import validate

SOURCE = 'workorders'


def _iso(value):
    return value.isoformat() if value else None


def _decimal(value):
    return str(value) if value is not None else None


def workorder_payload(work_order, actor_id):
    return {
        'work_order_id': work_order.id,
        'wo_code': work_order.wo_code,
        'asset_id': work_order.equipment,
        'status': work_order.status,
        'wo_type': work_order.wo_type,
        'assignee_id': work_order.assignee_id,
        'actor_id': int(actor_id or 0),
        'maintenance_plan_id': work_order.maintenance_plan_id,
        'asset_code': work_order.equipment_code or None,
        'asset_name': work_order.equipment_name or None,
        'priority': work_order.priority,
        'title': work_order.summary,
        'assignee_name': work_order.assignee_name or None,
        'planned_start': _iso(work_order.planned_start),
        'planned_end': _iso(work_order.planned_end),
        'actual_start': _iso(work_order.actual_start),
        'actual_end': _iso(work_order.actual_end),
        'downtime_minutes': work_order.downtime_minutes,
        'labor_hours': _decimal(work_order.labor_hours),
        'parts_cost': _decimal(work_order.parts_cost),
        'total_cost': _decimal(work_order.total_cost),
    }


def build_event(event_type, work_order, actor_id, **extra):
    payload = {**workorder_payload(work_order, actor_id), **extra}
    event = Event(type=event_type, payload=payload, source=SOURCE)
    validate(event)
    return event


def publish_after_commit(event):
    transaction.on_commit(lambda: get_event_bus().publish(event))


def publish_workorder_created(work_order, actor_id):
    publish_after_commit(build_event(
        'workorder.created', work_order, actor_id,
        created_at=_iso(work_order.created_at),
        request_id=work_order.request_id,
    ))


def publish_workorder_assigned(work_order, actor_id):
    publish_after_commit(build_event(
        'workorder.assigned', work_order, actor_id,
        assigned_at=_iso(work_order.assigned_at),
    ))


def publish_workorder_completed(work_order, actor_id):
    publish_after_commit(build_event(
        'workorder.completed', work_order, actor_id,
        completed_at=_iso(work_order.completed_at),
    ))


def publish_workorder_closed(work_order, actor_id):
    publish_after_commit(build_event(
        'workorder.closed', work_order, actor_id,
        closed_at=_iso(work_order.closed_at),
    ))
