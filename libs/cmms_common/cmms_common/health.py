from django.db import connection
from django.http import JsonResponse


def health_view(request):
    try:
        connection.ensure_connection()
    except Exception:
        return JsonResponse({'status': 'error', 'database': 'error'}, status=503)
    return JsonResponse({'status': 'ok', 'database': 'ok'})
