import pytest
from django.core.management import call_command
from django.db import connections

from inventory.models import PartTransaction, PurchaseRequest, SparePart


@pytest.mark.django_db(databases=['default', 'monolith'])
def test_import_from_monolith_is_idempotent():
    with connections['monolith'].cursor() as cursor:
        cursor.execute('DROP TABLE IF EXISTS part_transactions')
        cursor.execute('DROP TABLE IF EXISTS purchase_requests')
        cursor.execute('DROP TABLE IF EXISTS spare_parts')
        cursor.execute('CREATE TABLE IF NOT EXISTS users (id integer primary key, full_name text)')
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS spare_parts ('
            'id integer primary key, part_code varchar(50), name varchar(200), description text, '
            'spec varchar(200), category varchar(50), unit varchar(20), manufacturer varchar(100), '
            'supplier varchar(100), supplier_part_code varchar(50), current_stock decimal, '
            'safety_stock decimal, min_stock decimal, max_stock decimal, reorder_quantity decimal, '
            'location varchar(100), shelf varchar(50), unit_cost decimal, average_cost decimal, '
            'compatible_equipment text, alternative_parts text, lead_time_days integer, '
            'lifecycle_status varchar(20), notes text, created_by_id integer, created_at datetime, '
            'updated_at datetime, UNIQUE(part_code))'
        )
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS part_transactions ('
            'id integer primary key, part_id integer, transaction_type varchar(20), quantity decimal, '
            'stock_before decimal, stock_after decimal, related_work_order_id integer, '
            'reference varchar(100), operator_id integer, remark text, created_at datetime)'
        )
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS purchase_requests ('
            'id integer primary key, pr_code varchar(50), part_id integer, quantity decimal, '
            'urgency varchar(20), status varchar(20), reason text, requested_by_id integer, '
            'approved_by_id integer, approved_at datetime, expected_delivery_date date, '
            'actual_delivery_date date, notes text, created_at datetime, updated_at datetime, '
            'UNIQUE(pr_code))'
        )
        cursor.execute('INSERT OR REPLACE INTO users VALUES (7, ?)', ['Importer'])
        cursor.execute(
            'INSERT OR REPLACE INTO spare_parts '
            '(id, part_code, name, unit, current_stock, safety_stock, min_stock, '
            'compatible_equipment, alternative_parts, lifecycle_status, created_by_id) '
            'VALUES (101, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            ['SRC-1', 'Source Part', 'pcs', 3, 1, 1, '["pump"]', '["ALT-1"]', 'active', 7],
        )
        cursor.execute(
            'INSERT OR REPLACE INTO part_transactions '
            '(id, part_id, transaction_type, quantity, stock_before, stock_after, '
            'related_work_order_id, operator_id) VALUES (201, ?, ?, ?, ?, ?, ?, ?)',
            [101, 'in', 2, 1, 3, 42, 7],
        )
        cursor.execute(
            'INSERT OR REPLACE INTO purchase_requests '
            '(id, pr_code, part_id, quantity, requested_by_id) VALUES (301, ?, ?, ?, ?)',
            ['PR-1', 101, 2, 7],
        )

    call_command('import_from_monolith')
    assert SparePart.objects.filter(pk=101).count() == 1
    assert PartTransaction.objects.filter(pk=201).count() == 1
    assert PurchaseRequest.objects.filter(pk=301).count() == 1
    assert SparePart.objects.get(pk=101).created_by_name == 'Importer'
    assert PartTransaction.objects.get(pk=201).operator_name == 'Importer'

    with connections['monolith'].cursor() as cursor:
        cursor.execute('UPDATE spare_parts SET name = ? WHERE id = 101', ['Updated Part'])
    call_command('import_from_monolith')
    assert SparePart.objects.filter(pk=101).count() == 1
    assert SparePart.objects.get(pk=101).name == 'Updated Part'
