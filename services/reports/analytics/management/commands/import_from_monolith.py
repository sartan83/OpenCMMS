import json

from django.core.management.base import BaseCommand
from django.db import connections
from django.utils import timezone

from analytics.models import (
    AssetProjection,
    PartConsumptionFact,
    ReportRun,
    ScheduledReport,
    WorkOrderFact,
)
from analytics.projections import _decimal, _timestamp


def _rows(alias, table, fields):
    connection = connections[alias]
    if table not in connection.introspection.table_names():
        return []
    available = connection.introspection.get_table_description(
        connection.cursor(), table
    )
    names = {
        item.name if hasattr(item, 'name') else item[0]
        for item in available
    }
    selected = [field for field in fields if field in names]
    if not selected:
        return []
    quoted_table = connection.ops.quote_name(table)
    quoted_fields = ', '.join(connection.ops.quote_name(field) for field in selected)
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT {quoted_fields} FROM {quoted_table}')
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _value(row, *names, default=None):
    for name in names:
        if name in row and row[name] is not None:
            return row[name]
    return default


def _json_value(value, default):
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def import_assets(alias):
    count = 0
    for row in _rows(
        alias, 'assets',
        ['id', 'code', 'name', 'process', 'status', 'updated_at', 'created_at'],
    ):
        AssetProjection.objects.update_or_create(
            asset_id=row['id'],
            defaults={
                'asset_code': row.get('code') or str(row['id']),
                'asset_name': row.get('name') or '',
                'category': row.get('process'),
                'status': row.get('status'),
                'updated_at': _timestamp(
                    row.get('updated_at') or row.get('created_at')
                ) or timezone.now(),
            },
        )
        count += 1
    return count


def import_workorders(alias):
    count = 0
    for row in _rows(
        alias, 'work_orders',
        [
            'id', 'wo_code', 'equipment_id', 'wo_type', 'status', 'priority',
            'summary', 'assignee_id', 'maintenance_plan_id', 'created_at',
            'assigned_at', 'completed_at', 'closed_at', 'planned_start',
            'planned_end', 'actual_start', 'actual_end', 'downtime_minutes',
            'labor_hours', 'parts_cost', 'total_cost', 'updated_at',
        ],
    ):
        asset = AssetProjection.objects.filter(asset_id=row['equipment_id']).first()
        WorkOrderFact.objects.update_or_create(
            work_order_id=row['id'],
            defaults={
                'wo_code': row.get('wo_code') or str(row['id']),
                'asset_id': row['equipment_id'],
                'asset_code': asset.asset_code if asset else None,
                'asset_name': asset.asset_name if asset else None,
                'wo_type': row.get('wo_type') or 'CM',
                'status': row.get('status') or 'open',
                'priority': row.get('priority'),
                'title': row.get('summary'),
                'assignee_id': row.get('assignee_id'),
                'maintenance_plan_id': row.get('maintenance_plan_id'),
                'created_at': _timestamp(row.get('created_at')),
                'assigned_at': _timestamp(row.get('assigned_at')),
                'completed_at': _timestamp(row.get('completed_at')),
                'closed_at': _timestamp(row.get('closed_at')),
                'planned_start': _timestamp(row.get('planned_start')),
                'planned_end': _timestamp(row.get('planned_end')),
                'actual_start': _timestamp(row.get('actual_start')),
                'actual_end': _timestamp(row.get('actual_end')),
                'downtime_minutes': row.get('downtime_minutes'),
                'labor_hours': _decimal(row.get('labor_hours')) or 0,
                'parts_cost': _decimal(row.get('parts_cost')) or 0,
                'total_cost': _decimal(row.get('total_cost')) or 0,
                'updated_at': _timestamp(row.get('updated_at')) or timezone.now(),
            },
        )
        count += 1
    return count


def import_parts(alias):
    rows = _rows(
        alias, 'part_transactions',
        [
            'id', 'part_id', 'part_code', 'quantity', 'unit_cost',
            'related_work_order_id', 'operator_id', 'created_at',
            'transaction_type',
        ],
    )
    count = 0
    for row in rows:
        if str(row.get('transaction_type', '')).lower() not in {
            'out', 'stock_out', 'consume', 'consumed',
        }:
            continue
        quantity = _decimal(row.get('quantity')) or 0
        unit_cost = _decimal(row.get('unit_cost'))
        PartConsumptionFact.objects.update_or_create(
            transaction_id=row['id'],
            defaults={
                'part_id': row['part_id'],
                'part_code': row.get('part_code') or str(row['part_id']),
                'quantity': quantity,
                'unit_cost': unit_cost,
                'total_cost': quantity * unit_cost if unit_cost is not None else None,
                'work_order_id': _value(row, 'related_work_order_id', 'work_order_id'),
                'actor_id': _value(row, 'operator_id', 'actor_id', default=0),
                'occurred_at': _timestamp(row.get('created_at')) or timezone.now(),
            },
        )
        count += 1
    return count


def import_scheduled_reports(alias):
    count = 0
    for row in _rows(
        alias, 'scheduled_reports',
        [
            'id', 'name', 'report_type', 'description', 'frequency',
            'parameters', 'recipients', 'status', 'last_run_at', 'next_run_at',
            'created_by_id', 'created_by', 'created_at', 'updated_at',
        ],
    ):
        ScheduledReport.objects.update_or_create(
            id=row['id'],
            defaults={
                'name': row.get('name') or '',
                'report_type': row.get('report_type') or 'workorder_summary',
                'description': row.get('description'),
                'frequency': row.get('frequency') or 'monthly',
                'parameters': _json_value(row.get('parameters'), {}),
                'recipients': _json_value(row.get('recipients'), []),
                'status': row.get('status') or 'active',
                'last_run_at': _timestamp(row.get('last_run_at')),
                'next_run_at': _timestamp(row.get('next_run_at')),
                'created_by_id': _value(row, 'created_by_id', 'created_by', default=0),
                'created_by_name': '',
            },
        )
        count += 1
    return count


def import_runs(alias):
    count = 0
    for row in _rows(
        alias, 'report_runs',
        [
            'id', 'scheduled_report_id', 'report_type', 'parameters', 'status',
            'output_file', 'output_format', 'error_message', 'requested_by_id',
            'requested_by', 'started_at', 'completed_at', 'created_at',
        ],
    ):
        scheduled_id = row.get('scheduled_report_id')
        ReportRun.objects.update_or_create(
            id=row['id'],
            defaults={
                'scheduled_report_id': scheduled_id if scheduled_id and ScheduledReport.objects.filter(id=scheduled_id).exists() else None,
                'report_type': row.get('report_type') or 'workorder_summary',
                'parameters': _json_value(row.get('parameters'), {}),
                'status': row.get('status') or 'completed',
                'output_file': row.get('output_file'),
                'output_format': row.get('output_format'),
                'error_message': row.get('error_message'),
                'requested_by_id': _value(row, 'requested_by_id', 'requested_by'),
                'requested_by_name': '',
                'started_at': _timestamp(row.get('started_at')),
                'completed_at': _timestamp(row.get('completed_at')),
            },
        )
        count += 1
    return count


class Command(BaseCommand):
    help = 'Import reporting data from the legacy monolith database'

    def handle(self, *args, **options):
        alias = 'monolith'
        counts = {
            'assets': import_assets(alias),
            'workorders': import_workorders(alias),
            'parts': import_parts(alias),
            'scheduled_reports': import_scheduled_reports(alias),
            'report_runs': import_runs(alias),
        }
        self.stdout.write(self.style.SUCCESS(f'Imported {counts}'))
