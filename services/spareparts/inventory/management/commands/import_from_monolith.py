import json

from django.core.management.base import BaseCommand
from django.db import connections, transaction

from inventory.models import PartTransaction, PurchaseRequest, SparePart


def _rows(cursor):
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _json_value(value):
    if isinstance(value, str):
        return json.loads(value)
    return value


class Command(BaseCommand):
    help = 'Import spare parts data from the monolith database'

    def handle(self, *args, **options):
        with connections['monolith'].cursor() as cursor:
            cursor.execute(
                'SELECT sp.*, u.full_name AS created_by_name '
                'FROM spare_parts sp LEFT JOIN users u ON u.id = sp.created_by_id'
            )
            parts = _rows(cursor)
            cursor.execute(
                'SELECT pt.*, u.full_name AS operator_name '
                'FROM part_transactions pt LEFT JOIN users u ON u.id = pt.operator_id'
            )
            transactions = _rows(cursor)
            cursor.execute(
                'SELECT pr.*, ru.full_name AS requested_by_name, '
                'au.full_name AS approved_by_name '
                'FROM purchase_requests pr '
                'LEFT JOIN users ru ON ru.id = pr.requested_by_id '
                'LEFT JOIN users au ON au.id = pr.approved_by_id'
            )
            purchase_requests = _rows(cursor)

        with transaction.atomic():
            for row in parts:
                row_id = row.pop('id')
                created_by_name = row.pop('created_by_name', None)
                defaults = {
                    key: row.get(key)
                    for key in (
                        'part_code', 'name', 'description', 'spec', 'category', 'unit',
                        'manufacturer', 'supplier', 'supplier_part_code', 'current_stock',
                        'safety_stock', 'min_stock', 'max_stock', 'reorder_quantity',
                        'location', 'shelf', 'unit_cost', 'average_cost', 'lead_time_days',
                        'lifecycle_status', 'notes', 'created_by_id', 'created_at', 'updated_at',
                    )
                    if key in row
                }
                defaults['compatible_equipment'] = _json_value(row.get('compatible_equipment', []))
                defaults['alternative_parts'] = _json_value(row.get('alternative_parts', []))
                defaults['created_by_name'] = created_by_name or ''
                for timestamp in ('created_at', 'updated_at'):
                    if defaults.get(timestamp) is None:
                        defaults.pop(timestamp, None)
                SparePart.objects.update_or_create(id=row_id, defaults=defaults)

            for row in transactions:
                row_id = row.pop('id')
                operator_name = row.pop('operator_name', None)
                defaults = {
                    key: row.get(key)
                    for key in (
                        'part_id', 'transaction_type', 'quantity', 'stock_before',
                        'stock_after', 'reference', 'remark', 'operator_id', 'created_at',
                    )
                    if key in row
                }
                defaults['related_work_order'] = row.get(
                    'related_work_order_id', row.get('related_work_order')
                )
                defaults['operator_name'] = operator_name or ''
                if defaults.get('created_at') is None:
                    defaults.pop('created_at', None)
                PartTransaction.objects.update_or_create(id=row_id, defaults=defaults)

            for row in purchase_requests:
                row_id = row.pop('id')
                requested_by_name = row.pop('requested_by_name', None)
                approved_by_name = row.pop('approved_by_name', None)
                defaults = {
                    key: row.get(key)
                    for key in (
                        'pr_code', 'part_id', 'quantity', 'urgency', 'status', 'reason',
                        'requested_by_id', 'approved_by_id', 'approved_at',
                        'expected_delivery_date', 'actual_delivery_date', 'notes',
                        'created_at', 'updated_at',
                    )
                    if key in row
                }
                defaults['urgency'] = row.get('urgency') or 'medium'
                defaults['status'] = row.get('status') or 'draft'
                defaults['requested_by_name'] = requested_by_name or ''
                defaults['approved_by_name'] = approved_by_name or ''
                for timestamp in ('created_at', 'updated_at'):
                    if defaults.get(timestamp) is None:
                        defaults.pop(timestamp, None)
                PurchaseRequest.objects.update_or_create(id=row_id, defaults=defaults)

        self.stdout.write(
            self.style.SUCCESS(
                f'Imported {len(parts)} spare parts, {len(transactions)} transactions, '
                f'{len(purchase_requests)} purchase requests.'
            )
        )
