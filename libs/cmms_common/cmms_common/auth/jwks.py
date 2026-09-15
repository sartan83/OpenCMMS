from __future__ import annotations

import json
import os
import time
import urllib.request

import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


def fetch_jwks(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.load(response)


class RemoteUser:
    is_authenticated = True
    is_active = True

    def __init__(self, user_id, username='', role='', full_name=''):
        self.id = int(user_id) if str(user_id).isdigit() else user_id
        self.pk = self.id
        self.username = username
        self.role = role
        self.full_name = full_name or username
        self.is_staff = role == 'admin'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_supervisor(self):
        return self.role in ['admin', 'supervisor']

    @property
    def is_engineer(self):
        return self.role in ['admin', 'supervisor', 'engineer']

    def has_role(self, *roles):
        return self.role in roles

    def __str__(self):
        return f'{self.full_name} ({self.role})'


class JWKSAuthentication(BaseAuthentication):
    ttl = 300
    _cache = {}

    def authenticate(self, request):
        header = request.META.get('HTTP_AUTHORIZATION', '')
        if not header:
            return None
        try:
            scheme, token = header.split(None, 1)
        except ValueError:
            raise AuthenticationFailed('Invalid authorization header')
        if scheme.lower() != 'bearer':
            return None

        try:
            from django.conf import settings

            if settings.configured:
                url = getattr(settings, 'JWKS_URL', None)
                audience = getattr(settings, 'JWT_AUDIENCE', None)
                issuer = getattr(settings, 'JWT_ISSUER', None)
            else:
                url = audience = issuer = None
        except ImportError:
            url = audience = issuer = None
        url = url or os.environ.get('JWKS_URL')
        if not url:
            raise AuthenticationFailed('JWKS_URL is not configured')

        try:
            header_data = jwt.get_unverified_header(token)
            kid = header_data.get('kid')
            jwks = self._get_jwks(url)
            key_data = self._select_key(jwks, kid)
            if key_data is None and kid:
                jwks = self._get_jwks(url, force=True)
                key_data = self._select_key(jwks, kid)
            if key_data is None:
                raise AuthenticationFailed('No matching JWKS key')
            options = {'verify_aud': audience is not None}
            claims = jwt.decode(
                token,
                jwt.PyJWK(key_data).key,
                algorithms=['RS256'],
                audience=audience,
                issuer=issuer,
                options=options,
            )
        except AuthenticationFailed:
            raise
        except Exception as exc:
            raise AuthenticationFailed(f'Invalid token: {exc}') from exc

        user_id = claims.get('user_id', claims.get('sub'))
        if user_id is None:
            raise AuthenticationFailed('Token has no subject')
        return RemoteUser(
            user_id=user_id,
            username=claims.get('username', ''),
            role=claims.get('role', ''),
            full_name=claims.get('full_name', ''),
        ), token

    @classmethod
    def _get_jwks(cls, url, force=False):
        cached = cls._cache.get(url)
        now = time.monotonic()
        if not force and cached and now - cached[0] < cls.ttl:
            return cached[1]
        jwks = fetch_jwks(url)
        cls._cache[url] = (now, jwks)
        return jwks

    @staticmethod
    def _select_key(jwks, kid):
        keys = jwks.get('keys', [])
        if kid:
            return next((key for key in keys if key.get('kid') == kid), None)
        return keys[0] if len(keys) == 1 else None
