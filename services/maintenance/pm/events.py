from cmms_common.events.bus import Event, get_event_bus
from cmms_common.events.schemas import validate
from django.core.exceptions import ValidationError
from django.utils import timezone as django_timezone

from .models import AssetProjection, MaintenancePlan, ProcessedEvent, WorkOrderRequest


def build_workorder_requested_payload(plan, requested_by_id=None):
    request = WorkOrderRequest.objects.create(
        plan=plan,
        requested_by_id=requested_by_id,
    )
    payload = {
        'request_id': str(request.request_id),
        'source': 'maintenance',
        'asset_id': plan.equipment_id,
        'asset_code': plan.equipment_code,
        'wo_type': 'PM',
        'priority': plan.priority,
        'summary': f'预防性维护 - {plan.title}',
        'description': plan.description or '',
        'maintenance_plan_id': plan.id,
        'inspection_record_id': None,
        'requested_by_id': requested_by_id,
        'due_date': None,
    }
    return request, payload


def request_work_order(plan, requested_by=None):
    requested_by_id = getattr(requested_by, 'id', None) if requested_by else None
    request, payload = build_workorder_requested_payload(plan, requested_by_id)
    event = Event(
        type='workorder.requested',
        payload=payload,
        source='maintenance',
    )
    validate(event)
    get_event_bus().publish(event)
    return request


def _asset_projection_payload(payload):
    return {
        'code': payload['code'],
        'name': payload['name'],
        'status': payload['status'],
        'process': payload['process'],
        'factory': payload['factory'],
        'workshop': payload['workshop'],
        'line': payload['line'],
        'station': payload['station'],
    }


def handle_event(event):
    if isinstance(event, dict):
        event = Event.from_dict(event)
    processed, created = ProcessedEvent.objects.get_or_create(
        event_id=event.id,
        defaults={'event_type': event.type},
    )
    if not created:
        return False

    payload = event.payload
    if event.type in {'asset.created', 'asset.updated'}:
        defaults = _asset_projection_payload(payload)
        AssetProjection.objects.update_or_create(
            asset_id=payload['asset_id'],
            defaults=defaults,
        )
        MaintenancePlan.objects.filter(
            equipment_id=payload['asset_id'],
        ).update(
            equipment_code=payload['code'],
            equipment_name=payload['name'],
        )
    elif event.type == 'workorder.created' and payload.get('request_id'):
        try:
            WorkOrderRequest.objects.filter(
                pk=payload['request_id'],
            ).update(
                status='fulfilled',
                work_order_id=payload.get('work_order_id'),
                wo_code=payload.get('wo_code', ''),
                fulfilled_at=django_timezone.now(),
            )
        except (ValueError, TypeError, ValidationError):
            pass
    return True
