import json

import pytest
from django.core.management import call_command
from django.db import connections

from inspection.models import (
    AssetProjection,
    InspectionRecord,
    InspectionRoute,
    InspectionTemplate,
)


@pytest.mark.django_db(databases=['default', 'monolith'])
def test_import_from_monolith_is_idempotent():
    with connections['monolith'].cursor() as cursor:
        for table in (
            'inspection_routes',
            'inspection_templates',
            'inspection_records',
            'users',
            'assets',
        ):
            cursor.execute(f'DROP TABLE IF EXISTS {table}')
        cursor.execute(
            'CREATE TABLE assets ('
            'id INTEGER PRIMARY KEY, code VARCHAR(100), name VARCHAR(200), '
            'status VARCHAR(50), process VARCHAR(100), factory VARCHAR(100), '
            'workshop VARCHAR(100), line VARCHAR(100), station VARCHAR(100))'
        )
        cursor.execute(
            'CREATE TABLE users (id INTEGER PRIMARY KEY, full_name VARCHAR(150))'
        )
        cursor.execute(
            'CREATE TABLE inspection_records ('
            'id INTEGER PRIMARY KEY, equipment_id INTEGER, route VARCHAR(100), '
            'items TEXT, inspector_id INTEGER, result VARCHAR(20), '
            'triggered_work_order_id INTEGER, notes TEXT, created_at DATETIME)'
        )
        cursor.execute(
            'CREATE TABLE inspection_templates ('
            'id INTEGER PRIMARY KEY, code VARCHAR(50), name VARCHAR(200), '
            'description TEXT, items_template TEXT, equipment_type VARCHAR(50), '
            'frequency_days INTEGER, is_active BOOLEAN, created_at DATETIME, '
            'updated_at DATETIME)'
        )
        cursor.execute(
            'CREATE TABLE inspection_routes ('
            'id INTEGER PRIMARY KEY, code VARCHAR(50), name VARCHAR(200), '
            'description TEXT, route_items TEXT, estimated_duration_minutes INTEGER, '
            'inspector_id INTEGER, is_active BOOLEAN, created_at DATETIME, '
            'updated_at DATETIME)'
        )
        cursor.execute(
            "INSERT INTO assets VALUES (1, 'EQ-IMPORT', 'Imported pump', 'active', "
            "'Process', 'Factory', 'Workshop', 'Line', 'Station')"
        )
        cursor.execute("INSERT INTO users VALUES (7, 'Imported Inspector')")
        cursor.execute(
            "INSERT INTO inspection_records VALUES "
            "(11, 1, 'Route 1', ?, 7, 'pass', NULL, 'note', '2025-01-01 00:00:00')",
            [json.dumps([{'item': 'Temp', 'ok': True}])],
        )
        cursor.execute(
            "INSERT INTO inspection_templates VALUES "
            "(12, 'TMP-IMPORT', 'Imported template', 'description', ?, 'pump', "
            "7, 1, '2025-01-01 00:00:00', '2025-01-01 00:00:00')",
            [json.dumps([])],
        )
        cursor.execute(
            "INSERT INTO inspection_routes VALUES "
            "(13, 'ROUTE-IMPORT', 'Imported route', 'description', ?, 30, 7, 1, "
            "'2025-01-01 00:00:00', '2025-01-01 00:00:00')",
            [json.dumps([])],
        )

    call_command('import_from_monolith')
    call_command('import_from_monolith')

    assert AssetProjection.objects.count() == 1
    assert InspectionRecord.objects.count() == 1
    assert InspectionTemplate.objects.count() == 1
    assert InspectionRoute.objects.count() == 1
    record = InspectionRecord.objects.get(pk=11)
    assert record.equipment_code == 'EQ-IMPORT'
    assert record.inspector_name == 'Imported Inspector'
    assert record.created_at.year == 2025
    template = InspectionTemplate.objects.get(pk=12)
    assert template.code == 'TMP-IMPORT'
    assert template.created_at.year == 2025
    route = InspectionRoute.objects.get(pk=13)
    assert route.inspector_name == 'Imported Inspector'
    assert route.created_at.year == 2025
