import os

from django.core.wsgi import get_wsgi_application
from cmms_common.telemetry import configure_telemetry

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'audit_service.settings')
configure_telemetry('audit')
application = get_wsgi_application()
