from decimal import Decimal

import pytest

from inventory.models import PartTransaction, SparePart


def part_payload(**overrides):
    payload = {
        'part_code': 'P-100',
        'name': 'Bearing',
        'unit': 'pcs',
        'current_stock': '2.00',
        'min_stock': '1.00',
        'safety_stock': '1.00',
        'unit_cost': '4.50',
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_spare_part_crud_and_low_stock(client):
    response = client.post('/api/spareparts/', part_payload(), format='json')
    assert response.status_code == 201
    part_id = response.data['id']
    part = SparePart.objects.get(pk=part_id)
    assert part.created_by_id == 7
    assert part.created_by_name == 'Op Erator'

    assert client.get('/api/spareparts/').status_code == 200
    assert client.get(f'/api/spareparts/{part_id}/').status_code == 200
    assert client.get('/api/spareparts/?low_stock=true').status_code == 200
    assert client.patch(f'/api/spareparts/{part_id}/', {'name': 'Large Bearing'}, format='json').status_code == 200
    assert client.delete(f'/api/spareparts/{part_id}/').status_code == 204


@pytest.mark.django_db
def test_stock_actions_and_transaction_filters(client):
    response = client.post('/api/spareparts/', part_payload(), format='json')
    part_id = response.data['id']

    response = client.post(f'/api/spareparts/{part_id}/stock_in/', {'quantity': '3.5'}, format='json')
    assert response.status_code == 200
    txn = PartTransaction.objects.get()
    assert txn.operator_id == 7
    assert txn.operator_name == 'Op Erator'
    assert txn.quantity == Decimal('3.50')

    assert client.post(
        f'/api/spareparts/{part_id}/stock-in/', {'quantity': '1'}, format='json'
    ).status_code == 200
    assert client.post(
        f'/api/spareparts/{part_id}/stock_out/', {'quantity': '100'}, format='json'
    ).status_code == 400
    assert client.post(
        f'/api/spareparts/{part_id}/stock-out/',
        {'quantity': '1', 'related_work_order': 42},
        format='json',
    ).status_code == 200

    txn = PartTransaction.objects.filter(transaction_type='out').get()
    assert txn.related_work_order == 42
    assert client.get(f'/api/spareparts/transactions/?part={part_id}').status_code == 200
    filtered = client.get('/api/spareparts/transactions/?related_work_order=42')
    assert filtered.status_code == 200
    assert len(filtered.data['results']) == 1

    for path in ('stock_in', 'stock-out'):
        assert client.post(
            f'/api/spareparts/{part_id}/{path}/', {'quantity': 0}, format='json'
        ).status_code == 400


@pytest.mark.django_db
def test_unauthenticated_request_is_rejected():
    from rest_framework.test import APIClient

    assert APIClient().get('/api/spareparts/').status_code in (401, 403)
