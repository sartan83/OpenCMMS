import pytest

from cmms_common.auth.jwks import RemoteUser
from pm.models import MaintenancePlan, WorkOrderRequest, WorkOrderTemplate


def plan_data(**overrides):
    data = {
        'code': 'PM-001',
        'equipment': 10,
        'title': 'Lubricate press',
        'description': 'Apply grease',
        'frequency_value': 1,
        'frequency_unit': 'day',
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_plan_crud_and_actions(api_client, asset, bus):
    response = api_client.post('/api/maintenance/plans/', plan_data(), format='json')
    assert response.status_code == 201
    assert response.data['equipment_code'] == 'EQ-001'
    assert response.data['created_by'] == 1
    assert response.data['created_by_name'] == 'Admin User'
    plan_id = response.data['id']

    assert api_client.post(
        '/api/maintenance/plans/', plan_data(code='PM-002', equipment=99), format='json'
    ).status_code == 400
    listed = api_client.get('/api/maintenance/plans/?equipment=10')
    assert listed.status_code == 200
    assert len(listed.data['results']) == 1
    assert api_client.get(f'/api/maintenance/plans/{plan_id}/').status_code == 200
    assert api_client.patch(
        f'/api/maintenance/plans/{plan_id}/', {'title': 'Updated'}, format='json'
    ).status_code == 200
    assert api_client.post(f'/api/maintenance/plans/{plan_id}/deactivate/').status_code == 200
    assert api_client.post(f'/api/maintenance/plans/{plan_id}/activate/').status_code == 200
    response = api_client.post(f'/api/maintenance/plans/{plan_id}/generate_work_order/')
    assert response.status_code == 200
    assert set(response.data) == {'message', 'request_id', 'work_order_id', 'wo_code'}
    assert WorkOrderRequest.objects.get(pk=response.data['request_id']).status == 'pending'
    assert {event.type for event in bus.published} >= {'workorder.requested', 'audit.recorded'}
    assert api_client.delete(f'/api/maintenance/plans/{plan_id}/').status_code == 204


@pytest.mark.django_db
def test_inactive_and_templates_and_permissions(api_client, asset):
    plan = MaintenancePlan.objects.create(
        code='PM-INACTIVE',
        equipment_id=asset.asset_id,
        equipment_code=asset.code,
        equipment_name=asset.name,
        title='Inactive',
        created_by_id=1,
        is_active=False,
    )
    assert api_client.post(
        f'/api/maintenance/plans/{plan.pk}/generate_work_order/'
    ).status_code == 400
    response = api_client.post(
        '/api/maintenance/templates/',
        {'code': 'TPL-1', 'name': 'Template'},
        format='json',
    )
    assert response.status_code == 201
    assert WorkOrderTemplate.objects.count() == 1
    api_client.force_authenticate(user=RemoteUser(2, 'tech', 'technician', 'Tech'))
    assert api_client.post(
        '/api/maintenance/plans/',
        plan_data(code='PM-TECH'),
        format='json',
    ).status_code == 403
