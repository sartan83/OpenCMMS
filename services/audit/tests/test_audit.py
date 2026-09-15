import pytest

from auditlog.models import AuditEntry
from cmms_common.events.bus import Event
from auditlog.management.commands.consume_events import handle_audit_event


@pytest.mark.django_db
def test_audit_event_is_stored():
    event = Event(
        type='audit.recorded',
        source='monolith',
        payload={
            'actor_id': 4,
            'actor_username': 'operator',
            'action': 'update',
            'entity_type': 'Asset',
            'entity_id': 8,
            'entity_repr': 'Asset 8',
            'diff': {'status': ['old', 'new']},
            'ip_address': None,
            'user_agent': 'pytest',
            'service': 'monolith',
        },
    )

    assert handle_audit_event(event.to_dict()) is True
    entry = AuditEntry.objects.get(event_id=event.id)
    assert entry.actor_id == 4
    assert entry.diff == {'status': ['old', 'new']}
    assert handle_audit_event(event.to_dict()) is False
