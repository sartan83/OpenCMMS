import uuid

from django.db import models, transaction


class InspectionResult(models.TextChoices):
    PASS = 'pass', 'Pass'
    FAIL = 'fail', 'Fail'
    WARNING = 'warning', 'Warning'


class AssetProjection(models.Model):
    asset_id = models.IntegerField(primary_key=True)
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=50, blank=True)
    process = models.CharField(max_length=100, blank=True)
    factory = models.CharField(max_length=100, blank=True)
    workshop = models.CharField(max_length=100, blank=True)
    line = models.CharField(max_length=100, blank=True)
    station = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inspection_asset_projections'


class ProcessedEvent(models.Model):
    event_id = models.CharField(max_length=64, unique=True)
    event_type = models.CharField(max_length=100)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inspection_processed_events'


class InspectionRecord(models.Model):
    id = models.BigAutoField(primary_key=True)
    equipment = models.IntegerField(db_index=True)
    equipment_code = models.CharField(max_length=100, blank=True)
    equipment_name = models.CharField(max_length=200, blank=True)
    route = models.CharField(max_length=100, blank=True, null=True)
    items = models.JSONField()
    inspector_id = models.IntegerField(db_index=True)
    inspector_name = models.CharField(max_length=150, blank=True)
    result = models.CharField(
        max_length=20,
        choices=InspectionResult.choices,
        default=InspectionResult.PASS,
    )
    triggered_work_order_id = models.IntegerField(null=True, blank=True)
    work_order_request_id = models.CharField(max_length=36, null=True, blank=True, db_index=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'inspection_records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['equipment', 'created_at']),
            models.Index(fields=['inspector_id', 'created_at']),
            models.Index(fields=['result', 'created_at']),
        ]

    def __str__(self):
        timestamp = self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        return f'Inspection - {self.equipment_code or self.equipment} - {timestamp}'

    def save(self, *args, **kwargs):
        if self.items:
            self.result = (
                InspectionResult.FAIL
                if any(not item.get('ok', True) for item in self.items)
                else InspectionResult.PASS
            )
        if not self.equipment_code or not self.equipment_name:
            asset = AssetProjection.objects.filter(asset_id=self.equipment).first()
            if asset:
                self.equipment_code = self.equipment_code or asset.code
                self.equipment_name = self.equipment_name or asset.name
        publish = (
            self.result == InspectionResult.FAIL
            and self.triggered_work_order_id is None
            and not self.work_order_request_id
        )
        if publish:
            self.work_order_request_id = str(uuid.uuid4())
        super().save(*args, **kwargs)
        if publish:
            from .events import publish_inspection_failed

            transaction.on_commit(lambda: publish_inspection_failed(self))


class InspectionTemplate(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    items_template = models.JSONField()
    equipment_type = models.CharField(max_length=50, blank=True, null=True)
    frequency_days = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inspection_templates'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.name}'


class InspectionRoute(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    route_items = models.JSONField()
    estimated_duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    inspector_id = models.IntegerField(null=True, blank=True, db_index=True)
    inspector_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inspection_routes'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.name}'
