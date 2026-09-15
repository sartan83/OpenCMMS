import redis
from kombu import Connection
from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def health_view(request):
    result = {'status': 'ok', 'database': 'ok'}
    try:
        connection.ensure_connection()
    except Exception:
        result['status'] = 'error'
        result['database'] = 'error'

    redis_url = getattr(settings, 'REDIS_URL', None)
    if redis_url:
        result['redis'] = 'ok'
        try:
            redis.Redis.from_url(redis_url, socket_timeout=1).ping()
        except Exception:
            result['status'] = 'error'
            result['redis'] = 'error'

    event_bus_url = getattr(settings, 'EVENT_BUS_URL', None)
    if event_bus_url:
        result['event_bus'] = 'ok'
        try:
            with Connection(event_bus_url, connect_timeout=1) as event_bus:
                event_bus.ensure_connection(max_retries=1)
        except Exception:
            result['status'] = 'error'
            result['event_bus'] = 'error'

    status_code = 200 if result['status'] == 'ok' else 503
    return JsonResponse(result, status=status_code)
