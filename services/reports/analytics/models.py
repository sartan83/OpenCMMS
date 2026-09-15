from django.db import models


class ProcessedEvent(models.Model):
    event_id = models.CharField(max_length=64, unique=True)
    event_type = models.CharField(max_length=100)
    processed_at = models.DateTimeField(auto_now_add=True)


class AssetProjection(models.Model):
    asset_id = models.BigIntegerField(primary_key=True)
    asset_code = models.CharField(max_length=50)
    asset_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=30, blank=True, null=True)
    updated_at = models.DateTimeField()

    class Meta:
        ordering = ['asset_code']


class WorkOrderFact(models.Model):
    work_order_id = models.BigIntegerField(primary_key=True)
    wo_code = models.CharField(max_length=50)
    asset_id = models.BigIntegerField()
    asset_code = models.CharField(max_length=50, blank=True, null=True)
    asset_name = models.CharField(max_length=200, blank=True, null=True)
    wo_type = models.CharField(max_length=30)
    status = models.CharField(max_length=30)
    priority = models.CharField(max_length=30, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    assignee_id = models.BigIntegerField(blank=True, null=True)
    assignee_name = models.CharField(max_length=150, blank=True, null=True)
    maintenance_plan_id = models.BigIntegerField(blank=True, null=True)
    request_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    assigned_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    planned_start = models.DateTimeField(blank=True, null=True)
    planned_end = models.DateTimeField(blank=True, null=True)
    actual_start = models.DateTimeField(blank=True, null=True)
    actual_end = models.DateTimeField(blank=True, null=True)
    downtime_minutes = models.IntegerField(blank=True, null=True)
    labor_hours = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    parts_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    updated_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at', '-updated_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['wo_type', 'created_at']),
            models.Index(fields=['asset_id', 'created_at']),
            models.Index(fields=['assignee_id', 'created_at']),
        ]


class PartConsumptionFact(models.Model):
    transaction_id = models.BigIntegerField(primary_key=True)
    part_id = models.BigIntegerField()
    part_code = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    work_order_id = models.BigIntegerField(blank=True, null=True)
    actor_id = models.BigIntegerField()
    occurred_at = models.DateTimeField()

    class Meta:
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['part_id', 'occurred_at']),
            models.Index(fields=['work_order_id', 'occurred_at']),
        ]


class InspectionFact(models.Model):
    inspection_record_id = models.BigIntegerField(primary_key=True)
    asset_id = models.BigIntegerField()
    work_order_id = models.BigIntegerField(blank=True, null=True)
    inspector_id = models.BigIntegerField()
    failed_items = models.JSONField(default=list)
    failed_item_count = models.IntegerField(default=0)
    occurred_at = models.DateTimeField()

    class Meta:
        ordering = ['-occurred_at']
        indexes = [models.Index(fields=['asset_id', 'occurred_at'])]


class ScheduledReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('workorder_summary', 'Work Order Summary'),
        ('downtime_analysis', 'Downtime Analysis'),
        ('spareparts_usage', 'Spare Parts Usage'),
        ('maintenance-compliance', 'Maintenance Compliance'),
        ('cost-analysis', 'Cost Analysis'),
        ('technician-performance', 'Technician Performance'),
        ('equipment-availability', 'Equipment Availability'),
    ]
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('disabled', 'Disabled'),
    ]

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    parameters = models.JSONField(default=dict, blank=True)
    recipients = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    created_by_id = models.BigIntegerField()
    created_by_name = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scheduled_reports'
        ordering = ['name']


class ReportRun(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.BigAutoField(primary_key=True)
    scheduled_report = models.ForeignKey(
        ScheduledReport,
        on_delete=models.CASCADE,
        related_name='runs',
        null=True,
        blank=True,
    )
    report_type = models.CharField(max_length=50)
    parameters = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result_data = models.JSONField(default=dict, blank=True)
    output_file = models.CharField(max_length=255, blank=True, null=True)
    output_format = models.CharField(max_length=10, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    requested_by_id = models.BigIntegerField(blank=True, null=True)
    requested_by_name = models.CharField(max_length=150, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'report_runs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report_type', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    @property
    def duration_seconds(self):
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0
