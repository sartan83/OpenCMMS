import pytest

from cmms_common.contracts import assert_matches_contract

from .test_api import plan_data


@pytest.mark.django_db
def test_plan_contracts(api_client, asset):
    response = api_client.post('/api/maintenance/plans/', plan_data(), format='json')
    assert_matches_contract(response.json(), 'maintenance', 'MaintenancePlanSerializer')
    listed = api_client.get('/api/maintenance/plans/').json()[0]
    assert_matches_contract(listed, 'maintenance', 'MaintenancePlanListSerializer')
    template = api_client.post(
        '/api/maintenance/templates/',
        {'code': 'TPL-C', 'name': 'Contract'},
        format='json',
    )
    assert_matches_contract(template.json(), 'maintenance', 'WorkOrderTemplateSerializer')
