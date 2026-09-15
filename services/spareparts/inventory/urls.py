from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PartTransactionViewSet, SparePartViewSet

router = DefaultRouter()
router.register(r'transactions', PartTransactionViewSet, basename='parttransaction')
router.register(r'', SparePartViewSet, basename='sparepart')

urlpatterns = [path('', include(router.urls))]
