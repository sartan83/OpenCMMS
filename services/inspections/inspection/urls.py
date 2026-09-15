from rest_framework.routers import DefaultRouter

from .views import (
    InspectionRecordViewSet,
    InspectionRouteViewSet,
    InspectionTemplateViewSet,
)

router = DefaultRouter()
router.register('templates', InspectionTemplateViewSet, basename='inspection-template')
router.register('routes', InspectionRouteViewSet, basename='inspection-route')
router.register('', InspectionRecordViewSet, basename='inspection-record')
urlpatterns = router.urls
