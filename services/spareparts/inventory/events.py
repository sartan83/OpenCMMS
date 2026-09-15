from cmms_common.events.bus import Event, get_event_bus


def publish_part_consumed(txn, spare_part, actor_id):
    get_event_bus().publish(Event(
        type='part.consumed',
        source='spareparts',
        payload={
            'transaction_id': txn.id,
            'part_id': spare_part.id,
            'part_code': spare_part.part_code,
            'quantity': str(txn.quantity),
            'unit_cost': str(spare_part.unit_cost) if spare_part.unit_cost is not None else None,
            'work_order_id': txn.related_work_order,
            'actor_id': actor_id,
        },
    ))
