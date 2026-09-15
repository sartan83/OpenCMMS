from datetime import timedelta

import pytest
from django.utils import timezone

from pm.models import MaintenancePlan
from pm.tasks import evaluate_plan_triggers


@pytest.mark.django_db
def test_evaluate_time_triggers(asset, bus):
    plan = MaintenancePlan.objects.create(
        code='PM-TASK',
        equipment_id=asset.asset_id,
        equipment_code=asset.code,
        equipment_name=asset.name,
        title='Daily',
        frequency_value=1,
        frequency_unit='day',
        last_generated_date=timezone.now().date() - timedelta(days=2),
        created_by_id=1,
    )
    assert evaluate_plan_triggers() == 1
    plan.refresh_from_db()
    assert plan.last_generated_date == timezone.now().date()
    assert len([event for event in bus.published if event.type == 'workorder.requested']) == 1
    assert evaluate_plan_triggers() == 0
