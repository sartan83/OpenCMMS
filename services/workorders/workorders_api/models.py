"""
Work Order models for the workorders service.

Cross-service references (assets, maintenance plans, users) are soft
references: integer ids plus cached display columns kept in sync from bus
events.
"""
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class WorkOrderType(models.TextChoices):
    PM = 'PM', 'Preventive Maintenance'
    CM = 'CM', 'Corrective Maintenance'
    INSPECTION = 'inspection', 'Inspection'


class WorkOrderStatus(models.TextChoices):
    OPEN = 'open', 'Open'
    ASSIGNED = 'assigned', 'Assigned'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    CLOSED = 'closed', 'Closed'
    CANCELED = 'canceled', 'Canceled'


class Priority(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    CRITICAL = 'critical', 'Critical'


class AssetProjection(models.Model):
    """Local read model of assets, populated from asset.created / asset.updated."""
    asset_id = models.IntegerField(primary_key=True)
    code = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, blank=True)
    process = models.CharField(max_length=100, blank=True)
    factory = models.CharField(max_length=100, blank=True)
    workshop = models.CharField(max_length=100, blank=True)
    line = models.CharField(max_length=100, blank=True)
    station = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'asset_projections'

    def __str__(self):
        return f'{self.code} - {self.name}'


class ProcessedEvent(models.Model):
    """Dedupe table for consumed bus events."""
    event_id = models.CharField(max_length=64, primary_key=True)
    event_type = models.CharField(max_length=100)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'processed_events'


def generate_wo_code(prefix='WO'):
    today = timezone.now().strftime('%Y%m%d')
    last_wo = WorkOrder.objects.filter(
        wo_code__startswith=f'{prefix}-{today}-'
    ).order_by('-wo_code').first()
    seq = 1
    if last_wo:
        try:
            seq = int(last_wo.wo_code.split('-')[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    return f'{prefix}-{today}-{seq:03d}'


class WorkOrder(models.Model):
    id = models.BigAutoField(primary_key=True)
    wo_code = models.CharField(max_length=50, unique=True, db_index=True, verbose_name='Work Order Code')
    # Soft reference to assets.Asset (API field name stays `equipment`)
    equipment = models.IntegerField(db_index=True, verbose_name='Equipment')
    equipment_code = models.CharField(max_length=50, blank=True, default='')
    equipment_name = models.CharField(max_length=200, blank=True, default='')
    wo_type = models.CharField(max_length=20, choices=WorkOrderType.choices, default=WorkOrderType.CM)
    status = models.CharField(max_length=20, choices=WorkOrderStatus.choices, default=WorkOrderStatus.OPEN, db_index=True)
    summary = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    # Soft references to users.User
    requested_by_id = models.IntegerField(db_index=True)
    requested_by_name = models.CharField(max_length=100, blank=True, default='')
    assignee_id = models.IntegerField(null=True, blank=True, db_index=True)
    assignee_name = models.CharField(max_length=100, blank=True, default='')
    assigned_at = models.DateTimeField(null=True, blank=True)
    assigned_by_id = models.IntegerField(null=True, blank=True)
    # Soft reference to maintenance.MaintenancePlan
    maintenance_plan_id = models.IntegerField(null=True, blank=True, db_index=True)
    # Correlation with workorder.requested events
    request_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    planned_start = models.DateTimeField(null=True, blank=True)
    planned_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    failure_code = models.CharField(max_length=50, blank=True, null=True)
    root_cause = models.TextField(blank=True, null=True)
    actions_taken = models.TextField(blank=True, null=True)
    checklist = models.JSONField(default=list, blank=True)
    downtime_minutes = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    labor_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    completed_by_id = models.IntegerField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    closed_by_id = models.IntegerField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    attachments = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'work_orders'
        verbose_name = 'Work Order'
        verbose_name_plural = 'Work Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['equipment', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['wo_type', 'status']),
            models.Index(fields=['assignee_id', 'status']),
            models.Index(fields=['priority', 'status']),
        ]

    def __str__(self):
        return f"{self.wo_code} - {self.summary}"

    def save(self, *args, **kwargs):
        if not self.wo_code:
            self.wo_code = generate_wo_code()
        if self.equipment and not (self.equipment_code and self.equipment_name):
            projection = AssetProjection.objects.filter(pk=self.equipment).first()
            if projection:
                self.equipment_code = self.equipment_code or projection.code
                self.equipment_name = self.equipment_name or projection.name
        self.total_cost = self.parts_cost
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.planned_end and self.status not in [WorkOrderStatus.COMPLETED, WorkOrderStatus.CLOSED, WorkOrderStatus.CANCELED]:
            return timezone.now() > self.planned_end
        return False

    @property
    def duration_hours(self):
        if self.actual_start and self.actual_end:
            return (self.actual_end - self.actual_start).total_seconds() / 3600
        return 0

    def can_be_assigned(self):
        return self.status == WorkOrderStatus.OPEN

    def can_be_started(self):
        return self.status in [WorkOrderStatus.ASSIGNED, WorkOrderStatus.OPEN]

    def can_be_completed(self):
        return self.status == WorkOrderStatus.IN_PROGRESS

    def can_be_closed(self):
        return self.status == WorkOrderStatus.COMPLETED


class WorkOrderComment(models.Model):
    id = models.BigAutoField(primary_key=True)
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='comments')
    author_id = models.IntegerField(db_index=True)
    author_name = models.CharField(max_length=100, blank=True, default='')
    comment = models.TextField()
    is_internal = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'work_order_comments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.work_order.wo_code} - {self.author_name} - {self.created_at}"


class WorkOrderPart(models.Model):
    id = models.BigAutoField(primary_key=True)
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='parts_used')
    part_code = models.CharField(max_length=50)
    part_name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit = models.CharField(max_length=20, blank=True, null=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        db_table = 'work_order_parts'
        ordering = ['part_code']

    def __str__(self):
        return f"{self.work_order.wo_code} - {self.part_name} x{self.quantity}"

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)
