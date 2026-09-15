import json

from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from pm.models import AssetProjection, MaintenancePlan, WorkOrderTemplate


def _rows(cursor, sql):
    cursor.execute(sql)
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _json_value(value):
    if isinstance(value, str):
        return json.loads(value)
    return value


class Command(BaseCommand):
    help = 'Import maintenance data from the monolith database'

    def handle(self, *args, **options):
        if 'monolith' not in connections.databases:
            raise CommandError('The monolith database alias is not configured')

        plan_count = asset_count = template_count = 0
        with connections['monolith'].cursor() as cursor:
            plans = _rows(cursor, """
                SELECT p.id, p.code, p.equipment_id, p.title, p.description, p.trigger_type,
                       p.frequency_value, p.frequency_unit, p.counter_name,
                       p.counter_threshold, p.checklist_template,
                       p.estimated_hours, p.estimated_cost, p.required_skills,
                       p.priority, p.is_active, p.last_generated_date,
                       p.last_counter_value, p.created_by_id, p.created_at,
                       p.updated_at, a.code AS equipment_code,
                       a.name AS equipment_name, u.full_name AS created_by_name
                FROM maintenance_plans p
                LEFT JOIN assets a ON a.id = p.equipment_id
                LEFT JOIN users u ON u.id = p.created_by_id
            """)
            for row in plans:
                MaintenancePlan.objects.update_or_create(
                    id=row['id'],
                    defaults={
                        'code': row['code'],
                        'equipment_id': row.get('equipment_id'),
                        'equipment_code': row['equipment_code'] or '',
                        'equipment_name': row['equipment_name'] or '',
                        'title': row['title'],
                        'description': row['description'],
                        'trigger_type': row['trigger_type'],
                        'frequency_value': row['frequency_value'],
                        'frequency_unit': row['frequency_unit'],
                        'counter_name': row['counter_name'],
                        'counter_threshold': row['counter_threshold'],
                        'checklist_template': _json_value(row['checklist_template']),
                        'estimated_hours': row['estimated_hours'],
                        'estimated_cost': row['estimated_cost'],
                        'required_skills': row['required_skills'],
                        'priority': row['priority'],
                        'is_active': row['is_active'],
                        'last_generated_date': row['last_generated_date'],
                        'last_counter_value': row['last_counter_value'],
                        'created_by_id': row['created_by_id'],
                        'created_by_name': row['created_by_name'] or '',
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at'],
                    },
                )
                plan_count += 1

            assets = _rows(cursor, """
                SELECT id AS asset_id, code, name, status, process, factory,
                       workshop, line, station
                FROM assets
            """)
            for row in assets:
                AssetProjection.objects.update_or_create(
                    asset_id=row['asset_id'],
                    defaults={
                        key: row[key] or ''
                        for key in (
                            'code', 'name', 'status', 'process', 'factory',
                            'workshop', 'line', 'station',
                        )
                    },
                )
                asset_count += 1

            templates = _rows(cursor, """
                SELECT id, code, name, description, work_order_type,
                       checklist_template, estimated_hours, required_skills,
                       is_active, created_at, updated_at
                FROM work_order_templates
            """)
            for row in templates:
                WorkOrderTemplate.objects.update_or_create(
                    id=row['id'],
                    defaults={
                        'code': row['code'],
                        'name': row['name'],
                        'description': row['description'],
                        'work_order_type': row['work_order_type'],
                        'checklist_template': _json_value(row['checklist_template']),
                        'estimated_hours': row['estimated_hours'],
                        'required_skills': row['required_skills'],
                        'is_active': row['is_active'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at'],
                    },
                )
                template_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Imported {plan_count} plans, {asset_count} assets, '
                f'{template_count} templates.'
            )
        )
