from rest_framework import serializers

from .models import (
    AssetProjection,
    InspectionFact,
    PartConsumptionFact,
    ReportRun,
    ScheduledReport,
    WorkOrderFact,
)


class AssetProjectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetProjection
        fields = '__all__'
        read_only_fields = [
            'asset_id', 'asset_code', 'asset_name', 'category', 'status', 'updated_at',
        ]


class WorkOrderFactSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrderFact
        fields = '__all__'
        read_only_fields = [
            'work_order_id', 'wo_code', 'asset_id', 'asset_code', 'asset_name',
            'wo_type', 'status', 'priority', 'title', 'assignee_id',
            'assignee_name', 'maintenance_plan_id', 'request_id', 'created_at',
            'assigned_at', 'completed_at', 'closed_at', 'planned_start',
            'planned_end', 'actual_start', 'actual_end', 'downtime_minutes',
            'labor_hours', 'parts_cost', 'total_cost', 'updated_at',
        ]


class PartConsumptionFactSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartConsumptionFact
        fields = '__all__'
        read_only_fields = [
            'transaction_id', 'part_id', 'part_code', 'quantity', 'unit_cost',
            'total_cost', 'work_order_id', 'actor_id', 'occurred_at',
        ]


class InspectionFactSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionFact
        fields = '__all__'
        read_only_fields = [
            'inspection_record_id', 'asset_id', 'work_order_id', 'inspector_id',
            'failed_items', 'failed_item_count', 'occurred_at',
        ]


class ScheduledReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledReport
        fields = '__all__'
        read_only_fields = [
            'id', 'created_by_id', 'created_by_name', 'created_at', 'updated_at',
        ]


class ReportRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportRun
        fields = '__all__'
        read_only_fields = [
            'id', 'scheduled_report', 'report_type', 'parameters', 'status',
            'result_data', 'output_file', 'output_format', 'error_message',
            'requested_by_id', 'requested_by_name', 'started_at', 'completed_at',
            'created_at',
        ]
