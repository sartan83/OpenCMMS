import json
from pathlib import Path

import jsonschema
import pytest
from django.db import transaction

from cmms_common.events.schemas import SCHEMAS, validate

from assetregistry.events import asset_payload, build_asset_event, publish_asset_event

CONTRACTS = Path(__file__).resolve().parents[3] / 'contracts' / 'events'


@pytest.mark.django_db
def test_payload_matches_schema_and_contract(asset_factory):
    asset = asset_factory(code='EV-1', name='Event asset', process=None, factory='F1')
    for event_type in ('asset.created', 'asset.updated'):
        event = build_asset_event(event_type, asset)
        assert event.source == 'assets'
        assert validate(event) is True
        jsonschema.validate(event.payload, SCHEMAS[event_type])
        contract = json.loads((CONTRACTS / f'{event_type}.v1.json').read_text())
        jsonschema.validate(event.payload, contract)
    payload = asset_payload(asset)
    assert payload['asset_id'] == asset.id
    assert payload['process'] == ''


@pytest.mark.django_db
def test_api_create_and_update_publish_after_commit(
    api_client, event_bus, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        response = api_client.post(
            '/api/assets/', {'code': 'EV-2', 'name': 'Created'}, format='json'
        )
    assert response.status_code == 201
    assert [e.type for e in event_bus.published] == ['asset.created']
    assert event_bus.published[0].payload['code'] == 'EV-2'
    assert event_bus.published[0].source == 'assets'

    asset_id = response.json()['id']
    with django_capture_on_commit_callbacks(execute=True):
        response = api_client.patch(
            f'/api/assets/{asset_id}/', {'status': 'maintenance'}, format='json'
        )
    assert response.status_code == 200
    assert [e.type for e in event_bus.published] == ['asset.created', 'asset.updated']
    assert event_bus.published[1].payload['status'] == 'maintenance'


@pytest.mark.django_db
def test_rolled_back_transaction_publishes_nothing(asset_factory, event_bus, django_capture_on_commit_callbacks):
    asset = asset_factory(code='EV-3')

    class Rollback(Exception):
        pass

    with django_capture_on_commit_callbacks(execute=True):
        with pytest.raises(Rollback):
            with transaction.atomic():
                publish_asset_event('asset.updated', asset)
                raise Rollback
    assert event_bus.published == []
