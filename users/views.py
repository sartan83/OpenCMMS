"""
Views for Users app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth import get_user_model

from cmms_common.audit import audit_log
from cmms_common.events.bus import Event, get_event_bus
from .models import User, AuditLog, Role
from .serializers import UserSerializer, UserRegistrationSerializer, CustomTokenObtainPairSerializer, AuditLogSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Custom permissions based on action"""
        if self.action in ['register', 'create']:
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        qs = super().get_queryset()

        # 所有认证用户都可以看到用户列表
        return qs.order_by('-created_at')

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user info"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Register a new user"""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Log the registration
            audit_log(
                actor=user,
                action='create',
                entity_type='User',
                entity_id=user.id,
                entity_repr=str(user),
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            get_event_bus().publish(Event(
                type='user.created',
                payload={
                    'user_id': user.id,
                    'username': user.username,
                    'role': user.role,
                    'full_name': user.full_name or user.username,
                },
                source='identity',
            ))

            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AuditLog model (read-only)"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter audit logs based on user role"""
        user = self.request.user
        qs = super().get_queryset()

        # Non-admin users can only see logs for themselves
        if not user.is_admin:
            qs = qs.filter(actor=user)

        return qs.select_related('actor').order_by('-created_at')
