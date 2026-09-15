import logging
from datetime import datetime, time, timezone as dt_timezone

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from cmms_common.events.bus import Event, get_event_bus
from workorders_api.events import publish_workorder_created
from workorders_api.models import (AssetProjection, ProcessedEvent, WorkOrder,
                               WorkOrderStatus, generate_wo_code)

logger = logging.getLogger('cmms.workorders')

ROUTING_KEYS = ['asset.created', 'asset.updated', 'workorder.requested']
QUEUE_NAME = 'workorders-service'


def _parse_due_date(value):
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        day = parse_date(value)
        if day is None:
            return None
        parsed = datetime.combine(day, time.min)
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, dt_timezone.utc)
    return parsed


def handle_asset_event(event):
    payload = event.payload
    AssetProjection.objects.update_or_create(
        asset_id=payload['asset_id'],
        defaults={
            'code': payload['code'],
            'name': payload['name'],
            'status': payload.get('status', ''),
            'process': payload.get('process', ''),
            'factory': payload.get('factory', ''),
            'workshop': payload.get('workshop', ''),
            'line': payload.get('line', ''),
            'station': payload.get('station', ''),
        },
    )
    WorkOrder.objects.filter(equipment=payload['asset_id']).update(
        equipment_code=payload['code'],
        equipment_name=payload['name'],
    )
    return True


def handle_workorder_requested(event):
    payload = event.payload
    request_id = payload['request_id']
    if WorkOrder.objects.filter(request_id=request_id).exists():
        return False

    projection = AssetProjection.objects.filter(pk=payload['asset_id']).first()
    try:
        with transaction.atomic():
            work_order = WorkOrder.objects.create(
                wo_code=generate_wo_code(payload['wo_type']),
                equipment=payload['asset_id'],
                equipment_code=payload.get('asset_code') or (projection.code if projection else ''),
                equipment_name=projection.name if projection else '',
                wo_type=payload['wo_type'],
                status=WorkOrderStatus.OPEN,
                summary=payload['summary'][:200],
                description=payload.get('description') or '',
                priority=payload.get('priority') or 'medium',
                requested_by_id=payload.get('requested_by_id') or 0,
                requested_by_name=payload['source'],
                maintenance_plan_id=payload.get('maintenance_plan_id'),
                planned_end=_parse_due_date(payload.get('due_date')),
                request_id=request_id,
            )
    except IntegrityError:
        return False
    publish_workorder_created(work_order, 0)
    return True


HANDLERS = {
    'asset.created': handle_asset_event,
    'asset.updated': handle_asset_event,
    'workorder.requested': handle_workorder_requested,
}


def handle_event(event):
    if isinstance(event, dict):
        event = Event.from_dict(event)
    handler = HANDLERS.get(event.type)
    if handler is None:
        return False
    try:
        with transaction.atomic():
            ProcessedEvent.objects.create(event_id=event.id, event_type=event.type)
            return handler(event)
    except IntegrityError:
        return False


class Command(BaseCommand):
    help = 'Consume asset and work-order request events from the shared event bus'

    def handle(self, *args, **options):
        get_event_bus().subscribe(ROUTING_KEYS, handle_event, QUEUE_NAME)
