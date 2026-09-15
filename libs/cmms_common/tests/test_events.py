import json
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from cmms_common.events.bus import Event, InMemoryEventBus
from cmms_common.events.schemas import validate


def test_in_memory_bus_publishes_and_dispatches():
    bus = InMemoryEventBus()
    received = []
    bus.subscribe(['asset.created'], received.append, 'test')
    event = Event('asset.created', payload={
        'asset_id': 1,
        'code': 'A-1',
        'name': 'Pump',
        'status': 'active',
        'process': 'P',
        'factory': 'F',
        'workshop': 'W',
        'line': 'L',
        'station': 'S',
    }, source='test')

    assert bus.publish(event) is True
    assert bus.published == [event]
    assert received == [event]


def test_schema_validation_rejects_invalid_payload():
    event = Event('asset.created', payload={'asset_id': 'not-an-int'}, source='test')
    with pytest.raises(Exception):
        validate(event)


def test_in_memory_bus_json_encodes_common_django_types():
    bus = InMemoryEventBus()
    event = Event(
        'test.event',
        payload={
            'amount': Decimal('1.50'),
            'today': date.today(),
            'identifier': uuid4(),
        },
        source='test',
    )

    assert bus.publish(event) is True
    payload = bus.published[0].to_dict()['payload']

    assert json.dumps(payload)
    assert payload['amount'] == '1.50'
    assert payload['today'] == date.today().isoformat()
    assert isinstance(payload['identifier'], str)
