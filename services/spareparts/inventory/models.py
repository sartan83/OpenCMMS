"""
Spare Parts models for CMMS
Inventory management and tracking
"""
from django.db import models
from django.core.validators import MinValueValidator


class TransactionType(models.TextChoices):
    """Transaction types for inventory movements"""
    IN = 'in', 'Stock In'
    OUT = 'out', 'Stock Out'
    ADJUST = 'adjust', 'Adjustment'


class SparePart(models.Model):
    """
    Spare Part - inventory item for maintenance
    Tracks stock levels, locations, and reordering information
    """
    id = models.BigAutoField(primary_key=True)
    part_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='Part Code',
        help_text='Unique part code/SKU'
    )
    name = models.CharField(max_length=200, verbose_name='Part Name')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    spec = models.CharField(max_length=200, blank=True, null=True, verbose_name='Specification')
    category = models.CharField(max_length=50, blank=True, null=True, verbose_name='Category')
    unit = models.CharField(
        max_length=20,
        verbose_name='Unit',
        help_text='Unit of measurement (e.g., pcs, kg, m)'
    )
    manufacturer = models.CharField(max_length=100, blank=True, null=True, verbose_name='Manufacturer')
    supplier = models.CharField(max_length=100, blank=True, null=True, verbose_name='Supplier')
    supplier_part_code = models.CharField(
        max_length=50, blank=True, null=True, verbose_name='Supplier Part Code'
    )
    current_stock = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(0)], verbose_name='Current Stock'
    )
    safety_stock = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(0)], verbose_name='Safety Stock',
        help_text='Minimum stock level to prevent stockout'
    )
    min_stock = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(0)], verbose_name='Min Stock',
        help_text='Reorder point - trigger reorder when below this level'
    )
    max_stock = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)], verbose_name='Max Stock',
        help_text='Maximum stock level to avoid overstocking'
    )
    reorder_quantity = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)], verbose_name='Reorder Quantity'
    )
    location = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='Storage Location',
        help_text='Warehouse/bin location'
    )
    shelf = models.CharField(max_length=50, blank=True, null=True, verbose_name='Shelf/Bin')
    unit_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)], verbose_name='Unit Cost'
    )
    average_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)], verbose_name='Average Cost'
    )
    compatible_equipment = models.JSONField(
        default=list, blank=True, verbose_name='Compatible Equipment',
        help_text='List of equipment codes this part is compatible with'
    )
    alternative_parts = models.JSONField(
        default=list, blank=True, verbose_name='Alternative Parts',
        help_text='List of alternative part codes'
    )
    lead_time_days = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Lead Time (Days)',
        help_text='Days from order to delivery'
    )
    lifecycle_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('obsolete', 'Obsolete'),
            ('discontinued', 'Discontinued'),
        ],
        default='active',
        verbose_name='Lifecycle Status'
    )
    notes = models.TextField(blank=True, null=True, verbose_name='Notes')
    created_by_id = models.IntegerField(db_index=True)
    created_by_name = models.CharField(max_length=150, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        db_table = 'spare_parts'
        verbose_name = 'Spare Part'
        verbose_name_plural = 'Spare Parts'
        ordering = ['part_code']
        indexes = [
            models.Index(fields=['part_code']),
            models.Index(fields=['category']),
            models.Index(fields=['lifecycle_status']),
        ]

    def __str__(self):
        return f"{self.part_code} - {self.name}"

    @property
    def is_below_min_stock(self):
        """Check if stock is below minimum level"""
        return self.current_stock <= self.min_stock

    @property
    def is_below_safety_stock(self):
        """Check if stock is below safety stock level"""
        return self.current_stock <= self.safety_stock

    @property
    def stock_status(self):
        """Get stock status indicator"""
        if self.current_stock <= self.min_stock:
            return 'critical'
        elif self.current_stock <= self.safety_stock:
            return 'warning'
        else:
            return 'ok'

    @property
    def total_value(self):
        """Calculate total inventory value"""
        if self.average_cost:
            return self.current_stock * self.average_cost
        elif self.unit_cost:
            return self.current_stock * self.unit_cost
        return 0


class PartTransaction(models.Model):
    """
    Part Transaction - tracks all inventory movements
    Records stock in, stock out, and adjustments
    """
    id = models.BigAutoField(primary_key=True)
    part = models.ForeignKey(
        SparePart, on_delete=models.PROTECT, related_name='transactions', verbose_name='Part'
    )
    transaction_type = models.CharField(
        max_length=20, choices=TransactionType.choices, verbose_name='Transaction Type'
    )
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='Quantity',
        help_text='Positive value. Direction determined by transaction type.'
    )
    stock_before = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Stock Before')
    stock_after = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Stock After')
    related_work_order = models.IntegerField(null=True, blank=True, db_index=True)
    reference = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='Reference',
        help_text='PO number, invoice number, or other reference'
    )
    operator_id = models.IntegerField(db_index=True)
    operator_name = models.CharField(max_length=150, blank=True, default='')
    remark = models.TextField(blank=True, null=True, verbose_name='Remark')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At', db_index=True)

    class Meta:
        db_table = 'part_transactions'
        verbose_name = 'Part Transaction'
        verbose_name_plural = 'Part Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['part', 'created_at']),
            models.Index(fields=['transaction_type', 'created_at']),
        ]

    def __str__(self):
        return (
            f"{self.part.part_code} - {self.get_transaction_type_display()} - "
            f"{self.quantity} - {self.created_at}"
        )


class PurchaseRequest(models.Model):
    """
    Purchase Request - for requesting spare parts procurement
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('canceled', 'Canceled'),
    ]

    id = models.BigAutoField(primary_key=True)
    pr_code = models.CharField(max_length=50, unique=True, verbose_name='PR Code')
    part = models.ForeignKey(
        SparePart, on_delete=models.PROTECT, related_name='purchase_requests', verbose_name='Part'
    )
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)],
        verbose_name='Quantity'
    )
    urgency = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        default='medium',
        verbose_name='Urgency'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Status'
    )
    reason = models.TextField(blank=True, null=True, verbose_name='Reason')
    requested_by_id = models.IntegerField(db_index=True)
    requested_by_name = models.CharField(max_length=150, blank=True, default='')
    approved_by_id = models.IntegerField(null=True, blank=True)
    approved_by_name = models.CharField(max_length=150, blank=True, default='')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Approved At')
    expected_delivery_date = models.DateField(null=True, blank=True, verbose_name='Expected Delivery Date')
    actual_delivery_date = models.DateField(null=True, blank=True, verbose_name='Actual Delivery Date')
    notes = models.TextField(blank=True, null=True, verbose_name='Notes')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        db_table = 'purchase_requests'
        verbose_name = 'Purchase Request'
        verbose_name_plural = 'Purchase Requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.pr_code} - {self.part.name}"
