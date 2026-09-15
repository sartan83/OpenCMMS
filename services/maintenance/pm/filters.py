import django_filters

from .models import MaintenancePlan


class MaintenancePlanFilter(django_filters.FilterSet):
    equipment = django_filters.NumberFilter(field_name='equipment_id')

    class Meta:
        model = MaintenancePlan
        fields = ['trigger_type', 'is_active', 'priority']
