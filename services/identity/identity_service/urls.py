from django.http import JsonResponse
from django.urls import include, path
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes

from cmms_common.auth.keys import jwks_from_public_key
from cmms_common.health import health_view
from users.urls import urlpatterns as user_urlpatterns
from . import settings


@api_view(['GET'])
@permission_classes([AllowAny])
def jwks_view(request):
    return JsonResponse(jwks_from_public_key(settings.JWT_PUBLIC_KEY, settings.JWT_KID))


urlpatterns = [
    path('api/auth/', include((user_urlpatterns, 'users'))),
    path('.well-known/jwks.json', jwks_view, name='jwks'),
    path('health/', health_view, name='health'),
]
