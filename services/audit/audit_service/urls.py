from django.urls import include, path

from cmms_common.health import health_view

urlpatterns = [
    path('api/audit/', include('auditlog.urls')),
    path('health/', health_view, name='health'),
    path('', include('django_prometheus.urls')),
]
