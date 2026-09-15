from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives import serialization


def _load_key(path_env: str, private: bool):
    path = os.environ.get(path_env)
    if not path:
        return None
    with open(path, 'rb') as key_file:
        return key_file.read()


def load_private_key(path_env='JWT_PRIVATE_KEY_PATH'):
    return _load_key(path_env, private=True)


def load_public_key(path_env='JWT_PUBLIC_KEY_PATH'):
    return _load_key(path_env, private=False)


def _base64url(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, 'big')
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode('ascii')


def jwks_from_public_key(pem, kid):
    if isinstance(pem, str):
        pem = pem.encode()
    key = serialization.load_pem_public_key(pem)
    numbers = key.public_numbers()
    return {
        'keys': [{
            'kty': 'RSA',
            'use': 'sig',
            'alg': 'RS256',
            'kid': kid,
            'n': _base64url(numbers.n),
            'e': _base64url(numbers.e),
        }]
    }
