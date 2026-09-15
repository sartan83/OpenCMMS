"""
Views for Maintenance app
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.contrib.auth import get_user_model

from cmms_common.audit import audit_log
from .models import MaintenancePlan, WorkOrderTemplate
from .serializers import (
    MaintenancePlanSerializer,
    MaintenancePlanListSerializer,
    WorkOrderTemplateSerializer
)

User = get_user_model()


class IsAdminOrSupervisorOrReadOnly(BasePermission):
    """
    自定义权限：admin和supervisor可以修改，其他用户只读
    """
    def has_permission(self, request, view):
        # 读取操作允许所有认证用户
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user.is_authenticated
        # 创建/更新/删除只允许admin或supervisor
        return request.user.is_authenticated and request.user.role in ['admin', 'supervisor']


class MaintenancePlanViewSet(viewsets.ModelViewSet):
    """ViewSet for MaintenancePlan model"""
    queryset = MaintenancePlan.objects.select_related(
        'equipment', 'created_by'
    ).all()
    serializer_class = MaintenancePlanSerializer
    permission_classes = [IsAdminOrSupervisorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['trigger_type', 'equipment', 'is_active', 'priority']
    search_fields = ['code', 'title', 'description']
    ordering_fields = ['code', 'created_at', 'last_generated_date']
    ordering = ['code']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return MaintenancePlanListSerializer
        return MaintenancePlanSerializer

    def perform_create(self, serializer):
        """Set created_by on create"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def generate_work_order(self, request, pk=None):
        """Generate a work order from this maintenance plan"""
        plan = self.get_object()

        if not plan.is_active:
            return Response(
                {"error": "Cannot generate work order from inactive plan"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create work order
        from workorders.models import WorkOrder, WorkOrderType, WorkOrderStatus

        # Generate work order code
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m%d')
        wo_count = WorkOrder.objects.filter(
            wo_code__startswith=f'PM-{date_str}'
        ).count()
        wo_code = f"PM-{date_str}-{wo_count + 1:03d}"

        # Create work order
        work_order = WorkOrder.objects.create(
            wo_code=wo_code,
            equipment=plan.equipment,
            wo_type=WorkOrderType.PM,
            status=WorkOrderStatus.OPEN,
            summary=f"预防性维护 - {plan.title}",
            description=plan.description,
            priority=plan.priority,
            planned_start=timezone.now(),
            checklist=plan.checklist_template,
            maintenance_plan=plan,
            requested_by=request.user
        )

        # Update last generated date
        plan.last_generated_date = timezone.now().date()
        plan.save()

        audit_log(
            actor=request.user,
            action='create',
            entity_type='WorkOrder',
            entity_id=work_order.id,
            entity_repr=str(work_order)
        )

        return Response({
            "message": "Work order generated successfully",
            "work_order_id": work_order.id,
            "wo_code": work_order.wo_code
        })

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a maintenance plan"""
        plan = self.get_object()
        plan.is_active = True
        plan.save()
        return Response({"message": "Plan activated successfully"})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a maintenance plan"""
        plan = self.get_object()
        plan.is_active = False
        plan.save()
        return Response({"message": "Plan deactivated successfully"})


class WorkOrderTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for WorkOrderTemplate model"""
    queryset = WorkOrderTemplate.objects.all()
    serializer_class = WorkOrderTemplateSerializer
    permission_classes = [IsAdminOrSupervisorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['work_order_type', 'is_active']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name']
    ordering = ['code']
