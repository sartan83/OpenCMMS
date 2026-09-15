from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    DowntimeReportView,
    GenericReportView,
    ReportRunViewSet,
    RunReportView,
    ScheduledReportViewSet,
    SparePartsUsageReportView,
    WorkOrderReportView,
)

router = DefaultRouter()
router.register('scheduled', ScheduledReportViewSet, basename='scheduled-report')
router.register('runs', ReportRunViewSet, basename='report-run')

urlpatterns = [
    path('workorders/', WorkOrderReportView.as_view(), name='workorder-report'),
    path('downtime/', DowntimeReportView.as_view(), name='downtime-report'),
    path('spareparts-usage/', SparePartsUsageReportView.as_view(), name='spareparts-usage-report'),
    path('run/', RunReportView.as_view(), name='run-report'),
    *router.urls,
    path('<slug:slug>/', GenericReportView.as_view(), name='generic-report'),
]
