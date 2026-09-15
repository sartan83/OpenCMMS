from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from cmms_common.events.bus import Event, get_event_bus
from auditlog.models import AuditEntry


def handle_audit_event(event):
    if isinstance(event, dict):
        event = Event.from_dict(event)
    payload = event.payload
    try:
        AuditEntry.objects.create(
            event_id=event.id,
            actor_id=payload['actor_id'],
            actor_username=payload['actor_username'],
            action=payload['action'],
            entity_type=payload['entity_type'],
            entity_id=payload['entity_id'],
            entity_repr=payload.get('entity_repr', ''),
            diff=payload.get('diff', {}),
            ip_address=payload.get('ip_address'),
            user_agent=payload.get('user_agent', ''),
            service=payload['service'],
            occurred_at=datetime.fromisoformat(event.occurred_at.replace('Z', '+00:00')),
        )
    except IntegrityError:
        return False
    return True


class Command(BaseCommand):
    help = 'Consume audit events from the shared event bus'

    def handle(self, *args, **options):
        get_event_bus().subscribe(
            ['audit.recorded'],
            handle_audit_event,
            'audit-service',
        )
