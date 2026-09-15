from rest_framework import mixins, viewsets

from cmms_common.audit import audit_log

from .models import InspectionRecord, InspectionRoute, InspectionTemplate
from .serializers import (
    InspectionRecordSerializer,
    InspectionRouteSerializer,
    InspectionTemplateSerializer,
)


def _audit(request, action, entity_type, obj):
    audit_log(
        request.user,
        action,
        entity_type,
        obj.id,
        str(obj),
        service='inspections',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )


class InspectionRecordViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = InspectionRecord.objects.all()
    serializer_class = InspectionRecordSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        for param, field in (
            ('equipment', 'equipment'),
            ('result', 'result'),
            ('inspector', 'inspector_id'),
            ('route', 'route'),
        ):
            value = self.request.query_params.get(param)
            if value:
                queryset = queryset.filter(**{field: value})
        return queryset

    def perform_create(self, serializer):
        obj = serializer.save(
            inspector_id=self.request.user.id,
            inspector_name=self.request.user.full_name,
        )
        _audit(self.request, 'create', 'InspectionRecord', obj)

    def perform_update(self, serializer):
        obj = serializer.save()
        _audit(self.request, 'update', 'InspectionRecord', obj)


class InspectionTemplateViewSet(viewsets.ModelViewSet):
    queryset = InspectionTemplate.objects.all()
    serializer_class = InspectionTemplateSerializer

    def perform_create(self, serializer):
        obj = serializer.save()
        _audit(self.request, 'create', 'InspectionTemplate', obj)

    def perform_update(self, serializer):
        obj = serializer.save()
        _audit(self.request, 'update', 'InspectionTemplate', obj)

    def perform_destroy(self, instance):
        _audit(self.request, 'delete', 'InspectionTemplate', instance)
        super().perform_destroy(instance)


class InspectionRouteViewSet(viewsets.ModelViewSet):
    queryset = InspectionRoute.objects.all()
    serializer_class = InspectionRouteSerializer

    def perform_create(self, serializer):
        data = serializer.validated_data
        if (
            data.get('inspector_id') == self.request.user.id
            and not data.get('inspector_name')
        ):
            data['inspector_name'] = self.request.user.full_name
        obj = serializer.save()
        _audit(self.request, 'create', 'InspectionRoute', obj)

    def perform_update(self, serializer):
        data = serializer.validated_data
        if (
            data.get('inspector_id') == self.request.user.id
            and not data.get('inspector_name')
        ):
            data['inspector_name'] = self.request.user.full_name
        obj = serializer.save()
        _audit(self.request, 'update', 'InspectionRoute', obj)

    def perform_destroy(self, instance):
        _audit(self.request, 'delete', 'InspectionRoute', instance)
        super().perform_destroy(instance)
