import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from cmms_common.auth.jwks import JWKSAuthentication
from cmms_common.auth.keys import jwks_from_public_key


class Request:
    META = {}


def test_jwks_authentication_roundtrip(monkeypatch):
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
    jwks = jwks_from_public_key(public_pem, 'test-key')
    token = jwt.encode(
        {'sub': '7', 'username': 'alice', 'role': 'engineer', 'full_name': 'Alice'},
        private_pem,
        algorithm='RS256',
        headers={'kid': 'test-key'},
    )
    monkeypatch.setenv('JWKS_URL', 'https://identity.test/.well-known/jwks.json')
    monkeypatch.setattr(
        'cmms_common.auth.jwks.fetch_jwks',
        lambda url: jwks,
    )
    Request.META = {'HTTP_AUTHORIZATION': f'Bearer {token}'}

    user, returned_token = JWKSAuthentication().authenticate(Request())

    assert returned_token == token
    assert user.id == 7
    assert user.username == 'alice'
    assert user.role == 'engineer'
    assert user.is_engineer
