"""
Serializers for Maintenance app
"""
from rest_framework import serializers
from .models import AssetProjection, MaintenancePlan, WorkOrderTemplate, TriggerType


class MaintenancePlanSerializer(serializers.ModelSerializer):
    """Serializer for MaintenancePlan model"""
    equipment = serializers.IntegerField(source='equipment_id')
    equipment_code = serializers.CharField(read_only=True)
    equipment_name = serializers.CharField(read_only=True)
    trigger_type_display = serializers.CharField(source='get_trigger_type_display', read_only=True)
    frequency_unit_display = serializers.CharField(source='get_frequency_unit_display', read_only=True)
    created_by = serializers.IntegerField(source='created_by_id', read_only=True)
    created_by_name = serializers.CharField(read_only=True)

    class Meta:
        model = MaintenancePlan
        fields = [
            'id', 'code', 'equipment', 'equipment_code', 'equipment_name',
            'title', 'description', 'trigger_type', 'trigger_type_display',
            'frequency_value', 'frequency_unit', 'frequency_unit_display',
            'counter_name', 'counter_threshold',
            'checklist_template', 'estimated_hours', 'estimated_cost',
            'required_skills', 'priority', 'is_active',
            'last_generated_date', 'last_counter_value',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'equipment_code', 'equipment_name',
                            'created_by_name', 'created_at', 'updated_at']

    def validate_equipment(self, value):
        if not AssetProjection.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Unknown equipment')
        return value

    @staticmethod
    def _cache_equipment(validated_data):
        equipment_id = validated_data.get('equipment_id')
        if equipment_id is not None:
            projection = AssetProjection.objects.get(pk=equipment_id)
            validated_data['equipment_code'] = projection.code
            validated_data['equipment_name'] = projection.name
        return validated_data

    def create(self, validated_data):
        return super().create(self._cache_equipment(validated_data))

    def update(self, instance, validated_data):
        return super().update(instance, self._cache_equipment(validated_data))


class MaintenancePlanListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for maintenance plan lists"""
    equipment_code = serializers.CharField(read_only=True)
    equipment_name = serializers.CharField(read_only=True)
    trigger_type_display = serializers.CharField(source='get_trigger_type_display', read_only=True)
    frequency_display = serializers.SerializerMethodField()

    class Meta:
        model = MaintenancePlan
        fields = [
            'id', 'code', 'equipment_code', 'equipment_name', 'title',
            'trigger_type', 'trigger_type_display', 'frequency_display',
            'priority', 'is_active', 'last_generated_date'
        ]

    def get_frequency_display(self, obj):
        """Get human-readable frequency display"""
        if obj.trigger_type == TriggerType.TIME and obj.frequency_value:
            return f"{obj.frequency_value} {obj.get_frequency_unit_display()}"
        elif obj.trigger_type == TriggerType.COUNTER and obj.counter_threshold:
            return f"{obj.counter_name or 'Counter'} >= {obj.counter_threshold}"
        return "-"


class WorkOrderTemplateSerializer(serializers.ModelSerializer):
    """Serializer for WorkOrderTemplate model"""
    work_order_type_display = serializers.CharField(source='get_work_order_type_display', read_only=True)

    class Meta:
        model = WorkOrderTemplate
        fields = [
            'id', 'code', 'name', 'description', 'work_order_type',
            'work_order_type_display', 'checklist_template',
            'estimated_hours', 'required_skills', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
