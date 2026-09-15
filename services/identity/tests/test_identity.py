import jwt
import pytest
from rest_framework.test import APIClient

from cmms_common.auth.jwks import JWKSAuthentication
from users.models import User


@pytest.mark.django_db
def test_login_returns_rs256_token_and_jwks(monkeypatch):
    user = User.objects.create_user(
        username='identity-user',
        password='password123',
        role='engineer',
        full_name='Identity User',
    )
    client = APIClient()
    response = client.post(
        '/api/auth/login/',
        {'username': user.username, 'password': 'password123'},
        format='json',
    )
    assert response.status_code == 200
    token = response.data['access']
    assert jwt.get_unverified_header(token)['alg'] == 'RS256'

    jwks_response = client.get('/.well-known/jwks.json')
    assert jwks_response.status_code == 200
    jwks = jwks_response.json()
    assert len(jwks['keys']) == 1
    monkeypatch.setattr('cmms_common.auth.jwks.fetch_jwks', lambda url: jwks)

    class Request:
        META = {'HTTP_AUTHORIZATION': f'Bearer {token}'}

    authenticated_user, _ = JWKSAuthentication().authenticate(Request())
    assert authenticated_user.id == user.id
