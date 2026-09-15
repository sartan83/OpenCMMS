"""
URL configuration for Maintenance app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MaintenancePlanViewSet, WorkOrderTemplateViewSet


router = DefaultRouter()
router.register(r'plans', MaintenancePlanViewSet, basename='maintenanceplan')
router.register(r'templates', WorkOrderTemplateViewSet, basename='workordertemplate')

urlpatterns = [
    path('', include(router.urls)),
]
