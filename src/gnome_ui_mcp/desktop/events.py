"""AT-SPI event subscription and polling (Item 12)."""

from __future__ import annotations

import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from ..runtime.gi_env import Atspi, GLib

JsonDict = dict[str, Any]

_MAX_BUFFER = 1000


def _init_atspi() -> None:
    if not Atspi.is_initialized():
        Atspi.init()


@dataclass
class EventSubscription:
    """Holds an AT-SPI event listener plus its buffered events."""

    listener: Any = None
    event_types: list[str] = field(default_factory=list)
    buffer: deque[JsonDict] = field(default_factory=lambda: deque(maxlen=_MAX_BUFFER))


# Module-level registry: subscription_id -> EventSubscription
_subscriptions: dict[str, EventSubscription] = {}


def subscribe_events(event_types: list[str], app_name: str | None = None) -> JsonDict:
    """Register an AT-SPI event listener for the given event types.

    Args:
        event_types: List of AT-SPI event type strings to listen for.
        app_name: Optional app name filter (reserved for future use).

    Returns a subscription id that can be used with :func:`poll_events`
    and :func:`unsubscribe_events`.
    """
    if not event_types:
        return {"success": False, "error": "event_types must not be empty"}

    _init_atspi()
    sub_id = str(uuid.uuid4())
    sub = EventSubscription(event_types=list(event_types))

    def _callback(event: Any) -> None:
        source = getattr(event, "source", None)
        sub.buffer.append(
            {
                "type": getattr(event, "type", ""),
                "source_name": (source.get_name() if source else "") or "",
                "source_role": (source.get_role_name() if source else "") or "",
                "detail1": getattr(event, "detail1", 0),
                "detail2": getattr(event, "detail2", 0),
                "timestamp": int(time.time() * 1000),
            }
        )

    listener = Atspi.EventListener.new(_callback)
    sub.listener = listener

    for etype in event_types:
        listener.register(etype)

    _subscriptions[sub_id] = sub
    return {"success": True, "subscription_id": sub_id, "event_types": list(event_types)}


def poll_events(
    subscription_id: str,
    timeout_ms: int = 500,
    max_events: int = 0,
    clear: bool = True,
) -> JsonDict:
    """Drain pending events from a subscription's buffer.

    Spins the GLib main context briefly to flush pending AT-SPI events.

    Args:
        subscription_id: ID returned from subscribe_events.
        timeout_ms: Time in milliseconds to pump the GLib event loop.
        max_events: Max events to return (0 = no limit).
        clear: Whether to clear the buffer after collecting events.
    """
    sub = _subscriptions.get(subscription_id)
    if sub is None:
        return {"success": False, "error": f"Unknown subscription: {subscription_id!r}"}

    # Pump GLib events to flush AT-SPI callbacks
    ctx = GLib.MainContext.default()
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if not ctx.iteration(False):
            break

    collected = list(sub.buffer)
    if max_events > 0:
        collected = collected[:max_events]
    if clear:
        sub.buffer.clear()

    return {"success": True, "events": collected, "count": len(collected)}


def unsubscribe(subscription_id: str) -> JsonDict:
    """Deregister an event subscription and remove it from the registry."""
    sub = _subscriptions.pop(subscription_id, None)
    if sub is None:
        return {"success": False, "error": f"Unknown subscription: {subscription_id!r}"}

    if sub.listener is not None:
        for etype in sub.event_types:
            try:
                sub.listener.deregister(etype)
            except Exception:
                pass

    return {"success": True, "subscription_id": subscription_id}


# Alias for consistency with backend/server naming convention
unsubscribe_events = unsubscribe
