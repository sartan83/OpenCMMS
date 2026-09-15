import pytest
from rest_framework.test import APIClient

from cmms_common.auth.jwks import RemoteUser
from cmms_common.events import bus as bus_module
from cmms_common.events.bus import InMemoryEventBus
from workorders_api.models import AssetProjection, WorkOrder


@pytest.fixture
def event_bus(monkeypatch):
    fresh = InMemoryEventBus()
    monkeypatch.setattr(bus_module, '_in_memory_bus', fresh)
    return fresh


@pytest.fixture
def admin_user():
    return RemoteUser(1, username='admin', role='admin', full_name='Admin User')


@pytest.fixture
def technician_user():
    return RemoteUser(7, username='tech', role='technician', full_name='Tech One')


@pytest.fixture
def api_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def technician_client(technician_user):
    client = APIClient()
    client.force_authenticate(user=technician_user)
    return client


@pytest.fixture
def asset():
    return AssetProjection.objects.create(
        asset_id=101, code='EQ-001', name='Pump A', status='active',
    )


@pytest.fixture
def work_order(asset, admin_user):
    return WorkOrder.objects.create(
        equipment=asset.asset_id,
        wo_type='CM',
        summary='Pump leaking',
        description='Leak on seal',
        priority='high',
        requested_by_id=admin_user.id,
        requested_by_name=admin_user.full_name,
    )
