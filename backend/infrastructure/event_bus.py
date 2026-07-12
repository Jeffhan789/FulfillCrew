"""Async event bus infrastructure for FulfillCrew.

Supports Redis-backed pub/sub and an in-memory fallback for development.
"""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable

import redis.asyncio as redis

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Event channel constants
# ---------------------------------------------------------------------------
ORDER_CREATED = "order.created"
FRAUD_CHECKED = "fraud.checked"
INVENTORY_CHECKED = "inventory.checked"
WAREHOUSE_BID = "warehouse.bid"
FULFILLMENT_COMPLETED = "fulfillment.completed"


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------
class EventBus(ABC):
    """Abstract async event bus."""

    @abstractmethod
    async def publish(self, channel: str, event: dict[str, Any]) -> None:
        """Publish an event to a channel. Returns immediately without waiting for handlers."""

    @abstractmethod
    async def subscribe(self, channel: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        """Subscribe a handler to a channel."""

    @abstractmethod
    async def close(self) -> None:
        """Release resources and stop background tasks."""


# ---------------------------------------------------------------------------
# Redis implementation
# ---------------------------------------------------------------------------
class RedisEventBus(EventBus):
    """Redis-based async pub/sub event bus."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        self._redis_url = redis_url
        self._redis: redis.Redis | None = None
        self._pubsub: redis.client.PubSub | None = None
        self._handlers: dict[str, list[Callable[[dict[str, Any]], Any]]] = {}
        self._listener_task: asyncio.Task | None = None
        self._closed = False

    # --- internal helpers ---

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    async def _get_pubsub(self) -> redis.client.PubSub:
        if self._pubsub is None:
            self._pubsub = (await self._get_redis()).pubsub()
        return self._pubsub

    async def _listen_loop(self) -> None:
        """Background task: listen for incoming Redis messages and dispatch to handlers."""
        try:
            pubsub = await self._get_pubsub()
            await pubsub.subscribe(*self._handlers.keys())
            async for message in pubsub.listen():
                if self._closed:
                    break
                if message["type"] != "message":
                    continue
                channel = message["channel"]
                payload = message["data"]
                try:
                    event = json.loads(payload)
                except json.JSONDecodeError as exc:
                    logger.warning("Failed to decode message on %s: %s", channel, exc)
                    continue
                handlers = self._handlers.get(channel, [])
                for handler in handlers:
                    try:
                        result = handler(event)
                        if asyncio.isfuture(result) or asyncio.iscoroutine(result):
                            asyncio.create_task(self._run_handler(handler, event))
                    except Exception as exc:
                        logger.exception("Handler error on %s: %s", channel, exc)
        except asyncio.CancelledError:
            logger.info("Redis listener task cancelled")
        except Exception as exc:
            logger.exception("Redis listener loop crashed: %s", exc)

    @staticmethod
    async def _run_handler(handler: Callable[[dict[str, Any]], Any], event: dict[str, Any]) -> None:
        try:
            await handler(event)
        except Exception as exc:
            logger.exception("Async handler error: %s", exc)

    # --- public API ---

    async def publish(self, channel: str, event: dict[str, Any]) -> None:
        if self._closed:
            logger.warning("Publish on closed event bus, dropping event on %s", channel)
            return
        try:
            r = await self._get_redis()
            await r.publish(channel, json.dumps(event))
        except Exception as exc:
            logger.exception("Failed to publish event to %s: %s", channel, exc)

    async def subscribe(self, channel: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        if self._closed:
            raise RuntimeError("Cannot subscribe to a closed event bus")
        if channel not in self._handlers:
            self._handlers[channel] = []
        self._handlers[channel].append(handler)
        # If listener is already running, subscribe the new channel on the fly
        if self._listener_task is not None and not self._listener_task.done():
            try:
                pubsub = await self._get_pubsub()
                await pubsub.subscribe(channel)
            except Exception as exc:
                logger.exception("Failed to subscribe %s to Redis pubsub: %s", channel, exc)
        elif self._listener_task is None:
            self._listener_task = asyncio.create_task(self._listen_loop())

    async def close(self) -> None:
        self._closed = True
        if self._listener_task is not None and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        if self._pubsub is not None:
            try:
                await self._pubsub.close()
            except Exception as exc:
                logger.warning("Error closing pubsub: %s", exc)
        if self._redis is not None:
            try:
                await self._redis.close()
            except Exception as exc:
                logger.warning("Error closing redis client: %s", exc)
        self._pubsub = None
        self._redis = None


# ---------------------------------------------------------------------------
# In-memory implementation
# ---------------------------------------------------------------------------
class InMemoryEventBus(EventBus):
    """In-memory fallback for development without Redis."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[dict[str, Any]], Any]]] = {}
        self._queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()
        self._dispatcher_task: asyncio.Task | None = None
        self._closed = False

    async def _dispatch_loop(self) -> None:
        """Background task: pull events from queue and dispatch to handlers."""
        try:
            while not self._closed:
                try:
                    channel, event = await asyncio.wait_for(self._queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                handlers = self._handlers.get(channel, [])
                for handler in handlers:
                    try:
                        result = handler(event)
                        if asyncio.isfuture(result) or asyncio.iscoroutine(result):
                            asyncio.create_task(self._run_handler(handler, event))
                    except Exception as exc:
                        logger.exception("Handler error on %s: %s", channel, exc)
                self._queue.task_done()
        except asyncio.CancelledError:
            logger.info("InMemory dispatcher task cancelled")
        except Exception as exc:
            logger.exception("InMemory dispatcher loop crashed: %s", exc)

    @staticmethod
    async def _run_handler(handler: Callable[[dict[str, Any]], Any], event: dict[str, Any]) -> None:
        try:
            await handler(event)
        except Exception as exc:
            logger.exception("Async handler error: %s", exc)

    async def publish(self, channel: str, event: dict[str, Any]) -> None:
        if self._closed:
            logger.warning("Publish on closed event bus, dropping event on %s", channel)
            return
        try:
            await self._queue.put((channel, event))
        except Exception as exc:
            logger.exception("Failed to enqueue event to %s: %s", channel, exc)

    async def subscribe(self, channel: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        if self._closed:
            raise RuntimeError("Cannot subscribe to a closed event bus")
        if channel not in self._handlers:
            self._handlers[channel] = []
        self._handlers[channel].append(handler)
        if self._dispatcher_task is None:
            self._dispatcher_task = asyncio.create_task(self._dispatch_loop())

    async def close(self) -> None:
        self._closed = True
        if self._dispatcher_task is not None and not self._dispatcher_task.done():
            self._dispatcher_task.cancel()
            try:
                await self._dispatcher_task
            except asyncio.CancelledError:
                pass
        # Drain remaining queue so pending events don't block
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except asyncio.QueueEmpty:
                break


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
async def get_event_bus(redis_url: str | None = None) -> EventBus:
    """Return a Redis-backed event bus if available; otherwise fall back to in-memory."""
    if redis_url:
        try:
            bus = RedisEventBus(redis_url)
            # Quick connectivity check
            r = await bus._get_redis()
            await r.ping()
            logger.info("Connected to Redis at %s", redis_url)
            return bus
        except Exception as exc:
            logger.warning("Redis connection failed (%s), falling back to InMemoryEventBus", exc)
    return InMemoryEventBus()
