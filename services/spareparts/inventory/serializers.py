"""
Serializers for Spare Parts app
"""
from rest_framework import serializers

from .models import PartTransaction, SparePart


class SparePartSerializer(serializers.ModelSerializer):
    """Serializer for SparePart model"""
    is_below_min_stock = serializers.BooleanField(read_only=True)
    stock_status = serializers.CharField(read_only=True)
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = SparePart
        fields = ['id', 'part_code', 'name', 'description', 'spec', 'category',
                  'unit', 'current_stock', 'min_stock', 'safety_stock', 'max_stock',
                  'unit_cost', 'average_cost', 'supplier', 'supplier_part_code', 'location',
                  'reorder_quantity', 'lead_time_days', 'lifecycle_status',
                  'notes', 'created_at', 'updated_at', 'is_below_min_stock',
                  'stock_status', 'total_value']
        read_only_fields = ['id', 'created_at', 'updated_at',
                            'is_below_min_stock', 'stock_status', 'total_value']


class PartTransactionSerializer(serializers.ModelSerializer):
    """Serializer for PartTransaction model"""
    part_code = serializers.CharField(source='part.part_code', read_only=True)
    part_name = serializers.CharField(source='part.name', read_only=True)
    operator = serializers.IntegerField(source='operator_id', read_only=True)

    class Meta:
        model = PartTransaction
        fields = ['id', 'part', 'part_code', 'part_name',
                  'transaction_type', 'quantity', 'stock_before', 'stock_after',
                  'related_work_order', 'reference', 'operator', 'operator_name',
                  'remark', 'created_at']
        read_only_fields = ['id', 'part_code', 'part_name', 'operator', 'operator_name', 'created_at']
