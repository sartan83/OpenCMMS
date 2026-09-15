from django.core.management.base import BaseCommand

from cmms_common.events.bus import get_event_bus

from pm.events import handle_event


class Command(BaseCommand):
    help = 'Consume asset and work-order events from the shared event bus'

    def handle(self, *args, **options):
        get_event_bus().subscribe(
            ['asset.created', 'asset.updated', 'workorder.created'],
            handle_event,
            'maintenance-service',
        )
