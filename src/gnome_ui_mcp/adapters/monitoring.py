"""Event monitoring and notifications.

Wraps desktop events, notifications, and accessibility modules. Returns
typed data and raises exceptions on failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..desktop import accessibility as _desktop_accessibility
from ..desktop import events as _desktop_events
from ..desktop import notifications as _desktop_notifications


def _require(result: dict) -> dict:
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Operation failed")))
    return result


# -- dataclasses --


@dataclass
class EventSubscription:
    subscription_id: str
    event_types: list[str]


@dataclass
class PollResult:
    events: list[dict]
    count: int


@dataclass
class NotificationList:
    notifications: list[dict]
    count: int


# -- public API --


def subscribe_events(
    event_types: list[str],
    app_name: str | None = None,
) -> EventSubscription:
    """Subscribe to AT-SPI events. Raises on failure."""
    result = _require(_desktop_events.subscribe_events(event_types=event_types, app_name=app_name))
    return EventSubscription(
        subscription_id=result.get("subscription_id", ""),
        event_types=result.get("event_types", event_types),
    )


def poll_events(
    subscription_id: str,
    timeout_ms: int = 5000,
    max_events: int = 100,
) -> PollResult:
    """Poll for captured AT-SPI events. Raises on failure."""
    result = _require(
        _desktop_events.poll_events(
            subscription_id=subscription_id,
            timeout_ms=timeout_ms,
            max_events=max_events,
        )
    )
    events = result.get("events", [])
    return PollResult(events=events, count=len(events))


def unsubscribe_events(subscription_id: str) -> None:
    """Unsubscribe from AT-SPI events. Raises on failure."""
    _require(_desktop_events.unsubscribe_events(subscription_id=subscription_id))


def notification_monitor_start() -> None:
    """Start monitoring desktop notifications. Raises on failure."""
    _require(_desktop_notifications.notification_monitor_start())


def notification_monitor_read(clear: bool = True) -> NotificationList:
    """Read captured notifications. Raises on failure."""
    result = _require(_desktop_notifications.notification_monitor_read(clear=clear))
    notifications = result.get("notifications", [])
    return NotificationList(notifications=notifications, count=len(notifications))


def notification_monitor_stop() -> None:
    """Stop monitoring notifications. Raises on failure."""
    _require(_desktop_notifications.notification_monitor_stop())


def dismiss_notification(notification_id: int) -> None:
    """Dismiss a notification by ID. Raises on failure."""
    _require(_desktop_notifications.dismiss_notification(notification_id=notification_id))


def click_notification_action(notification_id: int, action_key: str) -> None:
    """Invoke an action on a notification. Raises on failure."""
    _require(
        _desktop_notifications.click_notification_action(
            notification_id=notification_id,
            action_key=action_key,
        )
    )


def visible_shell_popups() -> list[dict]:
    """Return visible GNOME Shell popup containers. Raises on failure."""
    result = _require(_desktop_accessibility.visible_shell_popups())
    return result.get("popups", [])
