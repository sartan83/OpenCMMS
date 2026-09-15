from django.db import transaction

from cmms_common.events import schemas
from cmms_common.events.bus import Event, get_event_bus

from .models import AssetProjection, InspectionRecord, ProcessedEvent


def publish_inspection_failed(record):
    bus = get_event_bus()
    failed_items = [item for item in record.items if not item.get('ok', True)]
    failed_event = Event(
        type='inspection.failed',
        source='inspections',
        payload={
            'inspection_record_id': record.id,
            'asset_id': record.equipment,
            'work_order_id': None,
            'failed_items': failed_items,
            'inspector_id': record.inspector_id,
        },
    )
    schemas.validate(failed_event)
    bus.publish(failed_event)

    description = 'Failed inspection items:\n' + '\n'.join(
        f"- {item.get('item', '')}: {item.get('value', '')} "
        f"{item.get('unit', '')} (threshold {item.get('threshold', '')})"
        for item in failed_items
    )
    requested_event = Event(
        type='workorder.requested',
        source='inspections',
        payload={
            'request_id': record.work_order_request_id,
            'source': 'inspection',
            'asset_id': record.equipment,
            'asset_code': record.equipment_code,
            'wo_type': 'CM',
            'priority': 'high',
            'summary': f'Inspection failure - {record.equipment_code or record.equipment}',
            'description': description,
            'maintenance_plan_id': None,
            'inspection_record_id': record.id,
            'requested_by_id': record.inspector_id,
            'due_date': None,
        },
    )
    schemas.validate(requested_event)
    bus.publish(requested_event)


def handle_event(event):
    if isinstance(event, dict):
        event = Event.from_dict(event)
    with transaction.atomic():
        processed, created = ProcessedEvent.objects.get_or_create(
            event_id=event.id,
            defaults={'event_type': event.type},
        )
        if not created:
            return False
        payload = event.payload
        if event.type in {'asset.created', 'asset.updated'}:
            asset_id = payload['asset_id']
            defaults = {
                field: payload.get(field, '')
                for field in (
                    'code', 'name', 'status', 'process', 'factory',
                    'workshop', 'line', 'station',
                )
            }
            AssetProjection.objects.update_or_create(
                asset_id=asset_id,
                defaults=defaults,
            )
            InspectionRecord.objects.filter(equipment=asset_id).update(
                equipment_code=defaults['code'],
                equipment_name=defaults['name'],
            )
        elif event.type == 'workorder.created' and payload.get('request_id'):
            InspectionRecord.objects.filter(
                work_order_request_id=payload['request_id'],
                triggered_work_order_id__isnull=True,
            ).update(triggered_work_order_id=payload['work_order_id'])
    return True
