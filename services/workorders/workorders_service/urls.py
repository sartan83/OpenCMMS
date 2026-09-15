from django.urls import include, path

from cmms_common.health import health_view

urlpatterns = [
    path('api/workorders/', include('workorders_api.urls')),
    path('health/', health_view, name='health'),
    path('', include('django_prometheus.urls')),
]
