import pytest
from django.test import Client


@pytest.mark.django_db
def test_health(db, monkeypatch):
    monkeypatch.setattr('redis.Redis.ping', lambda self: True)
    response = Client().get('/health/')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok', 'database': 'ok', 'redis': 'ok'}
