"""
Serializers for the workorders service.

Field names match the monolith API contract; soft references are exposed
under their monolith names (e.g. `assignee` carries the user id).
"""
from rest_framework import serializers

from .models import WorkOrder, WorkOrderComment, WorkOrderPart


class WorkOrderSerializer(serializers.ModelSerializer):
    wo_type_display = serializers.CharField(source='get_wo_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    equipment_code = serializers.CharField(read_only=True)
    equipment_name = serializers.CharField(read_only=True)
    requested_by = serializers.IntegerField(source='requested_by_id', read_only=True)
    requester_name = serializers.CharField(source='requested_by_name', read_only=True)
    assignee = serializers.IntegerField(source='assignee_id', required=False, allow_null=True)
    assignee_name = serializers.CharField(read_only=True)
    assigned_by = serializers.IntegerField(source='assigned_by_id', required=False, allow_null=True)
    maintenance_plan = serializers.IntegerField(source='maintenance_plan_id', required=False, allow_null=True)
    completed_by = serializers.IntegerField(source='completed_by_id', required=False, allow_null=True)
    closed_by = serializers.IntegerField(source='closed_by_id', required=False, allow_null=True)
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
    wo_type_display = serializers.CharField(source='get_wo_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    equipment_code = serializers.CharField(read_only=True)
    equipment_name = serializers.CharField(read_only=True)
    assignee_name = serializers.CharField(read_only=True)

    class Meta:
        model = WorkOrder
        fields = ['id', 'wo_code', 'equipment', 'equipment_code', 'equipment_name',
                  'wo_type', 'wo_type_display', 'status', 'status_display',
                  'priority', 'priority_display', 'summary', 'assignee_name',
                  'planned_end', 'created_at']


class WorkOrderCommentSerializer(serializers.ModelSerializer):
    author = serializers.IntegerField(source='author_id', read_only=True)
    author_name = serializers.CharField(read_only=True)

    class Meta:
        model = WorkOrderComment
        fields = ['id', 'work_order', 'author', 'author_name', 'comment', 'is_internal', 'created_at']
        read_only_fields = ['id', 'author', 'author_name', 'created_at']


class WorkOrderPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrderPart
        fields = ['id', 'work_order', 'part_code', 'part_name', 'quantity', 'unit', 'unit_cost', 'total_cost']
        read_only_fields = ['id', 'total_cost']


class WorkOrderAssignSerializer(serializers.Serializer):
    assignee_id = serializers.IntegerField(required=True)
    assignee_name = serializers.CharField(required=False, allow_blank=True)
