import pytest
from rest_framework.test import APIClient

from cmms_common.auth.jwks import RemoteUser
from cmms_common.events import bus as bus_module
from cmms_common.events.bus import InMemoryEventBus

from assetregistry.models import Asset


@pytest.fixture
def event_bus(monkeypatch):
    bus = InMemoryEventBus()
    monkeypatch.setattr(bus_module, '_in_memory_bus', bus)
    monkeypatch.setattr('assets_service.settings.EVENT_BUS_URL', None, raising=False)
    monkeypatch.delenv('EVENT_BUS_URL', raising=False)
    return bus


@pytest.fixture
def admin_user():
    return RemoteUser(user_id=7, username='admin', role='admin', full_name='Admin User')


@pytest.fixture
def operator_user():
    return RemoteUser(user_id=9, username='operator', role='operator', full_name='Operator')


@pytest.fixture
def api_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def operator_client(operator_user):
    client = APIClient()
    client.force_authenticate(user=operator_user)
    return client


@pytest.fixture
def asset_factory(admin_user):
    def create(**kwargs):
        kwargs.setdefault('code', f'EQ-{Asset.objects.count() + 1:03d}')
        kwargs.setdefault('name', 'Machine')
        kwargs.setdefault('created_by_id', admin_user.id)
        kwargs.setdefault('created_by_name', admin_user.full_name)
        return Asset.objects.create(**kwargs)

    return create
