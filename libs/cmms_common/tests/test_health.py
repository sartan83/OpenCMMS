import json

import pytest
from django.test import RequestFactory, override_settings

from cmms_common.health import health_view


@pytest.mark.django_db
@override_settings(REDIS_URL=None, EVENT_BUS_URL=None)
def test_health_omits_optional_components_when_unconfigured():
    response = health_view(RequestFactory().get('/health/'))

    assert response.status_code == 200
    assert json.loads(response.content) == {'status': 'ok', 'database': 'ok'}


@pytest.mark.django_db
@override_settings(REDIS_URL='redis://127.0.0.1:1/0', EVENT_BUS_URL=None)
def test_health_reports_unreachable_redis():
    response = health_view(RequestFactory().get('/health/'))

    assert response.status_code == 503
    assert json.loads(response.content) == {
        'status': 'error',
        'database': 'ok',
        'redis': 'error',
    }
