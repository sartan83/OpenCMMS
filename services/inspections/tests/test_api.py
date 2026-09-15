import pytest

from inspection.models import InspectionRecord, InspectionRoute, InspectionTemplate


@pytest.mark.django_db
def test_template_crud(client):
    payload = {
        'code': 'TMP-001',
        'name': 'Routine',
        'description': 'Routine checks',
        'items_template': [{'item': 'Temp', 'unit': 'C', 'threshold': '80'}],
        'equipment_type': 'pump',
        'frequency_days': 7,
        'is_active': True,
    }
    response = client.post('/api/inspections/templates/', payload, format='json')
    assert response.status_code == 201
    template_id = response.json()['id']
    assert client.get('/api/inspections/templates/').status_code == 200
    assert client.get(f'/api/inspections/templates/{template_id}/').status_code == 200
    assert client.patch(
        f'/api/inspections/templates/{template_id}/',
        {'name': 'Updated'},
        format='json',
    ).status_code == 200
    assert client.delete(f'/api/inspections/templates/{template_id}/').status_code == 204
    assert not InspectionTemplate.objects.filter(id=template_id).exists()


@pytest.mark.django_db
def test_route_crud(client, user):
    payload = {
        'code': 'ROUTE-001',
        'name': 'Daily route',
        'description': '',
        'route_items': [{'sequence': 1, 'equipment_id': 1, 'template_id': 1}],
        'estimated_duration_minutes': 30,
        'inspector': user.id,
        'is_active': True,
    }
    response = client.post('/api/inspections/routes/', payload, format='json')
    assert response.status_code == 201
    route_id = response.json()['id']
    assert response.json()['inspector_name'] == 'Ins Pector'
    assert client.get('/api/inspections/routes/').status_code == 200
    assert client.get(f'/api/inspections/routes/{route_id}/').status_code == 200
    assert client.patch(
        f'/api/inspections/routes/{route_id}/',
        {'name': 'Updated route'},
        format='json',
    ).status_code == 200
    assert client.delete(f'/api/inspections/routes/{route_id}/').status_code == 204
    assert not InspectionRoute.objects.filter(id=route_id).exists()


@pytest.mark.django_db
def test_record_crud_and_filters(client, asset, user):
    payload = {
        'equipment': asset.asset_id,
        'items': [{
            'item': 'Temp',
            'value': '70',
            'unit': 'C',
            'threshold': '80',
            'ok': True,
        }],
        'notes': 'x',
    }
    response = client.post('/api/inspections/', payload, format='json')
    assert response.status_code == 201
    record = response.json()
    record_id = record['id']
    assert record['result'] == 'pass'
    assert record['equipment_code'] == 'EQ-001'
    assert record['inspector'] == user.id
    assert record['inspector_name'] == 'Ins Pector'
    assert client.get('/api/inspections/').status_code == 200
    assert len(client.get('/api/inspections/?equipment=1').json()['results']) == 1
    assert len(client.get('/api/inspections/?result=pass').json()['results']) == 1
    assert client.get(f'/api/inspections/{record_id}/').status_code == 200
    assert client.patch(
        f'/api/inspections/{record_id}/',
        {'notes': 'updated'},
        format='json',
    ).status_code == 200
    delete_response = client.delete(f'/api/inspections/{record_id}/')
    assert delete_response.status_code in (404, 405)
    assert InspectionRecord.objects.filter(id=record_id).exists()


@pytest.mark.django_db
def test_unauthenticated_client_is_rejected():
    from rest_framework.test import APIClient

    assert APIClient().get('/api/inspections/').status_code in (401, 403)
