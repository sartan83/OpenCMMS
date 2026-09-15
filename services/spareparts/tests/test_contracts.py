import pytest

from cmms_common.contracts import assert_matches_contract

from .test_api import part_payload


@pytest.mark.django_db
def test_spare_part_contract(client):
    response = client.post('/api/spareparts/', part_payload(), format='json')
    assert_matches_contract(response.json(), 'spareparts', 'SparePartSerializer')


@pytest.mark.django_db
def test_transaction_contract(client):
    response = client.post('/api/spareparts/', part_payload(), format='json')
    client.post(
        f"/api/spareparts/{response.data['id']}/stock_in/",
        {'quantity': '1'},
        format='json',
    )
    response = client.get('/api/spareparts/transactions/')
    assert response.status_code == 200
    assert_matches_contract(response.json()[0], 'spareparts', 'PartTransactionSerializer')
