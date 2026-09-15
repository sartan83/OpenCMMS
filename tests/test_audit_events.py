import pytest

from cmms_common.events.bus import get_event_bus
from users.models import AuditLog


@pytest.mark.django_db
def test_assign_publishes_audit_event_and_writes_local_log(
    authenticated_client,
    work_order,
    technician_user,
):
    bus = get_event_bus()
    bus.published.clear()
    before = AuditLog.objects.count()

    response = authenticated_client.post(
        f'/api/workorders/{work_order.id}/assign/',
        {'assignee_id': technician_user.id},
        format='json',
    )

    assert response.status_code == 200
    events = [event for event in bus.published if event.type == 'audit.recorded']
    assert len(events) == 1
    assert events[0].payload['action'] == 'assign'
    assert AuditLog.objects.count() == before + 1
