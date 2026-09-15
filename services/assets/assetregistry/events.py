from django.db import transaction

from cmms_common.events.bus import Event, get_event_bus
from cmms_common.events.schemas import validate

SOURCE = 'assets'


def asset_payload(asset):
    return {
        'asset_id': asset.id,
        'code': asset.code,
        'name': asset.name,
        'status': asset.status,
        'process': asset.process or '',
        'factory': asset.factory or '',
        'workshop': asset.workshop or '',
        'line': asset.line or '',
        'station': asset.station or '',
    }


def build_asset_event(event_type, asset):
    event = Event(type=event_type, payload=asset_payload(asset), source=SOURCE)
    validate(event)
    return event


def publish_asset_event(event_type, asset):
    """Publish an asset lifecycle event once the surrounding transaction commits."""
    event = build_asset_event(event_type, asset)
    transaction.on_commit(lambda: get_event_bus().publish(event))
    return event
