from rest_framework.routers import DefaultRouter

from .views import AuditEntryViewSet

router = DefaultRouter()
router.register('entries', AuditEntryViewSet, basename='audit-entry')
urlpatterns = router.urls
