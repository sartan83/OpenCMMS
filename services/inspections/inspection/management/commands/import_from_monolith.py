import json

from django.core.management.base import BaseCommand
from django.db import connections

from inspection.models import (
    AssetProjection,
    InspectionRecord,
    InspectionRoute,
    InspectionTemplate,
)


def _value(value):
    return '' if value is None else value


class Command(BaseCommand):
    help = 'Import inspections data from the monolith database'

    def handle(self, *args, **options):
        counts = {'assets': 0, 'records': 0, 'templates': 0, 'routes': 0}
        with connections['monolith'].cursor() as cursor:
            cursor.execute(
                'SELECT id, code, name, status, process, factory, workshop, line, station '
                'FROM assets'
            )
            for row in cursor.fetchall():
                (
                    asset_id, code, name, status, process, factory,
                    workshop, line, station,
                ) = row
                AssetProjection.objects.update_or_create(
                    asset_id=asset_id,
                    defaults={
                        'code': _value(code),
                        'name': _value(name),
                        'status': _value(status),
                        'process': _value(process),
                        'factory': _value(factory),
                        'workshop': _value(workshop),
                        'line': _value(line),
                        'station': _value(station),
                    },
                )
                counts['assets'] += 1

            cursor.execute(
                'SELECT r.id, r.equipment_id, a.code, a.name, r.route, r.items, '
                'r.inspector_id, u.full_name, r.result, r.triggered_work_order_id, '
                'r.notes, r.created_at '
                'FROM inspection_records r '
                'LEFT JOIN assets a ON a.id = r.equipment_id '
                'LEFT JOIN users u ON u.id = r.inspector_id'
            )
            for row in cursor.fetchall():
                (
                    record_id, equipment, equipment_code, equipment_name, route,
                    items, inspector_id, inspector_name, result,
                    triggered_work_order_id, notes, created_at,
                ) = row
                if isinstance(items, str):
                    items = json.loads(items)
                values = {
                    'equipment': equipment,
                    'equipment_code': _value(equipment_code),
                    'equipment_name': _value(equipment_name),
                    'route': route,
                    'items': items,
                    'inspector_id': inspector_id,
                    'inspector_name': _value(inspector_name),
                    'result': result,
                    'triggered_work_order_id': triggered_work_order_id,
                    'notes': notes,
                    'created_at': created_at,
                }
                if InspectionRecord.objects.filter(id=record_id).update(**values) == 0:
                    InspectionRecord.objects.bulk_create([
                        InspectionRecord(id=record_id, **values)
                    ])
                    InspectionRecord.objects.filter(id=record_id).update(
                        created_at=created_at
                    )
                counts['records'] += 1

            cursor.execute(
                'SELECT id, code, name, description, items_template, equipment_type, '
                'frequency_days, is_active, created_at, updated_at '
                'FROM inspection_templates'
            )
            for row in cursor.fetchall():
                (
                    template_id, code, name, description, items_template,
                    equipment_type, frequency_days, is_active, created_at, updated_at,
                ) = row
                if isinstance(items_template, str):
                    items_template = json.loads(items_template)
                InspectionTemplate.objects.update_or_create(
                    id=template_id,
                    defaults={
                        'code': code,
                        'name': name,
                        'description': description,
                        'items_template': items_template,
                        'equipment_type': equipment_type,
                        'frequency_days': frequency_days,
                        'is_active': is_active,
                        'created_at': created_at,
                        'updated_at': updated_at,
                    },
                )
                InspectionTemplate.objects.filter(id=template_id).update(
                    created_at=created_at,
                    updated_at=updated_at,
                )
                counts['templates'] += 1

            cursor.execute(
                'SELECT r.id, r.code, r.name, r.description, r.route_items, '
                'r.estimated_duration_minutes, r.inspector_id, u.full_name, '
                'r.is_active, r.created_at, r.updated_at '
                'FROM inspection_routes r '
                'LEFT JOIN users u ON u.id = r.inspector_id'
            )
            for row in cursor.fetchall():
                (
                    route_id, code, name, description, route_items,
                    estimated_duration_minutes, inspector_id, inspector_name,
                    is_active, created_at, updated_at,
                ) = row
                if isinstance(route_items, str):
                    route_items = json.loads(route_items)
                InspectionRoute.objects.update_or_create(
                    id=route_id,
                    defaults={
                        'code': code,
                        'name': name,
                        'description': description,
                        'route_items': route_items,
                        'estimated_duration_minutes': estimated_duration_minutes,
                        'inspector_id': inspector_id,
                        'inspector_name': _value(inspector_name),
                        'is_active': is_active,
                        'created_at': created_at,
                        'updated_at': updated_at,
                    },
                )
                InspectionRoute.objects.filter(id=route_id).update(
                    created_at=created_at,
                    updated_at=updated_at,
                )
                counts['routes'] += 1

        self.stdout.write(
            self.style.SUCCESS(
                'Imported '
                + ', '.join(f'{name}={count}' for name, count in counts.items())
            )
        )
