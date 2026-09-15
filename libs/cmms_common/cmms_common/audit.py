from __future__ import annotations

import os

from .events.bus import Event
from .events.bus import get_event_bus


def _setting(name: str, default):
    try:
        from django.conf import settings

        if settings.configured:
            return getattr(settings, name, default)
    except ImportError:
        pass
    return default


def audit_log(
    actor,
    action,
    entity_type,
    entity_id,
    entity_repr='',
    diff=None,
    ip_address=None,
    user_agent='',
    service=None,
):
    service = service or _setting('SERVICE_NAME', os.environ.get('SERVICE_NAME', 'monolith'))
    event = Event(
        type='audit.recorded',
        payload={
            'actor_id': int(getattr(actor, 'id', 0) or 0),
            'actor_username': getattr(actor, 'username', ''),
            'action': action,
            'entity_type': entity_type,
            'entity_id': int(entity_id),
            'entity_repr': entity_repr,
            'diff': diff or {},
            'ip_address': ip_address,
            'user_agent': user_agent or '',
            'service': service,
        },
        source=service,
    )
    get_event_bus().publish(event)

    if _setting('AUDIT_LOCAL_WRITE', True):
        try:
            from django.apps import apps

            if apps.ready and apps.is_installed('users'):
                from users.models import AuditLog

                AuditLog.log(
                    actor=actor,
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    entity_repr=entity_repr,
                    diff=diff,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
        except (ImportError, LookupError):
            pass
    return event
