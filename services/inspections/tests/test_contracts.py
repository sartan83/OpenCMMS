import pytest

from cmms_common.contracts import assert_matches_contract


@pytest.mark.django_db
def test_inspection_contracts(client, asset, user):
    template = client.post(
        '/api/inspections/templates/',
        {
            'code': 'TMP-CONTRACT',
            'name': 'Contract template',
            'items_template': [],
        },
        format='json',
    )
    assert template.status_code == 201
    assert_matches_contract(
        template.json(), 'inspections', 'InspectionTemplateSerializer'
    )

    route = client.post(
        '/api/inspections/routes/',
        {
            'code': 'ROUTE-CONTRACT',
            'name': 'Contract route',
            'route_items': [],
            'inspector': user.id,
        },
        format='json',
    )
    assert route.status_code == 201
    assert_matches_contract(
        route.json(), 'inspections', 'InspectionRouteSerializer'
    )

    record = client.post(
        '/api/inspections/',
        {'equipment': asset.asset_id, 'items': []},
        format='json',
    )
    assert record.status_code == 201
    assert_matches_contract(
        record.json(), 'inspections', 'InspectionRecordSerializer'
    )
