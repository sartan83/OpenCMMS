from django.db import models


class AuditEntry(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_id = models.CharField(max_length=64, unique=True)
    actor_id = models.IntegerField()
    actor_username = models.CharField(max_length=150)
    action = models.CharField(max_length=50)
    entity_type = models.CharField(max_length=100)
    entity_id = models.IntegerField()
    entity_repr = models.CharField(max_length=255, blank=True)
    diff = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    service = models.CharField(max_length=100)
    occurred_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-occurred_at', '-created_at']
