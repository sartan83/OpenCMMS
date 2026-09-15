import pytest

from cmms_common.events import get_event_bus, validate

from .test_api import part_payload


@pytest.mark.django_db
def test_stock_out_publishes_consumed_and_audit_events(client):
    response = client.post(
        '/api/spareparts/',
        part_payload(current_stock='5.00'),
        format='json',
    )
    part_id = response.data['id']
    client.post(
        f'/api/spareparts/{part_id}/stock_out/',
        {'quantity': '2', 'related_work_order': 42},
        format='json',
    )

    events = get_event_bus().published
    consumed = [event for event in events if event.type == 'part.consumed']
    audits = [event for event in events if event.type == 'audit.recorded']
    assert len(consumed) == 1
    validate(consumed[0])
    assert consumed[0].payload['part_id'] == part_id
    assert consumed[0].payload['quantity'] == '2'
    assert consumed[0].payload['work_order_id'] == 42
    assert len(audits) == 1
    assert audits[0].payload['service'] == 'spareparts'
    assert audits[0].payload['action'] == 'stock_out'


@pytest.mark.django_db
def test_stock_in_publishes_audit_only(client):
    response = client.post('/api/spareparts/', part_payload(), format='json')
    client.post(
        f"/api/spareparts/{response.data['id']}/stock_in/",
        {'quantity': '1'},
        format='json',
    )
    events = get_event_bus().published
    assert [event.type for event in events] == ['audit.recorded']
    assert events[0].payload['service'] == 'spareparts'
    assert events[0].payload['action'] == 'stock_in'
