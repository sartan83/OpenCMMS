from __future__ import annotations

import logging
import os
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from kombu import Connection, Consumer, Exchange, Producer, Queue
from kombu.entity import binding

from .schemas import validate

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Event:
    type: str
    version: int = 1
    payload: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: str = field(default_factory=_utc_now)
    source: str = 'monolith'
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Event:
        return cls(**value)


class EventBus(ABC):
    @abstractmethod
    def publish(self, event: Event) -> bool:
        raise NotImplementedError

    @abstractmethod
    def subscribe(
        self,
        routing_keys: list[str],
        handler: Callable[[Event], None],
        queue_name: str,
    ) -> None:
        raise NotImplementedError

    @staticmethod
    def _validate(event: Event) -> bool:
        try:
            validate(event)
        except Exception:
            logger.exception('Event validation failed for %s', event.type)
            return False
        return True


class RabbitMQEventBus(EventBus):
    exchange_name = 'cmms.events'

    def __init__(self, url: str):
        self.url = url
        self.exchange = Exchange(self.exchange_name, type='topic', durable=True)

    def publish(self, event: Event) -> bool:
        if not self._validate(event):
            return False
        try:
            with Connection(self.url) as connection:
                producer = Producer(connection)
                producer.publish(
                    event.to_dict(),
                    exchange=self.exchange,
                    routing_key=event.type,
                    serializer='json',
                    declare=[self.exchange],
                    delivery_mode=2,
                )
            return True
        except Exception:
            logger.exception('Failed to publish event %s', event.type)
            return False

    def subscribe(
        self,
        routing_keys: list[str],
        handler: Callable[[Event], None],
        queue_name: str,
    ) -> None:
        queue = Queue(
            queue_name,
            exchange=self.exchange,
            bindings=[binding(self.exchange, routing_key=key) for key in routing_keys],
            durable=True,
        )
        with Connection(self.url) as connection:
            with Consumer(connection, queues=[queue], accept=['json']) as consumer:
                def callback(body: dict[str, Any], message: Any) -> None:
                    try:
                        handler(Event.from_dict(body))
                        message.ack()
                    except Exception:
                        logger.exception('Event handler failed for queue %s', queue_name)
                        message.reject(requeue=False)

                consumer.register_callback(callback)
                consumer.consume()
                while True:
                    try:
                        connection.drain_events()
                    except Exception:
                        logger.exception('Event consumer failed for queue %s', queue_name)


class InMemoryEventBus(EventBus):
    def __init__(self):
        self.published: list[Event] = []
        self._subscribers: list[tuple[list[str], Callable[[Event], None], str]] = []

    def publish(self, event: Event) -> bool:
        if not self._validate(event):
            return False
        self.published.append(event)
        for routing_keys, handler, _queue_name in list(self._subscribers):
            if event.type in routing_keys or '#' in routing_keys:
                try:
                    handler(event)
                except Exception:
                    logger.exception('In-memory event handler failed for %s', event.type)
        return True

    def subscribe(
        self,
        routing_keys: list[str],
        handler: Callable[[Event], None],
        queue_name: str,
    ) -> None:
        self._subscribers.append((routing_keys, handler, queue_name))


_in_memory_bus: InMemoryEventBus | None = None


def get_event_bus() -> EventBus:
    global _in_memory_bus
    url = os.environ.get('EVENT_BUS_URL')
    try:
        from django.conf import settings

        if settings.configured:
            url = getattr(settings, 'EVENT_BUS_URL', url)
    except ImportError:
        pass

    if url:
        return RabbitMQEventBus(url)
    if _in_memory_bus is None:
        _in_memory_bus = InMemoryEventBus()
    return _in_memory_bus
