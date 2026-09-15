from rest_framework import serializers

from .models import AuditEntry


class AuditEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEntry
        fields = '__all__'
        read_only_fields = fields
