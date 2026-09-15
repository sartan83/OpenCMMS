import redis
from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def health(request):
    result = {'status': 'ok', 'database': 'ok', 'redis': 'ok'}
    try:
        connection.ensure_connection()
    except Exception:
        result['status'] = 'error'
        result['database'] = 'error'

    try:
        redis.Redis.from_url(settings.REDIS_URL, socket_timeout=1).ping()
    except Exception:
        result['status'] = 'error'
        result['redis'] = 'error'

    status_code = 200 if result['status'] == 'ok' else 503
    return JsonResponse(result, status=status_code)
