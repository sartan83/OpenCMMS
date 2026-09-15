"""
Import work orders, comments and parts from the monolith database.

Reads through the `monolith` database alias (configured from
SOURCE_DATABASE_URL) with raw SQL, preserves primary keys and maps foreign
keys onto the service's soft-reference columns. Safe to re-run.
"""
import json
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction

from workorders_api.models import AssetProjection, WorkOrder, WorkOrderComment, WorkOrderPart

ASSET_SQL = """
SELECT id, code, name, status, process, factory, workshop, line, station
FROM assets
"""

WORK_ORDER_SQL = """
SELECT wo.id, wo.wo_code, wo.equipment_id, a.code, a.name,
       wo.wo_type, wo.status, wo.summary, wo.description, wo.priority,
       wo.requested_by_id, rq.full_name, rq.username,
       wo.assignee_id, asg.full_name, asg.username,
       wo.assigned_at, wo.assigned_by_id, wo.maintenance_plan_id,
       wo.planned_start, wo.planned_end, wo.actual_start, wo.actual_end,
       wo.failure_code, wo.root_cause, wo.actions_taken, wo.checklist,
       wo.downtime_minutes, wo.labor_hours, wo.parts_cost, wo.total_cost,
       wo.completed_by_id, wo.completed_at, wo.closed_by_id, wo.closed_at,
       wo.attachments, wo.notes, wo.created_at, wo.updated_at
FROM work_orders wo
LEFT JOIN assets a ON a.id = wo.equipment_id
LEFT JOIN users rq ON rq.id = wo.requested_by_id
LEFT JOIN users asg ON asg.id = wo.assignee_id
ORDER BY wo.id
"""

COMMENT_SQL = """
SELECT c.id, c.work_order_id, c.author_id, u.full_name, u.username,
       c.comment, c.is_internal, c.created_at
FROM work_order_comments c
LEFT JOIN users u ON u.id = c.author_id
ORDER BY c.id
"""

PART_SQL = """
SELECT id, work_order_id, part_code, part_name, quantity, unit, unit_cost, total_cost
FROM work_order_parts
ORDER BY id
"""


def _decimal(value, default='0'):
    return Decimal(str(value)) if value not in (None, '') else Decimal(default)


def _display_name(full_name, username):
    return full_name or username or ''


def _json(value, default):
    if value is None:
        return default
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return default
    return value


class Command(BaseCommand):
    help = 'Import work orders from the monolith database into the service database'

    def add_arguments(self, parser):
        parser.add_argument('--source', default='monolith', help='Database alias to read from')

    def handle(self, *args, **options):
        source = options['source']
        if source not in connections:
            raise CommandError(
                f"Database alias '{source}' is not configured; set SOURCE_DATABASE_URL"
            )
        counts = {'assets': 0, 'work_orders': 0, 'comments': 0, 'parts': 0}
        with connections[source].cursor() as cursor:
            cursor.execute(ASSET_SQL)
            assets = cursor.fetchall()
            cursor.execute(WORK_ORDER_SQL)
            work_orders = cursor.fetchall()
            cursor.execute(COMMENT_SQL)
            comments = cursor.fetchall()
            cursor.execute(PART_SQL)
            parts = cursor.fetchall()

        with transaction.atomic():
            for row in assets:
                (asset_id, code, name, status, process, factory, workshop, line, station) = row
                AssetProjection.objects.update_or_create(
                    asset_id=asset_id,
                    defaults={
                        'code': code or '', 'name': name or '', 'status': status or '',
                        'process': process or '', 'factory': factory or '',
                        'workshop': workshop or '', 'line': line or '', 'station': station or '',
                    },
                )
                counts['assets'] += 1

            for row in work_orders:
                (wo_id, wo_code, equipment_id, asset_code, asset_name,
                 wo_type, status, summary, description, priority,
                 requested_by_id, requester_full_name, requester_username,
                 assignee_id, assignee_full_name, assignee_username,
                 assigned_at, assigned_by_id, maintenance_plan_id,
                 planned_start, planned_end, actual_start, actual_end,
                 failure_code, root_cause, actions_taken, checklist,
                 downtime_minutes, labor_hours, parts_cost, total_cost,
                 completed_by_id, completed_at, closed_by_id, closed_at,
                 attachments, notes, created_at, updated_at) = row
                defaults = {
                    'wo_code': wo_code,
                    'equipment': equipment_id,
                    'equipment_code': asset_code or '',
                    'equipment_name': asset_name or '',
                    'wo_type': wo_type,
                    'status': status,
                    'summary': summary,
                    'description': description,
                    'priority': priority,
                    'requested_by_id': requested_by_id,
                    'requested_by_name': _display_name(requester_full_name, requester_username),
                    'assignee_id': assignee_id,
                    'assignee_name': _display_name(assignee_full_name, assignee_username),
                    'assigned_at': assigned_at,
                    'assigned_by_id': assigned_by_id,
                    'maintenance_plan_id': maintenance_plan_id,
                    'planned_start': planned_start,
                    'planned_end': planned_end,
                    'actual_start': actual_start,
                    'actual_end': actual_end,
                    'failure_code': failure_code,
                    'root_cause': root_cause,
                    'actions_taken': actions_taken,
                    'checklist': _json(checklist, []),
                    'downtime_minutes': downtime_minutes or 0,
                    'labor_hours': _decimal(labor_hours),
                    'parts_cost': _decimal(parts_cost),
                    'total_cost': total_cost or 0,
                    'completed_by_id': completed_by_id,
                    'completed_at': completed_at,
                    'closed_by_id': closed_by_id,
                    'closed_at': closed_at,
                    'attachments': _json(attachments, []),
                    'notes': notes,
                }
                WorkOrder.objects.update_or_create(id=wo_id, defaults=defaults)
                WorkOrder.objects.filter(id=wo_id).update(created_at=created_at, updated_at=updated_at)
                counts['work_orders'] += 1

            for row in comments:
                (comment_id, work_order_id, author_id, full_name, username,
                 comment, is_internal, created_at) = row
                WorkOrderComment.objects.update_or_create(
                    id=comment_id,
                    defaults={
                        'work_order_id': work_order_id,
                        'author_id': author_id,
                        'author_name': _display_name(full_name, username),
                        'comment': comment,
                        'is_internal': bool(is_internal),
                    },
                )
                WorkOrderComment.objects.filter(id=comment_id).update(created_at=created_at)
                counts['comments'] += 1

            for row in parts:
                (part_id, work_order_id, part_code, part_name, quantity, unit, unit_cost, total_cost) = row
                WorkOrderPart.objects.update_or_create(
                    id=part_id,
                    defaults={
                        'work_order_id': work_order_id,
                        'part_code': part_code,
                        'part_name': part_name,
                        'quantity': _decimal(quantity, '1'),
                        'unit': unit,
                        'unit_cost': _decimal(unit_cost),
                    },
                )
                counts['parts'] += 1

        self.stdout.write(
            'Imported {assets} assets, {work_orders} work orders, '
            '{comments} comments, {parts} parts'.format(**counts)
        )
