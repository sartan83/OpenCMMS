from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from django.db.models import QuerySet

from .models import (
    AssetProjection,
    InspectionFact,
    PartConsumptionFact,
    WorkOrderFact,
)
from .serializers import PartConsumptionFactSerializer, WorkOrderFactSerializer


@dataclass(frozen=True)
class ReportFilters:
    date_from: date | None = None
    date_to: date | None = None
    asset_id: int | None = None
    wo_type: str | None = None
    status: str | None = None


def filters_from_params(params) -> ReportFilters:
    def parse_date(value):
        try:
            return date.fromisoformat(value) if value else None
        except (TypeError, ValueError):
            return None

    try:
        asset_id = int(params.get('asset_id')) if params.get('asset_id') else None
    except (TypeError, ValueError):
        asset_id = None
    return ReportFilters(
        date_from=parse_date(params.get('date_from')),
        date_to=parse_date(params.get('date_to')),
        asset_id=asset_id,
        wo_type=params.get('wo_type') or None,
        status=params.get('status') or None,
    )


def _filter_dates(queryset: QuerySet, field: str, filters: ReportFilters):
    if filters.date_from:
        queryset = queryset.filter(**{f'{field}__date__gte': filters.date_from})
    if filters.date_to:
        queryset = queryset.filter(**{f'{field}__date__lte': filters.date_to})
    return queryset


def _workorders(filters):
    queryset = _filter_dates(WorkOrderFact.objects.all(), 'created_at', filters)
    if filters.asset_id is not None:
        queryset = queryset.filter(asset_id=filters.asset_id)
    if filters.wo_type:
        queryset = queryset.filter(wo_type=filters.wo_type)
    if filters.status:
        queryset = queryset.filter(status=filters.status)
    return queryset


def _parts(filters):
    queryset = _filter_dates(PartConsumptionFact.objects.all(), 'occurred_at', filters)
    if filters.asset_id is not None or filters.wo_type or filters.status:
        workorder_filters = ReportFilters(
            asset_id=filters.asset_id,
            wo_type=filters.wo_type,
            status=filters.status,
        )
        queryset = queryset.filter(
            work_order_id__in=_workorders(workorder_filters).values('work_order_id')
        )
    return queryset


def _decimal_string(value):
    return str(Decimal(str(value or 0)).quantize(Decimal('0.01')))


def _workorder_item(fact):
    return WorkOrderFactSerializer(fact).data


def _part_item(fact):
    return PartConsumptionFactSerializer(fact).data


def build_workorder_summary(filters: ReportFilters) -> dict:
    facts = list(_workorders(filters).order_by('-created_at', '-updated_at'))
    status_counts = Counter(f.status for f in facts)
    type_counts = Counter(f.wo_type for f in facts)
    priority_counts = Counter(f.priority for f in facts if f.priority)
    completed = [f for f in facts if f.status in {'completed', 'closed'}]
    now = datetime.now(timezone.utc)
    overdue = [
        f for f in facts
        if f.planned_end and f.planned_end < now
        and f.status not in {'completed', 'closed', 'canceled'}
    ]
    completion_hours = []
    for fact in completed:
        start = fact.actual_start or fact.created_at
        if start and fact.completed_at:
            completion_hours.append((fact.completed_at - start).total_seconds() / 3600)
    return {
        'total': len(facts),
        'by_status': dict(status_counts),
        'by_type': dict(type_counts),
        'by_priority': dict(priority_counts),
        'completed': len(completed),
        'overdue': len(overdue),
        'avg_completion_hours': (
            sum(completion_hours) / len(completion_hours)
            if completion_hours else None
        ),
        'total_cost': _decimal_string(sum((f.total_cost for f in facts), Decimal('0'))),
        'items': [_workorder_item(fact) for fact in facts[:100]],
    }


def build_downtime_analysis(filters: ReportFilters) -> dict:
    facts = list(_workorders(filters).order_by('-created_at', '-updated_at'))
    grouped = defaultdict(lambda: {
        'asset_id': 0, 'asset_code': '', 'asset_name': '',
        'downtime_minutes': 0, 'work_order_count': 0,
    })
    for fact in facts:
        item = grouped[fact.asset_id]
        item['asset_id'] = fact.asset_id
        item['asset_code'] = fact.asset_code or ''
        item['asset_name'] = fact.asset_name or ''
        item['downtime_minutes'] += fact.downtime_minutes or 0
        item['work_order_count'] += 1
    by_asset = sorted(grouped.values(), key=lambda item: item['downtime_minutes'], reverse=True)
    return {
        'total_downtime_minutes': sum(item['downtime_minutes'] for item in by_asset),
        'by_asset': by_asset,
        'items': [_workorder_item(fact) for fact in facts],
    }


def build_spareparts_usage(filters: ReportFilters) -> dict:
    facts = list(_parts(filters).order_by('-occurred_at'))
    grouped = defaultdict(lambda: {
        'part_id': 0, 'part_code': '', 'quantity': Decimal('0'),
        'total_cost': Decimal('0'), 'transaction_count': 0,
    })
    for fact in facts:
        item = grouped[fact.part_id]
        item['part_id'] = fact.part_id
        item['part_code'] = fact.part_code
        item['quantity'] += fact.quantity
        item['total_cost'] += fact.total_cost or Decimal('0')
        item['transaction_count'] += 1
    by_part = sorted(
        (
            {
                **item,
                'quantity': _decimal_string(item['quantity']),
                'total_cost': _decimal_string(item['total_cost']),
            }
            for item in grouped.values()
        ),
        key=lambda item: Decimal(item['total_cost']),
        reverse=True,
    )
    return {
        'total_quantity': _decimal_string(sum((f.quantity for f in facts), Decimal('0'))),
        'total_cost': _decimal_string(sum((f.total_cost or 0 for f in facts), Decimal('0'))),
        'by_part': by_part,
        'items': [_part_item(fact) for fact in facts],
    }


def build_maintenance_compliance(filters: ReportFilters) -> dict:
    facts = list(_workorders(filters).filter(wo_type='PM'))
    completed_on_time = []
    late = []
    by_plan = defaultdict(lambda: {'plan_id': None, 'total': 0, 'completed_on_time': 0, 'late': 0})
    for fact in facts:
        plan = by_plan[fact.maintenance_plan_id]
        plan['plan_id'] = fact.maintenance_plan_id
        plan['total'] += 1
        if fact.completed_at and (not fact.planned_end or fact.completed_at <= fact.planned_end):
            completed_on_time.append(fact)
            plan['completed_on_time'] += 1
        elif fact.completed_at and fact.planned_end and fact.completed_at > fact.planned_end:
            late.append(fact)
            plan['late'] += 1
    total = len(facts)
    return {
        'total': total,
        'completed_on_time': len(completed_on_time),
        'late': len(late),
        'compliance_rate': len(completed_on_time) / total if total else 0,
        'by_plan': list(by_plan.values()),
    }


def build_cost_analysis(filters: ReportFilters) -> dict:
    facts = list(_workorders(filters))
    parts = list(_parts(filters))
    by_type = defaultdict(lambda: {'parts_cost': Decimal('0'), 'labor_hours': Decimal('0'), 'total_cost': Decimal('0')})
    by_asset = defaultdict(lambda: {'asset_id': 0, 'asset_code': '', 'asset_name': '', 'total_cost': Decimal('0'), 'work_order_count': 0})
    by_month = defaultdict(lambda: {'parts_cost': Decimal('0'), 'labor_hours': Decimal('0'), 'total_cost': Decimal('0')})
    for fact in facts:
        type_item = by_type[fact.wo_type]
        type_item['parts_cost'] += fact.parts_cost or 0
        type_item['labor_hours'] += fact.labor_hours or 0
        type_item['total_cost'] += fact.total_cost or 0
        asset_item = by_asset[fact.asset_id]
        asset_item.update({
            'asset_id': fact.asset_id,
            'asset_code': fact.asset_code or '',
            'asset_name': fact.asset_name or '',
        })
        asset_item['total_cost'] += fact.total_cost or 0
        asset_item['work_order_count'] += 1
        if fact.created_at:
            month = by_month[fact.created_at.strftime('%Y-%m')]
            month['parts_cost'] += fact.parts_cost or 0
            month['labor_hours'] += fact.labor_hours or 0
            month['total_cost'] += fact.total_cost or 0
    total_parts = sum((fact.total_cost or 0 for fact in parts), Decimal('0'))
    return {
        'parts_cost': _decimal_string(sum((f.parts_cost or 0 for f in facts), Decimal('0'))),
        'labor_hours': _decimal_string(sum((f.labor_hours or 0 for f in facts), Decimal('0'))),
        'total_cost': _decimal_string(sum((f.total_cost or 0 for f in facts), Decimal('0'))),
        'parts_consumption_total': _decimal_string(total_parts),
        'by_type': [
            {'wo_type': key, **{name: _decimal_string(value) for name, value in item.items()}}
            for key, item in by_type.items()
        ],
        'by_asset': [
            {**item, 'total_cost': _decimal_string(item['total_cost'])}
            for item in sorted(by_asset.values(), key=lambda item: item['total_cost'], reverse=True)[:20]
        ],
        'by_month': [
            {'month': key, **{name: _decimal_string(value) for name, value in item.items()}}
            for key, item in sorted(by_month.items())
        ],
    }


def build_technician_performance(filters: ReportFilters) -> dict:
    facts = list(_workorders(filters).exclude(assignee_id__isnull=True))
    grouped = defaultdict(lambda: {
        'assignee_id': None, 'assignee_name': '', 'assigned': 0, 'completed': 0,
        'avg_completion_hours': None, 'total_labor_hours': Decimal('0'),
        '_hours': [],
    })
    for fact in facts:
        item = grouped[fact.assignee_id]
        item['assignee_id'] = fact.assignee_id
        item['assignee_name'] = fact.assignee_name or ''
        item['assigned'] += 1
        if fact.status in {'completed', 'closed'}:
            item['completed'] += 1
        if fact.completed_at and (fact.actual_start or fact.created_at):
            start = fact.actual_start or fact.created_at
            item['_hours'].append((fact.completed_at - start).total_seconds() / 3600)
        item['total_labor_hours'] += fact.labor_hours or 0
    output = []
    for item in grouped.values():
        hours = item.pop('_hours')
        item['avg_completion_hours'] = sum(hours) / len(hours) if hours else None
        item['total_labor_hours'] = _decimal_string(item['total_labor_hours'])
        output.append(item)
    return {'by_technician': output}


def _availability_window(filters):
    now = datetime.now(timezone.utc)
    start = datetime.combine(filters.date_from, time.min, tzinfo=timezone.utc) if filters.date_from else now - timedelta(days=30)
    end = datetime.combine(filters.date_to, time.max, tzinfo=timezone.utc) if filters.date_to else now
    return start, end


def build_equipment_availability(filters: ReportFilters) -> dict:
    start, end = _availability_window(filters)
    period_minutes = max(1, int((end - start).total_seconds() / 60))
    workorders = WorkOrderFact.objects.filter(created_at__gte=start, created_at__lte=end)
    inspections = InspectionFact.objects.filter(occurred_at__gte=start, occurred_at__lte=end)
    if filters.asset_id is not None:
        workorders = workorders.filter(asset_id=filters.asset_id)
        inspections = inspections.filter(asset_id=filters.asset_id)
    if filters.wo_type:
        workorders = workorders.filter(wo_type=filters.wo_type)
    if filters.status:
        workorders = workorders.filter(status=filters.status)
    downtime = defaultdict(int)
    counts = Counter()
    for fact in workorders:
        downtime[fact.asset_id] += fact.downtime_minutes or 0
        counts[fact.asset_id] += 1
    failed = Counter(inspections.values_list('asset_id', flat=True))
    asset_ids = set(downtime) | set(counts) | set(failed)
    if filters.asset_id is not None:
        asset_ids.add(filters.asset_id)
    asset_map = {
        asset.asset_id: asset
        for asset in AssetProjection.objects.filter(asset_id__in=asset_ids)
    }
    items = []
    for asset_id in sorted(asset_ids):
        asset = asset_map.get(asset_id)
        minutes = downtime[asset_id]
        items.append({
            'asset_id': asset_id,
            'asset_code': asset.asset_code if asset else '',
            'asset_name': asset.asset_name if asset else '',
            'downtime_minutes': minutes,
            'period_minutes': period_minutes,
            'availability': max(0, min(1, 1 - minutes / period_minutes)),
            'wo_count': counts[asset_id],
            'failed_inspections': failed[asset_id],
        })
    return {
        'date_from': start.date().isoformat(),
        'date_to': end.date().isoformat(),
        'period_minutes': period_minutes,
        'items': items,
    }


REPORT_BUILDERS = {
    'workorder_summary': build_workorder_summary,
    'downtime_analysis': build_downtime_analysis,
    'spareparts_usage': build_spareparts_usage,
    'maintenance-compliance': build_maintenance_compliance,
    'cost-analysis': build_cost_analysis,
    'technician-performance': build_technician_performance,
    'equipment-availability': build_equipment_availability,
}
