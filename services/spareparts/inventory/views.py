"""
Views for Spare Parts app
"""
from decimal import Decimal, InvalidOperation

from django.db import models, transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cmms_common.audit import audit_log

from .events import publish_part_consumed
from .models import PartTransaction, SparePart
from .serializers import PartTransactionSerializer, SparePartSerializer


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
        queryset = super().get_queryset()
        if self.request.query_params.get('low_stock') == 'true':
            queryset = queryset.filter(current_stock__lte=models.F('min_stock'))
        return queryset

    def perform_create(self, serializer):
        serializer.save(
            created_by_id=self.request.user.id,
            created_by_name=self.request.user.full_name,
        )

    def _quantity(self, request):
        try:
            quantity = Decimal(str(request.data.get('quantity', 0)))
        except InvalidOperation:
            return None
        if quantity <= 0:
            return None
        return quantity

    def _related_work_order(self, request):
        value = request.data.get('related_work_order')
        if value in (None, ''):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _stock_movement(self, request, pk, transaction_type):
        quantity = self._quantity(request)
        if quantity is None:
            return Response(
                {'error': 'Quantity must be greater than 0'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        related_work_order = self._related_work_order(request)
        spare_part = self.get_object()
        with transaction.atomic():
            spare_part = SparePart.objects.select_for_update().get(pk=spare_part.pk)
            stock_before = spare_part.current_stock
            if transaction_type == 'out' and stock_before < quantity:
                return Response(
                    {'error': 'Insufficient stock'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if transaction_type == 'in':
                spare_part.current_stock += quantity
            else:
                spare_part.current_stock -= quantity
            spare_part.save()
            txn = PartTransaction.objects.create(
                part=spare_part,
                transaction_type=transaction_type,
                quantity=quantity,
                stock_before=stock_before,
                stock_after=spare_part.current_stock,
                related_work_order=related_work_order,
                reference=request.data.get('reference', ''),
                remark=request.data.get('notes', ''),
                operator_id=request.user.id,
                operator_name=request.user.full_name,
            )

        audit_log(
            actor=request.user,
            action=f'stock_{transaction_type}',
            entity_type='SparePart',
            entity_id=spare_part.id,
            entity_repr=str(spare_part),
            diff={
                'quantity': str(quantity),
                'stock_before': str(stock_before),
                'stock_after': str(spare_part.current_stock),
            },
            service='spareparts',
        )
        if transaction_type == 'out':
            publish_part_consumed(txn, spare_part, request.user.id)
        return Response(SparePartSerializer(spare_part).data)

    @action(detail=True, methods=['post'])
    def stock_in(self, request, pk=None):
        return self._stock_movement(request, pk, 'in')

    @action(detail=True, methods=['post'], url_path='stock-in', url_name='stock-in-hyphen')
    def stock_in_hyphen(self, request, pk=None):
        return self.stock_in(request, pk)

    @action(detail=True, methods=['post'])
    def stock_out(self, request, pk=None):
        return self._stock_movement(request, pk, 'out')

    @action(detail=True, methods=['post'], url_path='stock-out', url_name='stock-out-hyphen')
    def stock_out_hyphen(self, request, pk=None):
        return self.stock_out(request, pk)


class PartTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PartTransaction.objects.select_related('part')
    serializer_class = PartTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['part', 'related_work_order', 'transaction_type']
    ordering_fields = ['created_at', 'quantity', 'stock_before', 'stock_after']
    ordering = ['-created_at']
