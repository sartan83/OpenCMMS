from rest_framework import viewsets

from .models import AuditEntry
from .serializers import AuditEntrySerializer


class AuditEntryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditEntry.objects.all()
    serializer_class = AuditEntrySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_admin:
            queryset = queryset.filter(actor_id=self.request.user.id)
        return queryset
