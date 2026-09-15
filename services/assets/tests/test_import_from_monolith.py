from datetime import date, datetime, timezone

import pytest
from django.core.management import call_command
from django.db import connections

from assetregistry.models import Asset

MONOLITH_SCHEMA = [
    '''CREATE TABLE users (
        id integer PRIMARY KEY,
        username varchar(150) NOT NULL,
        full_name varchar(150) NOT NULL
    )''',
    '''CREATE TABLE assets (
        id integer PRIMARY KEY,
        code varchar(50) NOT NULL UNIQUE,
        name varchar(200) NOT NULL,
        process varchar(100), equipment_id varchar(50), machine_name varchar(100),
        location_path varchar(255), factory varchar(50), workshop varchar(50),
        line varchar(50), station varchar(50), vendor varchar(100), model varchar(100),
        serial_number varchar(100), specification text, start_date date,
        warranty_expiry date, status varchar(20) NOT NULL, parent_id integer,
        criticality varchar(20) NOT NULL, cost_center varchar(50),
        asset_value decimal, expected_life_years integer,
        current_meter_reading decimal NOT NULL, meter_unit varchar(20),
        last_maintenance_date date, next_maintenance_date date, notes text,
        created_by_id integer NOT NULL,
        created_at datetime NOT NULL, updated_at datetime NOT NULL
    )''',
]

ASSET_INSERT = '''INSERT INTO assets (
    id, code, name, process, factory, status, parent_id, criticality,
    current_meter_reading, created_by_id, created_at, updated_at, start_date
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''


@pytest.fixture
def monolith_db():
    with connections['monolith'].cursor() as cursor:
        for statement in MONOLITH_SCHEMA:
            cursor.execute(statement)
        cursor.execute("INSERT INTO users (id, username, full_name) VALUES (1, 'admin', 'Site Admin')")
        cursor.execute("INSERT INTO users (id, username, full_name) VALUES (2, 'tech', '')")
        created = '2023-05-01 10:00:00'
        cursor.execute(ASSET_INSERT, [10, 'ROOT', 'Root line', 'Assembly', 'F1', 'active', None,
                                      'critical', 0, 1, created, created, '2020-02-03'])
        cursor.execute(ASSET_INSERT, [11, 'CHILD', 'Robot', None, 'F1', 'inactive', 10,
                                      'normal', 12.5, 2, created, created, None])
        cursor.execute(ASSET_INSERT, [12, 'ORPHAN', 'Legacy', None, None, 'retired', None,
                                      'normal', 0, 99, created, created, None])
    yield
    with connections['monolith'].cursor() as cursor:
        cursor.execute('DROP TABLE assets')
        cursor.execute('DROP TABLE users')


@pytest.mark.django_db(databases=['default', 'monolith'])
def test_import_from_monolith_is_idempotent(monolith_db):
    call_command('import_from_monolith', alias='monolith')
    assert Asset.objects.count() == 3

    root = Asset.objects.get(id=10)
    assert root.code == 'ROOT'
    assert root.created_by_id == 1
    assert root.created_by_name == 'Site Admin'
    assert root.start_date == date(2020, 2, 3)
    assert root.created_at == datetime(2023, 5, 1, 10, 0, tzinfo=timezone.utc)

    child = Asset.objects.get(id=11)
    assert child.parent_id == 10
    assert child.created_by_name == 'tech'
    assert float(child.current_meter_reading) == 12.5

    orphan = Asset.objects.get(id=12)
    assert orphan.created_by_id == 99
    assert orphan.created_by_name == ''

    with connections['monolith'].cursor() as cursor:
        cursor.execute("UPDATE assets SET name = 'Root line v2' WHERE id = 10")
    call_command('import_from_monolith', alias='monolith')
    assert Asset.objects.count() == 3
    assert Asset.objects.get(id=10).name == 'Root line v2'


def test_import_requires_configured_alias():
    from django.core.management.base import CommandError

    with pytest.raises(CommandError):
        call_command('import_from_monolith', alias='missing')
