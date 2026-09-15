import pytest
from rest_framework.test import APIClient

from cmms_common.auth.jwks import RemoteUser
from cmms_common.events.bus import InMemoryEventBus, get_event_bus
from inspection.models import AssetProjection


@pytest.fixture
def user():
    return RemoteUser(7, 'inspector', 'engineer', 'Ins Pector')


@pytest.fixture
def client(user):
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture(autouse=True)
def bus():
    event_bus = get_event_bus()
    assert isinstance(event_bus, InMemoryEventBus)
    event_bus.published.clear()
    event_bus._subscribers.clear()
    yield event_bus


@pytest.fixture
def asset():
    return AssetProjection.objects.create(
        asset_id=1,
        code='EQ-001',
        name='Pump 1',
        status='active',
    )
