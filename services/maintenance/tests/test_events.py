from datetime import datetime, timezone

import pytest

from cmms_common.events.bus import Event
from cmms_common.events.schemas import validate
from pm.events import handle_event
from pm.models import MaintenancePlan, WorkOrderRequest

from .test_api import plan_data


@pytest.mark.django_db
def test_event_handlers_and_dedupe(api_client, asset, bus):
    response = api_client.post('/api/maintenance/plans/', plan_data(), format='json')
    request = api_client.post(
        f"/api/maintenance/plans/{response.data['id']}/generate_work_order/"
    )
    published = next(event for event in bus.published if event.type == 'workorder.requested')
    validate(published)
    plan = MaintenancePlan.objects.get(pk=response.data['id'])
    asset_event = Event(
        type='asset.created',
        payload={
            'asset_id': 10, 'code': 'EQ-NEW', 'name': 'New Press', 'status': 'active',
            'process': '', 'factory': '', 'workshop': '', 'line': '', 'station': '',
        },
    )
    assert handle_event(asset_event) is True
    assert MaintenancePlan.objects.get(pk=plan.pk).equipment_name == 'New Press'
    assert handle_event(asset_event) is False
    created = Event(
        type='workorder.created',
        payload={
            'work_order_id': 44, 'wo_code': 'WO-44', 'asset_id': 10, 'status': 'open',
            'wo_type': 'PM', 'assignee_id': None, 'actor_id': 1,
            'maintenance_plan_id': plan.id,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'request_id': request.data['request_id'],
        },
    )
    assert handle_event(created) is True
    work_order_request = WorkOrderRequest.objects.get(pk=request.data['request_id'])
    assert work_order_request.status == 'fulfilled'
    assert work_order_request.work_order_id == 44
