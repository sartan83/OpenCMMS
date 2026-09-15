import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from cmms_common.auth.jwks import JWKSAuthentication
from cmms_common.auth.keys import jwks_from_public_key
from users.models import User


def _key_material():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, jwks_from_public_key(public_pem, 'identity-test')


def _rest_framework_settings():
    from cmms_project.settings import REST_FRAMEWORK

    return {
        **REST_FRAMEWORK,
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'cmms_project.authentication.LocalUserJWKSAuthentication',
            'rest_framework_simplejwt.authentication.JWTAuthentication',
        ),
    }


@pytest.mark.django_db
def test_identity_rs256_token_creates_local_user(monkeypatch):
    private_pem, jwks = _key_material()
    token = jwt.encode(
        {
            'user_id': 42,
            'username': 'identity-user',
            'role': 'engineer',
            'full_name': 'Identity User',
        },
        private_pem,
        algorithm='RS256',
        headers={'kid': 'identity-test'},
    )

    monkeypatch.setattr(
        JWKSAuthentication,
        '_get_jwks',
        classmethod(lambda cls, url, force=False: jwks),
    )
    with override_settings(
        JWKS_URL='https://identity.test/.well-known/jwks.json',
        REST_FRAMEWORK=_rest_framework_settings(),
    ):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = client.get('/api/assets/')

    assert response.status_code == 200
    user = User.objects.get(id=42)
    assert user.username == 'identity-user'
    assert user.role == 'engineer'
    assert user.full_name == 'Identity User'


@pytest.mark.django_db
def test_hs256_token_falls_through_to_simplejwt(monkeypatch, admin_user):
    _, jwks = _key_material()
    token = str(RefreshToken.for_user(admin_user).access_token)
    monkeypatch.setattr(
        JWKSAuthentication,
        '_get_jwks',
        classmethod(lambda cls, url, force=False: jwks),
    )

    with override_settings(
        JWKS_URL='https://identity.test/.well-known/jwks.json',
        REST_FRAMEWORK=_rest_framework_settings(),
    ):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = client.get('/api/assets/')

    assert response.status_code == 200
