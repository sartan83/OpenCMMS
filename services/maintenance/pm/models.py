"""Maintenance plan and work-order request models."""
import uuid

from django.db import models
from django.core.validators import MinValueValidator


class TriggerType(models.TextChoices):
    """Maintenance trigger types"""
    TIME = 'time', 'Time Based'
    COUNTER = 'counter', 'Counter Based'


class FrequencyUnit(models.TextChoices):
    """Frequency units for time-based maintenance"""
    DAY = 'day', 'Day(s)'
    WEEK = 'week', 'Week(s)'
    MONTH = 'month', 'Month(s)'
    QUARTER = 'quarter', 'Quarter(s)'
    YEAR = 'year', 'Year(s)'


class MaintenancePlan(models.Model):
    """
    Maintenance Plan - defines schedules for preventive maintenance
    Can be time-based or counter-based (meter reading)
    """
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='Plan Code',
        help_text='Unique maintenance plan code'
    )
    equipment_id = models.IntegerField(
        db_index=True,
    )
    equipment_code = models.CharField(max_length=50, blank=True, default='')
    equipment_name = models.CharField(max_length=200, blank=True, default='')
    title = models.CharField(
        max_length=200,
        verbose_name='Title'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Description'
    )
    trigger_type = models.CharField(
        max_length=20,
        choices=TriggerType.choices,
        default=TriggerType.TIME,
        verbose_name='Trigger Type'
    )
    # Time-based fields
    frequency_value = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name='Frequency Value',
        help_text='Number of time units between maintenance'
    )
    frequency_unit = models.CharField(
        max_length=20,
        choices=FrequencyUnit.choices,
        null=True,
        blank=True,
        verbose_name='Frequency Unit'
    )
    # Counter-based fields
    counter_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Counter Name',
        help_text='Name of the counter (e.g., Running Hours, Production Count)'
    )
    counter_threshold = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Counter Threshold',
        help_text='Counter value threshold to trigger maintenance'
    )
    # Checklist template - JSON array of checklist items
    checklist_template = models.JSONField(
        default=list,
        verbose_name='Checklist Template',
        help_text='JSON array of checklist items for this maintenance plan'
    )
    # Estimated resources
    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Estimated Hours'
    )
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Estimated Cost'
    )
    required_skills = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Required Skills'
    )
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        default='medium',
        verbose_name='Priority'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active',
        help_text='Whether this plan is currently active'
    )
    last_generated_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Last Generated Date',
        help_text='Last date a work order was generated from this plan'
    )
    last_counter_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Last Counter Value',
        help_text='Last counter value when work order was generated'
    )
    created_by_id = models.IntegerField()
    created_by_name = models.CharField(max_length=150, blank=True, default='')
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    class Meta:
        db_table = 'maintenance_plans'
        verbose_name = 'Maintenance Plan'
        verbose_name_plural = 'Maintenance Plans'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['equipment_id', 'is_active']),
            models.Index(fields=['trigger_type']),
        ]

    def __str__(self):
        return f"{self.code} - {self.title} ({self.equipment_code})"

    def check_should_generate(self, current_date=None, current_counter=None):
        """
        Check if a work order should be generated based on the plan

        Args:
            current_date: Current date for time-based plans
            current_counter: Current counter value for counter-based plans

        Returns:
            bool: True if work order should be generated
        """
        if not self.is_active:
            return False

        if self.trigger_type == TriggerType.TIME:
            if not current_date:
                from django.utils import timezone
                current_date = timezone.now().date()

            if not self.last_generated_date:
                return True

            from datetime import timedelta
            from dateutil.relativedelta import relativedelta

            # Calculate next due date based on frequency
            if self.frequency_unit == FrequencyUnit.DAY:
                next_due = self.last_generated_date + timedelta(days=self.frequency_value)
            elif self.frequency_unit == FrequencyUnit.WEEK:
                next_due = self.last_generated_date + timedelta(weeks=self.frequency_value)
            elif self.frequency_unit == FrequencyUnit.MONTH:
                next_due = self.last_generated_date + relativedelta(months=self.frequency_value)
            elif self.frequency_unit == FrequencyUnit.QUARTER:
                next_due = self.last_generated_date + relativedelta(months=self.frequency_value * 3)
            elif self.frequency_unit == FrequencyUnit.YEAR:
                next_due = self.last_generated_date + relativedelta(years=self.frequency_value)
            else:
                return False

            return current_date >= next_due

        elif self.trigger_type == TriggerType.COUNTER:
            if current_counter is None or self.counter_threshold is None:
                return False

            if self.last_counter_value is None:
                return current_counter >= self.counter_threshold

            # Generate if counter has increased by threshold amount since last generation
            counter_delta = current_counter - self.last_counter_value
            return counter_delta >= self.counter_threshold

        return False


class WorkOrderTemplate(models.Model):
    """
    Work Order Template - reusable template for common maintenance tasks
    """
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Template Code'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Template Name'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Description'
    )
    work_order_type = models.CharField(
        max_length=20,
        choices=[
            ('PM', 'Preventive Maintenance'),
            ('CM', 'Corrective Maintenance'),
            ('inspection', 'Inspection'),
        ],
        default='PM',
        verbose_name='Work Order Type'
    )
    checklist_template = models.JSONField(
        default=list,
        verbose_name='Checklist Template'
    )
    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Estimated Hours'
    )
    required_skills = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Required Skills'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    class Meta:
        db_table = 'work_order_templates'
        verbose_name = 'Work Order Template'
        verbose_name_plural = 'Work Order Templates'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class AssetProjection(models.Model):
    asset_id = models.IntegerField(primary_key=True)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20)
    process = models.CharField(max_length=100, blank=True, default='')
    factory = models.CharField(max_length=100, blank=True, default='')
    workshop = models.CharField(max_length=100, blank=True, default='')
    line = models.CharField(max_length=100, blank=True, default='')
    station = models.CharField(max_length=100, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'asset_projections'


class WorkOrderRequest(models.Model):
    request_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(
        MaintenancePlan,
        on_delete=models.CASCADE,
        related_name='work_order_requests',
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('fulfilled', 'Fulfilled')],
        default='pending',
    )
    work_order_id = models.IntegerField(null=True)
    wo_code = models.CharField(max_length=50, blank=True, default='')
    requested_by_id = models.IntegerField(null=True)
    fulfilled_at = models.DateTimeField(null=True)


class ProcessedEvent(models.Model):
    event_id = models.CharField(max_length=64, primary_key=True)
    event_type = models.CharField(max_length=100)
    processed_at = models.DateTimeField(auto_now_add=True)
