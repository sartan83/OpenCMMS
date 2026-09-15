from datetime import datetime, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from django.core.management import call_command
from django.conf import settings
from django.db import connections
from django.test.utils import override_settings
from rest_framework.test import APIClient

from cmms_common.auth.keys import jwks_from_public_key
from cmms_common.events.bus import Event, get_event_bus
from cmms_common.events.schemas import validate

from analytics.management.commands.consume_events import dispatch_event
from analytics.models import (
    AssetProjection,
    InspectionFact,
    PartConsumptionFact,
    ProcessedEvent,
    ReportRun,
    WorkOrderFact,
)
from analytics.projections import HANDLERS


def event(event_type, payload, event_id):
    item = Event(
        type=event_type,
        id=event_id,
        source='pytest',
        occurred_at='2025-01-15T10:00:00+00:00',
        payload=payload,
    )
    validate(item)
    return item


def asset_event(event_id='asset-event'):
    return event('asset.created', {
        'asset_id': 1,
        'code': 'A-1',
        'name': 'Press',
        'status': 'active',
        'process': 'Stamping',
        'factory': 'F1',
        'workshop': 'W1',
        'line': 'L1',
        'station': 'S1',
    }, event_id)


def workorder_payload(**overrides):
    payload = {
        'work_order_id': 5,
        'wo_code': 'WO-5',
        'asset_id': 1,
        'asset_code': 'A-1',
        'asset_name': 'Press',
        'status': 'open',
        'wo_type': 'PM',
        'assignee_id': 7,
        'assignee_name': 'Tech',
        'actor_id': 7,
        'maintenance_plan_id': 3,
        'priority': 'high',
        'title': 'Inspect press',
        'planned_start': '2025-01-15T08:00:00+00:00',
        'planned_end': '2025-01-15T12:00:00+00:00',
        'actual_start': '2025-01-15T08:30:00+00:00',
        'actual_end': '2025-01-15T10:30:00+00:00',
        'downtime_minutes': 120,
        'labor_hours': '2.50',
        'parts_cost': '23.45',
        'total_cost': '123.45',
    }
    payload.update(overrides)
    return payload


@pytest.fixture(autouse=True)
def clean_in_memory_bus():
    bus = get_event_bus()
    bus.published.clear()
    bus._subscribers.clear()
    yield
    bus.published.clear()
    bus._subscribers.clear()


@pytest.mark.django_db
@pytest.mark.parametrize('event_factory,model', [
    (asset_event, AssetProjection),
    (
        lambda event_id: event(
            'workorder.created',
            workorder_payload(created_at='2025-01-15T09:00:00+00:00'),
            event_id,
        ),
        WorkOrderFact,
    ),
    (
        lambda event_id: event('part.consumed', {
            'transaction_id': 8, 'part_id': 2, 'part_code': 'P-2',
            'quantity': '2.00', 'unit_cost': '10.00', 'work_order_id': 5,
            'actor_id': 7,
        }, event_id),
        PartConsumptionFact,
    ),
    (
        lambda event_id: event('inspection.failed', {
            'inspection_record_id': 9, 'asset_id': 1, 'work_order_id': 5,
            'failed_items': [{'item': 'vibration'}], 'inspector_id': 7,
        }, event_id),
        InspectionFact,
    ),
])
def test_each_handler_is_idempotent(event_factory, model):
    item = event_factory(f'{model.__name__}-event')
    assert HANDLERS[item.type](item) is True
    assert HANDLERS[item.type](item) is False
    assert model.objects.count() == 1
    assert ProcessedEvent.objects.count() == 1


@pytest.mark.django_db
def test_workorder_lifecycle_events_do_not_regress_status():
    HANDLERS['workorder.created'](event(
        'workorder.created',
        workorder_payload(
            status='open',
            created_at='2025-01-15T09:00:00+00:00',
        ),
        'wo-created-ordering',
    ))
    HANDLERS['workorder.completed'](event(
        'workorder.completed',
        workorder_payload(
            status='completed',
            completed_at='2025-01-15T10:30:00+00:00',
        ),
        'wo-completed-ordering',
    ))
    HANDLERS['workorder.assigned'](event(
        'workorder.assigned',
        workorder_payload(
            status='assigned',
            assigned_at='2025-01-15T09:15:00+00:00',
        ),
        'wo-assigned-ordering',
    ))

    fact = WorkOrderFact.objects.get(work_order_id=5)
    assert fact.status == 'completed'
    assert fact.completed_at.isoformat() == '2025-01-15T10:30:00+00:00'
    assert fact.assigned_at.isoformat() == '2025-01-15T09:15:00+00:00'


@pytest.fixture
def signed_client(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    jwks = jwks_from_public_key(public_pem, 'reports-test')
    monkeypatch.setenv('JWKS_URL', 'https://identity.test/jwks')
    monkeypatch.setattr(
        'cmms_common.auth.jwks.fetch_jwks',
        lambda url: jwks,
    )
    from cmms_common.auth.jwks import JWKSAuthentication
    JWKSAuthentication._cache.clear()
    token = jwt.encode(
        {
            'sub': '7',
            'username': 'tech',
            'role': 'engineer',
            'full_name': 'Tech',
        },
        private_pem,
        algorithm='RS256',
        headers={'kid': 'reports-test'},
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


@pytest.mark.django_db
def test_event_flow_populates_all_reports_and_run(signed_client):
    bus = get_event_bus()
    bus.subscribe(list(HANDLERS), dispatch_event, 'reports-test')
    events = [
        asset_event(),
        event(
            'workorder.created',
            workorder_payload(
                status='open',
                created_at='2025-01-15T09:00:00+00:00',
            ),
            'wo-created',
        ),
        event(
            'workorder.assigned',
            workorder_payload(status='assigned', assigned_at='2025-01-15T09:15:00+00:00'),
            'wo-assigned',
        ),
        event(
            'workorder.completed',
            workorder_payload(
                status='completed',
                completed_at='2025-01-15T10:30:00+00:00',
            ),
            'wo-completed',
        ),
        event('part.consumed', {
            'transaction_id': 8, 'part_id': 2, 'part_code': 'P-2',
            'quantity': '2.00', 'unit_cost': '10.00', 'work_order_id': 5,
            'actor_id': 7,
        }, 'part-consumed'),
        event('inspection.failed', {
            'inspection_record_id': 9, 'asset_id': 1, 'work_order_id': 5,
            'failed_items': [{'item': 'vibration'}], 'inspector_id': 7,
        }, 'inspection-failed'),
    ]
    for item in events:
        assert bus.publish(item) is True

    workorders = signed_client.get('/api/reports/workorders/')
    assert workorders.status_code == 200
    assert workorders.data['total'] == 1
    assert workorders.data['completed'] == 1
    assert workorders.data['total_cost'] == '123.45'
    assert len(workorders.data['items']) == 1

    downtime = signed_client.get('/api/reports/downtime/')
    assert downtime.status_code == 200
    assert downtime.data['total_downtime_minutes'] == 120
    assert downtime.data['by_asset'][0]['asset_id'] == 1

    usage = signed_client.get('/api/reports/spareparts-usage/')
    assert usage.status_code == 200
    assert usage.data['total_quantity'] == '2.00'
    assert usage.data['total_cost'] == '20.00'

    for slug in (
        'maintenance-compliance',
        'cost-analysis',
        'technician-performance',
        'equipment-availability',
    ):
        response = signed_client.get(f'/api/reports/{slug}/')
        assert response.status_code == 200
        assert isinstance(response.data, dict)

    run = signed_client.get('/api/reports/run/?type=maintenance-compliance')
    assert run.status_code == 200
    assert 'compliance_rate' in run.data
    assert ReportRun.objects.get().status == 'completed'


@pytest.mark.django_db
def test_scheduled_report_create_sets_remote_user(signed_client):
    response = signed_client.post('/api/reports/scheduled/', {
        'name': 'Weekly summary',
        'report_type': 'workorder_summary',
        'frequency': 'weekly',
        'parameters': {},
        'recipients': [],
    }, format='json')
    assert response.status_code == 201
    assert response.data['created_by_id'] == 7
    assert response.data['created_by_name'] == 'Tech'


@pytest.mark.django_db
def test_import_from_monolith_is_idempotent(tmp_path, django_db_blocker):
    source_path = tmp_path / 'monolith.sqlite3'
    source_db = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': source_path,
        'TIME_ZONE': None,
        'CONN_MAX_AGE': 0,
        'CONN_HEALTH_CHECKS': False,
        'OPTIONS': {},
        'AUTOCOMMIT': True,
        'ATOMIC_REQUESTS': False,
        'TEST': {},
    }
    with django_db_blocker.unblock():
        with override_settings(DATABASES={**settings.DATABASES, 'monolith': source_db}):
            connections.databases['monolith'] = source_db
            connection = connections['monolith']
            with connection.cursor() as cursor:
                cursor.execute(
                    'CREATE TABLE assets (id INTEGER PRIMARY KEY, code VARCHAR(50), '
                    'name VARCHAR(200), process VARCHAR(100), status VARCHAR(30), '
                    'created_at DATETIME, updated_at DATETIME)'
                )
                cursor.execute(
                    'CREATE TABLE work_orders (id INTEGER PRIMARY KEY, '
                    'wo_code VARCHAR(50), equipment_id INTEGER, wo_type VARCHAR(20), '
                    'status VARCHAR(20), priority VARCHAR(20), summary VARCHAR(200), '
                    'created_at DATETIME, updated_at DATETIME)'
                )
                cursor.execute(
                    "INSERT INTO assets VALUES (1, 'A-1', 'Press', 'Stamping', "
                    "'active', '2025-01-15T09:00:00+00:00', '2025-01-15T09:00:00+00:00')"
                )
                cursor.execute(
                    "INSERT INTO work_orders VALUES (5, 'WO-5', 1, 'CM', 'completed', "
                    "'high', 'Repair press', '2025-01-15T09:00:00+00:00', "
                    "'2025-01-15T10:00:00+00:00')"
                )
            call_command('import_from_monolith')
            call_command('import_from_monolith')
            assert AssetProjection.objects.count() == 1
            assert WorkOrderFact.objects.count() == 1
            connection.close()
