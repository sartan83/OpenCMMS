import pytest
from rest_framework.test import APIClient

from cmms_common.auth.jwks import RemoteUser
from cmms_common.events import bus as event_bus
from cmms_common.events.bus import InMemoryEventBus, get_event_bus
from pm.models import AssetProjection


@pytest.fixture
def bus():
    event_bus._in_memory_bus = None
    result = get_event_bus()
    assert isinstance(result, InMemoryEventBus)
    return result


@pytest.fixture
def api_client():
    client = APIClient()
    client.force_authenticate(user=RemoteUser(1, 'admin', 'admin', 'Admin User'))
    return client


@pytest.fixture
def asset():
    return AssetProjection.objects.create(
        asset_id=10,
        code='EQ-001',
        name='Press',
        status='active',
    )
