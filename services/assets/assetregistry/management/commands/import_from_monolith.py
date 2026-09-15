from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction

from assetregistry.models import Asset

ASSET_COLUMNS = [
    'id', 'code', 'name', 'process', 'equipment_id', 'machine_name',
    'location_path', 'factory', 'workshop', 'line', 'station', 'vendor',
    'model', 'serial_number', 'specification', 'start_date', 'warranty_expiry',
    'status', 'parent_id', 'criticality', 'cost_center', 'asset_value',
    'expected_life_years', 'current_meter_reading', 'meter_unit',
    'last_maintenance_date', 'next_maintenance_date', 'notes', 'created_by_id',
    'created_at', 'updated_at',
]

IMPORT_SQL = (
    'SELECT ' + ', '.join(f'a.{column}' for column in ASSET_COLUMNS)
    + ', COALESCE(NULLIF(u.full_name, \'\'), u.username, \'\') AS created_by_name'
    + ' FROM assets a LEFT JOIN users u ON u.id = a.created_by_id'
    + ' ORDER BY a.id'
)


def import_assets(alias='monolith'):
    """Upsert every monolith asset row into the service table, preserving primary keys."""
    with connections[alias].cursor() as cursor:
        cursor.execute(IMPORT_SQL)
        rows = cursor.fetchall()

    created = updated = 0
    with transaction.atomic():
        for row in rows:
            record = dict(zip(ASSET_COLUMNS + ['created_by_name'], row))
            asset_id = record.pop('id')
            record['created_by_id'] = record['created_by_id'] or 0
            record['created_by_name'] = record['created_by_name'] or ''
            timestamps = {
                'created_at': record.pop('created_at'),
                'updated_at': record.pop('updated_at'),
            }
            _, was_created = Asset.objects.update_or_create(id=asset_id, defaults=record)
            # auto_now(_add) fields ignore assigned values; update() bypasses them
            Asset.objects.filter(id=asset_id).update(**timestamps)
            if was_created:
                created += 1
            else:
                updated += 1
    return created, updated


class Command(BaseCommand):
    help = 'Import assets from the monolith database (requires SOURCE_DATABASE_URL)'

    def add_arguments(self, parser):
        parser.add_argument('--alias', default='monolith')

    def handle(self, *args, **options):
        alias = options['alias']
        if alias not in connections.databases:
            raise CommandError(
                f'Database alias "{alias}" is not configured; set SOURCE_DATABASE_URL'
            )
        created, updated = import_assets(alias)
        self.stdout.write(f'Imported assets: {created} created, {updated} updated')
