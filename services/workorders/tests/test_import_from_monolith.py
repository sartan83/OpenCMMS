import pytest
from django.core.management import CommandError, call_command
from django.db import connections

from workorders_api.models import AssetProjection, WorkOrder, WorkOrderComment, WorkOrderPart

pytestmark = pytest.mark.django_db(databases=['default', 'monolith'])

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY, code TEXT, name TEXT, status TEXT,
        process TEXT, factory TEXT, workshop TEXT, line TEXT, station TEXT)""",
    "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, full_name TEXT)",
    """CREATE TABLE IF NOT EXISTS work_orders (
        id INTEGER PRIMARY KEY, wo_code TEXT, equipment_id INTEGER, wo_type TEXT, status TEXT,
        summary TEXT, description TEXT, priority TEXT, requested_by_id INTEGER,
        assignee_id INTEGER, assigned_at TEXT, assigned_by_id INTEGER, maintenance_plan_id INTEGER,
        planned_start TEXT, planned_end TEXT, actual_start TEXT, actual_end TEXT,
        failure_code TEXT, root_cause TEXT, actions_taken TEXT, checklist TEXT,
        downtime_minutes INTEGER, labor_hours TEXT, parts_cost TEXT, total_cost TEXT,
        completed_by_id INTEGER, completed_at TEXT, closed_by_id INTEGER, closed_at TEXT,
        attachments TEXT, notes TEXT, created_at TEXT, updated_at TEXT)""",
    """CREATE TABLE IF NOT EXISTS work_order_comments (
        id INTEGER PRIMARY KEY, work_order_id INTEGER, author_id INTEGER,
        comment TEXT, is_internal INTEGER, created_at TEXT)""",
    """CREATE TABLE IF NOT EXISTS work_order_parts (
        id INTEGER PRIMARY KEY, work_order_id INTEGER, part_code TEXT, part_name TEXT,
        quantity TEXT, unit TEXT, unit_cost TEXT, total_cost TEXT)""",
]


@pytest.fixture
def monolith_data():
    with connections['monolith'].cursor() as cur:
        for stmt in SCHEMA:
            cur.execute(stmt)
        for table in ('assets', 'users', 'work_orders', 'work_order_comments', 'work_order_parts'):
            cur.execute(f'DELETE FROM {table}')
        cur.execute("INSERT INTO assets VALUES (10, 'EQ-010', 'Lathe', 'active', '', 'F1', '', '', '')")
        cur.execute("INSERT INTO users VALUES (1, 'admin', 'Admin User')")
        cur.execute("INSERT INTO users VALUES (2, 'tech', '')")
        cur.execute(
            """INSERT INTO work_orders VALUES (
                500, 'WO-20260101-0001', 10, 'CM', 'assigned', 'Legacy order', 'desc', 'high', 1,
                2, '2026-01-02T10:00:00+00:00', 1, 7,
                '2026-01-03T08:00:00+00:00', NULL, NULL, NULL,
                'F01', '', '', '["a"]',
                15, '1.50', '20.00', '20.00',
                NULL, NULL, NULL, NULL,
                '[]', 'n', '2026-01-01T00:00:00+00:00', '2026-01-02T00:00:00+00:00')"""
        )
        cur.execute("INSERT INTO work_order_comments VALUES (900, 500, 2, 'hi', 0, '2026-01-02T11:00:00+00:00')")
        cur.execute("INSERT INTO work_order_parts VALUES (800, 500, 'P-1', 'Bolt', '4', 'pc', '0.50', '2.00')")


def test_import_preserves_ids_and_maps_soft_refs(monolith_data):
    call_command('import_from_monolith')
    call_command('import_from_monolith')  # idempotent

    assert AssetProjection.objects.get(pk=10).name == 'Lathe'
    wo = WorkOrder.objects.get(pk=500)
    assert WorkOrder.objects.count() == 1
    assert wo.wo_code == 'WO-20260101-0001'
    assert wo.equipment == 10
    assert wo.equipment_code == 'EQ-010'
    assert wo.equipment_name == 'Lathe'
    assert wo.requested_by_id == 1
    assert wo.requested_by_name == 'Admin User'
    assert wo.assignee_id == 2
    assert wo.assignee_name == 'tech'
    assert wo.maintenance_plan_id == 7
    assert wo.checklist == ['a']
    assert str(wo.parts_cost) == '20.00'
    assert wo.status == 'assigned'

    comment = WorkOrderComment.objects.get(pk=900)
    assert comment.work_order_id == 500
    assert comment.author_id == 2
    assert comment.author_name == 'tech'

    part = WorkOrderPart.objects.get(pk=800)
    assert part.work_order_id == 500
    assert str(part.total_cost) == '2.00'


def test_import_requires_configured_alias():
    with pytest.raises(CommandError):
        call_command('import_from_monolith', source='missing')
