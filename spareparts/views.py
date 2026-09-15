"""
Views for Spare Parts app
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import models

from cmms_common.audit import audit_log
from .models import SparePart, PartTransaction
from .serializers import SparePartSerializer, PartTransactionSerializer


class SparePartViewSet(viewsets.ModelViewSet):
    """ViewSet for SparePart model"""
    queryset = SparePart.objects.all()
    serializer_class = SparePartSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'supplier']
    search_fields = ['part_code', 'name', 'description']
    ordering_fields = ['part_code', 'name', 'current_stock']
    ordering = ['part_code']

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter for low stock items
        low_stock = self.request.query_params.get('low_stock')
        if low_stock == 'true':
            queryset = queryset.filter(current_stock__lte=models.F('min_stock'))
        
        return queryset

    def perform_create(self, serializer):
        """Set created_by on create"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def stock_in(self, request, pk=None):
        """Add stock to spare part"""
        spare_part = self.get_object()
        quantity = request.data.get('quantity', 0)
        
        if quantity <= 0:
            return Response(
                {"error": "Quantity must be greater than 0"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        stock_before = spare_part.current_stock
        spare_part.current_stock += quantity
        spare_part.save()
        
        # Create transaction record
        PartTransaction.objects.create(
            part=spare_part,
            transaction_type='in',
            quantity=quantity,
            stock_before=stock_before,
            stock_after=spare_part.current_stock,
            reference=request.data.get('reference', ''),
            remark=request.data.get('notes', ''),
            operator=request.user,
        )
        audit_log(
            actor=request.user,
            action='stock_in',
            entity_type='SparePart',
            entity_id=spare_part.id,
            entity_repr=str(spare_part),
            diff={'quantity': quantity, 'stock_before': stock_before, 'stock_after': spare_part.current_stock},
        )
        
        return Response(SparePartSerializer(spare_part).data)

    @action(detail=True, methods=['post'])
    def stock_out(self, request, pk=None):
        """Remove stock from spare part"""
        spare_part = self.get_object()
        quantity = request.data.get('quantity', 0)
        
        if quantity <= 0:
            return Response(
                {"error": "Quantity must be greater than 0"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if spare_part.current_stock < quantity:
            return Response(
                {"error": "Insufficient stock"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        stock_before = spare_part.current_stock
        spare_part.current_stock -= quantity
        spare_part.save()
        
        # Create transaction record
        PartTransaction.objects.create(
            part=spare_part,
            transaction_type='out',
            quantity=quantity,
            stock_before=stock_before,
            stock_after=spare_part.current_stock,
            reference=request.data.get('reference', ''),
            remark=request.data.get('notes', ''),
            operator=request.user,
        )
        audit_log(
            actor=request.user,
            action='stock_out',
            entity_type='SparePart',
            entity_id=spare_part.id,
            entity_repr=str(spare_part),
            diff={'quantity': quantity, 'stock_before': stock_before, 'stock_after': spare_part.current_stock},
        )
        
        return Response(SparePartSerializer(spare_part).data)
