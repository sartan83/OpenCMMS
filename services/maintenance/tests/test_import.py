import json

import pytest
from django.core.management import call_command
from django.db import connections

from pm.models import AssetProjection, MaintenancePlan, WorkOrderTemplate


@pytest.mark.django_db(databases=['default', 'monolith'])
def test_import_from_monolith_is_idempotent():
    with connections['monolith'].cursor() as cursor:
        for table in ('assets', 'users', 'maintenance_plans', 'work_order_templates'):
            cursor.execute(f'DROP TABLE IF EXISTS {table}')
        cursor.execute('CREATE TABLE assets (id INTEGER PRIMARY KEY, code VARCHAR(50), name VARCHAR(200), status VARCHAR(20), process VARCHAR(100), factory VARCHAR(100), workshop VARCHAR(100), line VARCHAR(100), station VARCHAR(100))')
        cursor.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR(150), full_name VARCHAR(150))')
        cursor.execute('CREATE TABLE maintenance_plans (id INTEGER PRIMARY KEY, code VARCHAR(50), equipment_id INTEGER, title VARCHAR(200), description TEXT, trigger_type VARCHAR(20), frequency_value INTEGER, frequency_unit VARCHAR(20), counter_name VARCHAR(50), counter_threshold DECIMAL, checklist_template TEXT, estimated_hours DECIMAL, estimated_cost DECIMAL, required_skills VARCHAR(200), priority VARCHAR(20), is_active BOOLEAN, last_generated_date DATE, last_counter_value DECIMAL, created_by_id INTEGER, created_at DATETIME, updated_at DATETIME)')
        cursor.execute('CREATE TABLE work_order_templates (id INTEGER PRIMARY KEY, code VARCHAR(50), name VARCHAR(200), description TEXT, work_order_type VARCHAR(20), checklist_template TEXT, estimated_hours DECIMAL, required_skills VARCHAR(200), is_active BOOLEAN, created_at DATETIME, updated_at DATETIME)')
        cursor.execute("INSERT INTO assets VALUES (10, 'EQ-IMPORT', 'Imported Press', 'active', '', '', '', '', '')")
        cursor.execute("INSERT INTO users VALUES (1, 'admin', 'Imported User')")
        cursor.execute("INSERT INTO maintenance_plans VALUES (7, 'PM-IMPORT', 10, 'Imported', '', 'time', 1, 'day', NULL, NULL, ?, NULL, NULL, '', 'medium', 1, NULL, NULL, 1, '2024-01-01 00:00:00', '2024-01-01 00:00:00')", [json.dumps([])])
        cursor.execute("INSERT INTO work_order_templates VALUES (8, 'TPL-IMPORT', 'Imported Template', '', 'PM', ?, NULL, '', 1, '2024-01-01 00:00:00', '2024-01-01 00:00:00')", [json.dumps([])])
    call_command('import_from_monolith')
    assert MaintenancePlan.objects.get(pk=7).equipment_code == 'EQ-IMPORT'
    assert MaintenancePlan.objects.get(pk=7).created_by_name == 'Imported User'
    assert AssetProjection.objects.filter(pk=10).count() == 1
    assert WorkOrderTemplate.objects.filter(pk=8).count() == 1
    call_command('import_from_monolith')
    assert MaintenancePlan.objects.count() == 1
    assert AssetProjection.objects.count() == 1
    assert WorkOrderTemplate.objects.count() == 1
