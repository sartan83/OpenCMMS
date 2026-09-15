import logging

import jwt
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework.exceptions import AuthenticationFailed

from cmms_common.auth.jwks import JWKSAuthentication

logger = logging.getLogger(__name__)


class LocalUserJWKSAuthentication(JWKSAuthentication):
    """Map an identity token to the monolith's local user row."""

    def authenticate(self, request):
        try:
            result = super().authenticate(request)
        except AuthenticationFailed:
            token = request.META.get('HTTP_AUTHORIZATION', '').split()[-1]
            try:
                has_kid = bool(jwt.get_unverified_header(token).get('kid'))
            except Exception:
                has_kid = False
            if not has_kid:
                return None
            raise

        if result is None:
            return None

        remote, token = result
        username = remote.username or f'user-{remote.id}'
        defaults = {
            'username': username,
            'role': remote.role or 'operator',
            'full_name': remote.full_name or '',
            'is_active': True,
        }
        user_model = get_user_model()
        try:
            user, _ = user_model.objects.update_or_create(
                id=remote.id,
                defaults=defaults,
            )
        except IntegrityError:
            logger.warning(
                'Identity username %s already belongs to another local user',
                username,
            )
            user = user_model.objects.get(username=username)
            user.role = defaults['role']
            user.full_name = defaults['full_name']
            user.is_active = defaults['is_active']
            user.save(update_fields=['role', 'full_name', 'is_active', 'updated_at'])
        return user, token
