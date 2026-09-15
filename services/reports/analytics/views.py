from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ReportRun, ScheduledReport
from .reports import REPORT_BUILDERS, filters_from_params
from .serializers import ReportRunSerializer, ScheduledReportSerializer


class ReportBuilderView(APIView):
    report_type = None

    def get(self, request, *args, **kwargs):
        return Response(REPORT_BUILDERS[self.report_type](filters_from_params(request.query_params)))


class WorkOrderReportView(ReportBuilderView):
    report_type = 'workorder_summary'


class DowntimeReportView(ReportBuilderView):
    report_type = 'downtime_analysis'


class SparePartsUsageReportView(ReportBuilderView):
    report_type = 'spareparts_usage'


class GenericReportView(ReportBuilderView):
    def get(self, request, slug, *args, **kwargs):
        builder = REPORT_BUILDERS.get(slug)
        if builder is None:
            return Response({'detail': 'Unknown report type'}, status=status.HTTP_404_NOT_FOUND)
        return Response(builder(filters_from_params(request.query_params)))


class RunReportView(APIView):
    def get(self, request, *args, **kwargs):
        report_type = request.query_params.get('type')
        builder = REPORT_BUILDERS.get(report_type)
        if builder is None:
            return Response(
                {'detail': 'A valid report type is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        filters = filters_from_params(request.query_params)
        started_at = timezone.now()
        report_run = ReportRun.objects.create(
            report_type=report_type,
            parameters=dict(request.query_params.lists()),
            status='running',
            requested_by_id=getattr(request.user, 'id', None),
            requested_by_name=getattr(request.user, 'full_name', ''),
            started_at=started_at,
        )
        try:
            result = builder(filters)
        except Exception as error:
            report_run.status = 'failed'
            report_run.error_message = str(error)
            report_run.completed_at = timezone.now()
            report_run.save(update_fields=['status', 'error_message', 'completed_at'])
            return Response(
                {'detail': 'Report generation failed', 'error': str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        report_run.status = 'completed'
        report_run.result_data = result
        report_run.completed_at = timezone.now()
        report_run.save(update_fields=['status', 'result_data', 'completed_at'])
        return Response(result)


class ScheduledReportViewSet(viewsets.ModelViewSet):
    queryset = ScheduledReport.objects.all()
    serializer_class = ScheduledReportSerializer

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(
            created_by_id=user.id,
            created_by_name=getattr(user, 'full_name', '') or user.username,
        )


class ReportRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReportRun.objects.all()
    serializer_class = ReportRunSerializer
