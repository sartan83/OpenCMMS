"""
Serializers for Work Orders app
"""
from rest_framework import serializers
from .models import WorkOrder, WorkOrderComment, WorkOrderPart, WorkOrderType, WorkOrderStatus, Priority


class WorkOrderSerializer(serializers.ModelSerializer):
    """Serializer for WorkOrder model"""
    wo_type_display = serializers.CharField(source='get_wo_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    equipment_code = serializers.CharField(source='equipment.code', read_only=True)
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    assignee_name = serializers.CharField(source='assignee.full_name', read_only=True)
    requester_name = serializers.CharField(source='requested_by.full_name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    duration_hours = serializers.FloatField(read_only=True)

    class Meta:
        model = WorkOrder
        fields = ['id', 'wo_code', 'equipment', 'equipment_code', 'equipment_name',
                  'wo_type', 'wo_type_display', 'status', 'status_display',
                  'summary', 'description', 'priority', 'priority_display',
                  'requested_by', 'requester_name', 'assignee', 'assignee_name',
                  'assigned_at', 'assigned_by', 'maintenance_plan',
                  'planned_start', 'planned_end', 'actual_start', 'actual_end',
                  'failure_code', 'root_cause', 'actions_taken', 'checklist',
                  'downtime_minutes', 'labor_hours', 'parts_cost', 'total_cost',
                  'completed_by', 'completed_at', 'closed_by', 'closed_at',
                  'attachments', 'notes', 'created_at', 'updated_at',
                  'is_overdue', 'duration_hours']
        read_only_fields = ['id', 'requested_by', 'created_at', 'updated_at', 'is_overdue', 'duration_hours']
        extra_kwargs = {'wo_code': {'required': False}}


class WorkOrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for work order lists"""
    wo_type_display = serializers.CharField(source='get_wo_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    equipment_code = serializers.CharField(source='equipment.code', read_only=True)
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    assignee_name = serializers.CharField(source='assignee.full_name', read_only=True)

    class Meta:
        model = WorkOrder
        fields = ['id', 'wo_code', 'equipment', 'equipment_code', 'equipment_name',
                  'wo_type', 'wo_type_display', 'status', 'status_display',
                  'priority', 'priority_display', 'summary', 'assignee_name',
                  'planned_end', 'created_at']


class WorkOrderCommentSerializer(serializers.ModelSerializer):
    """Serializer for WorkOrderComment model"""
    author_name = serializers.CharField(source='author.full_name', read_only=True)

    class Meta:
        model = WorkOrderComment
        fields = ['id', 'work_order', 'author', 'author_name', 'comment', 'is_internal', 'created_at']
        read_only_fields = ['id', 'created_at']


class WorkOrderPartSerializer(serializers.ModelSerializer):
    """Serializer for WorkOrderPart model"""

    class Meta:
        model = WorkOrderPart
        fields = ['id', 'work_order', 'part_code', 'part_name', 'quantity', 'unit', 'unit_cost', 'total_cost']
        read_only_fields = ['id', 'total_cost']


class WorkOrderAssignSerializer(serializers.Serializer):
    """Serializer for assigning work orders"""
    assignee_id = serializers.IntegerField(required=True)
