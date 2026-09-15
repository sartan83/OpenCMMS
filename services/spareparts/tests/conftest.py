import pytest
from rest_framework.test import APIClient

from cmms_common.auth.jwks import RemoteUser


@pytest.fixture
def user():
    return RemoteUser(user_id=7, username='op', role='engineer', full_name='Op Erator')


@pytest.fixture
def client(user):
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture(autouse=True)
def reset_event_bus(monkeypatch, settings):
    import cmms_common.events.bus as bus_mod

    bus_mod._in_memory_bus = None
    monkeypatch.delenv('EVENT_BUS_URL', raising=False)
    settings.EVENT_BUS_URL = None
    yield
    bus_mod._in_memory_bus = None
