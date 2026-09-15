from django.core.management.base import BaseCommand

from cmms_common.events.bus import Event, get_event_bus

from analytics.projections import HANDLERS


def dispatch_event(event):
    if isinstance(event, dict):
        event = Event.from_dict(event)
    handler = HANDLERS.get(event.type)
    return handler(event) if handler else False


class Command(BaseCommand):
    help = 'Consume domain events into reporting projections'

    def handle(self, *args, **options):
        get_event_bus().subscribe(
            list(HANDLERS),
            dispatch_event,
            'reports-service',
        )
