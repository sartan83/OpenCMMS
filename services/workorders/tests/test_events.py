import pytest

from cmms_common.events.bus import Event
from cmms_common.events.schemas import validate
from workorders_api.events import workorder_payload
from workorders_api.management.commands.consume_events import handle_event
from workorders_api.models import AssetProjection, ProcessedEvent, WorkOrder

pytestmark = pytest.mark.django_db(transaction=True)


def _lifecycle(bus):
    return [e for e in bus.published if e.type.startswith('workorder.')]


def _types(bus):
    return [e.type for e in _lifecycle(bus)]


def test_lifecycle_events_published_and_validate(api_client, asset, event_bus):
    response = api_client.post('/api/workorders/', {
        'equipment': asset.asset_id, 'summary': 'Event test', 'priority': 'high',
        'planned_start': '2026-01-01T08:00:00Z',
    }, format='json')
    wo_id = response.json()['id']
    url = f'/api/workorders/{wo_id}'
    api_client.post(f'{url}/assign/', {'assignee_id': 7, 'assignee_name': 'Tech One'}, format='json')
    api_client.post(f'{url}/start/')
    api_client.post(
        f'{url}/complete/',
        {
            'actions_taken': 'done',
            'downtime_minutes': '15',
            'labor_hours': '1.5',
            'parts_cost': '10',
        },
        format='json',
    )
    api_client.post(f'{url}/close/')

    assert _types(event_bus) == [
        'workorder.created', 'workorder.assigned', 'workorder.completed', 'workorder.closed',
    ]
    for event in _lifecycle(event_bus):
        validate(event)
        assert event.payload['work_order_id'] == wo_id
        assert event.payload['actor_id'] == 1
        assert event.payload['asset_code'] == 'EQ-001'
        assert event.payload['asset_name'] == 'Pump A'
        assert event.payload['priority'] == 'high'
        assert event.payload['title'] == 'Event test'
        assert event.payload['planned_start'] == '2026-01-01T08:00:00+00:00'

    created = _lifecycle(event_bus)[0].payload
    assert created['request_id'] is None
    assert created['assignee_name'] is None
    closed = _lifecycle(event_bus)[-1].payload
    completed = _lifecycle(event_bus)[2].payload
    assert completed['downtime_minutes'] == 15
    assert closed['assignee_name'] == 'Tech One'
    assert closed['labor_hours'] == '1.50'
    assert closed['total_cost'] == '10.00'
    assert closed['actual_end'] is not None


def test_payload_null_when_unknown(work_order):
    payload = workorder_payload(work_order, 0)
    assert payload['assignee_name'] is None
    assert payload['planned_start'] is None
    assert payload['actor_id'] == 0


def _asset_event(event_id, **overrides):
    payload = {
        'asset_id': 555, 'code': 'EQ-555', 'name': 'Compressor', 'status': 'active',
        'process': '', 'factory': '', 'workshop': '', 'line': '', 'station': '',
        'actor_id': 1,
    }
    payload.update(overrides)
    return Event(type='asset.created', payload=payload, id=event_id, version=1)


def test_asset_events_build_projection_and_refresh_cached_columns(admin_user):
    assert handle_event(_asset_event('evt-1')) is True
    projection = AssetProjection.objects.get(pk=555)
    assert projection.code == 'EQ-555'

    wo = WorkOrder.objects.create(equipment=555, summary='x', requested_by_id=1)
    assert wo.equipment_code == 'EQ-555'

    updated = _asset_event('evt-2', name='Compressor B')
    updated.type = 'asset.updated'
    assert handle_event(updated) is True
    wo.refresh_from_db()
    assert wo.equipment_name == 'Compressor B'

    assert handle_event(_asset_event('evt-2')) is False
    assert ProcessedEvent.objects.count() == 2


def _requested(request_id, source, wo_type, event_id=None):
    return Event(
        type='workorder.requested',
        id=event_id or f'evt-{request_id}',
        version=1,
        payload={
            'request_id': request_id, 'source': source, 'wo_type': wo_type,
            'asset_id': 101, 'asset_code': 'EQ-001', 'summary': f'{source} request',
            'description': 'auto', 'priority': 'medium', 'due_date': '2026-02-01',
            'maintenance_plan_id': 9 if source == 'maintenance' else None,
            'requested_by_id': 3, 'actor_id': 0,
        },
    )


@pytest.mark.parametrize('source,wo_type,prefix', [
    ('maintenance', 'PM', 'PM-'),
    ('inspection', 'CM', 'CM-'),
])
def test_workorder_requested_creates_and_publishes(asset, event_bus, source, wo_type, prefix):
    assert handle_event(_requested(f'req-{source}', source, wo_type)) is True
    wo = WorkOrder.objects.get(request_id=f'req-{source}')
    assert wo.wo_code.startswith(prefix)
    assert wo.wo_type == wo_type
    assert wo.equipment_name == 'Pump A'
    assert wo.planned_end is not None
    if source == 'maintenance':
        assert wo.maintenance_plan_id == 9

    assert _types(event_bus) == ['workorder.created']
    event = _lifecycle(event_bus)[0]
    validate(event)
    assert event.payload['request_id'] == f'req-{source}'
    assert event.payload['actor_id'] == 0
    assert event.payload['maintenance_plan_id'] == wo.maintenance_plan_id


def test_workorder_requested_dedupes_on_request_id(asset, event_bus):
    assert handle_event(_requested('req-dup', 'inspection', 'CM', event_id='e1')) is True
    assert handle_event(_requested('req-dup', 'inspection', 'CM', event_id='e2')) is False
    assert WorkOrder.objects.filter(request_id='req-dup').count() == 1
    assert len(_lifecycle(event_bus)) == 1
