from django.contrib import admin

from .models import AssetProjection, MaintenancePlan, ProcessedEvent, WorkOrderRequest, WorkOrderTemplate

admin.site.register([MaintenancePlan, WorkOrderTemplate, AssetProjection, WorkOrderRequest, ProcessedEvent])
