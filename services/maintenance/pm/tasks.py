from celery import shared_task
from django.utils import timezone

from .events import request_work_order
from .models import MaintenancePlan, TriggerType


@shared_task(name='pm.tasks.evaluate_plan_triggers')
def evaluate_plan_triggers(current_date=None):
    current_date = current_date or timezone.now().date()
    count = 0
    for plan in MaintenancePlan.objects.filter(
        is_active=True,
        trigger_type=TriggerType.TIME,
    ):
        if plan.check_should_generate(current_date=current_date):
            request_work_order(plan)
            plan.last_generated_date = current_date
            plan.save(update_fields=['last_generated_date', 'updated_at'])
            count += 1
    return count
