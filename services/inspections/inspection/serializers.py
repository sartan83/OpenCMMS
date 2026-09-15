from rest_framework import serializers

from .models import InspectionRecord, InspectionRoute, InspectionTemplate


class InspectionRecordSerializer(serializers.ModelSerializer):
    inspector = serializers.IntegerField(source='inspector_id', read_only=True)
    triggered_work_order = serializers.IntegerField(
        source='triggered_work_order_id',
        read_only=True,
    )

    class Meta:
        model = InspectionRecord
        fields = [
            'id', 'equipment', 'equipment_code', 'equipment_name', 'route',
            'items', 'inspector', 'inspector_name', 'result',
            'triggered_work_order', 'work_order_request_id', 'notes',
            'created_at',
        ]
        read_only_fields = [
            'id', 'equipment_code', 'equipment_name', 'inspector',
            'inspector_name', 'result', 'triggered_work_order',
            'work_order_request_id', 'created_at',
        ]


class InspectionTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class InspectionRouteSerializer(serializers.ModelSerializer):
    inspector = serializers.IntegerField(
        source='inspector_id',
        required=False,
        allow_null=True,
    )
    inspector_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = InspectionRoute
        fields = [
            'id', 'code', 'name', 'description', 'route_items',
            'estimated_duration_minutes', 'inspector', 'inspector_name',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
