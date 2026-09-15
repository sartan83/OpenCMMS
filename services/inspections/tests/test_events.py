import pytest

from cmms_common.events import schemas
from cmms_common.events.bus import Event
from inspection.events import handle_event
from inspection.models import AssetProjection, InspectionRecord


@pytest.mark.django_db
def test_failing_record_publishes_events_and_deduplicates(
    client, asset, bus, django_capture_on_commit_callbacks
):
    payload = {
        'equipment': asset.asset_id,
        'items': [{
            'item': 'Temp',
            'value': '90',
            'unit': 'C',
            'threshold': '80',
            'ok': False,
        }],
    }
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post('/api/inspections/', payload, format='json')
    assert response.status_code == 201
    record = InspectionRecord.objects.get(id=response.json()['id'])
    events = [
        event for event in bus.published
        if event.type in {'inspection.failed', 'workorder.requested'}
    ]
    assert len(events) == 2
    failed = next(event for event in events if event.type == 'inspection.failed')
    requested = next(event for event in events if event.type == 'workorder.requested')
    assert failed.payload['failed_items'] == payload['items']
    assert failed.payload['work_order_id'] is None
    assert requested.payload['source'] == 'inspection'
    assert requested.payload['wo_type'] == 'CM'
    assert requested.payload['priority'] == 'high'
    assert requested.payload['inspection_record_id'] == record.id
    assert requested.payload['request_id'] == record.work_order_request_id
    schemas.validate(failed)
    schemas.validate(requested)

    before = len([
        event for event in bus.published
        if event.type in {'inspection.failed', 'workorder.requested'}
    ])
    client.patch(
        f'/api/inspections/{record.id}/',
        {'notes': 'updated'},
        format='json',
    )
    assert len([
        event for event in bus.published
        if event.type in {'inspection.failed', 'workorder.requested'}
    ]) == before

    workorder_event = Event(
        type='workorder.created',
        source='workorders',
        payload={
            'work_order_id': 42,
            'wo_code': 'WO-042',
            'asset_id': asset.asset_id,
            'status': 'open',
            'wo_type': 'CM',
            'assignee_id': None,
            'actor_id': 7,
            'maintenance_plan_id': None,
            'created_at': '2025-01-01T00:00:00+00:00',
            'request_id': record.work_order_request_id,
        },
    )
    assert handle_event(workorder_event) is True
    assert InspectionRecord.objects.get(id=record.id).triggered_work_order_id == 42
    assert handle_event(workorder_event) is False


@pytest.mark.django_db
def test_asset_event_updates_projection_and_record(asset, bus):
    record = InspectionRecord.objects.create(
        equipment=asset.asset_id,
        items=[],
        inspector_id=7,
        inspector_name='Ins Pector',
    )
    asset_event = Event(
        type='asset.created',
        source='assets',
        payload={
            'asset_id': asset.asset_id,
            'code': 'EQ-UPDATED',
            'name': 'Updated pump',
            'status': 'active',
            'process': '',
            'factory': '',
            'workshop': '',
            'line': '',
            'station': '',
        },
    )
    assert handle_event(asset_event) is True
    projection = AssetProjection.objects.get(asset_id=asset.asset_id)
    assert projection.code == 'EQ-UPDATED'
    record.refresh_from_db()
    assert record.equipment_code == 'EQ-UPDATED'
    assert record.equipment_name == 'Updated pump'


@pytest.mark.django_db
def test_passing_record_publishes_no_inspection_events(
    client, asset, bus, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            '/api/inspections/',
            {'equipment': asset.asset_id, 'items': [{'item': 'Temp', 'ok': True}]},
            format='json',
        )
    assert response.status_code == 201
    assert not [
        event for event in bus.published
        if event.type in {'inspection.failed', 'workorder.requested'}
    ]
