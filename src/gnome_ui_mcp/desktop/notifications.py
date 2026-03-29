from __future__ import annotations

import logging
import time
from collections import deque
from typing import Any

from ..runtime.gi_env import Gio, GLib
from .types import JsonDict

logger = logging.getLogger(__name__)


class NotificationMonitor:
    def __init__(self) -> None:
        self._running = False
        self._bus: Gio.DBusConnection | None = None
        self._subscription_id: int | None = None
        self._notifications: deque[JsonDict] = deque(maxlen=500)

    def start(self) -> JsonDict:
        if self._running:
            return {"success": True, "already_running": True}

        try:
            self._bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            self._subscription_id = self._bus.signal_subscribe(
                None,
                "org.freedesktop.Notifications",
                "Notify",
                "/org/freedesktop/Notifications",
                None,
                Gio.DBusSignalFlags.NONE,
                self._on_notify,
                None,
            )
            self._running = True
        except Exception as exc:
            return {"success": False, "error": str(exc)}

        return {"success": True, "monitoring": True}

    def read(self, clear: bool = True) -> JsonDict:
        if not self._running:
            return {"success": False, "error": "Notification monitor not started"}

        notifications = list(self._notifications)
        if clear:
            self._notifications.clear()

        return {
            "success": True,
            "notifications": notifications,
            "count": len(notifications),
        }

    def stop(self) -> JsonDict:
        if not self._running:
            return {"success": True, "already_stopped": True}

        if self._bus is not None and self._subscription_id is not None:
            self._bus.signal_unsubscribe(self._subscription_id)

        self._running = False
        self._subscription_id = None
        self._notifications.clear()

        return {"success": True, "stopped": True}

    def _on_notify(
        self,
        connection: Any,
        sender: str,
        path: str,
        interface: str,
        signal_name: str,
        params: GLib.Variant,
        user_data: Any,
    ) -> None:
        if not self._running:
            return

        try:
            unpacked = params.unpack()
            app_name, _replaces_id, _icon, summary, body, _actions, _hints, _timeout = unpacked
            self._notifications.append(
                {
                    "app_name": str(app_name),
                    "summary": str(summary),
                    "body": str(body),
                    "timestamp": time.time(),
                }
            )
        except Exception:
            logger.debug("Failed to parse notification signal", exc_info=True)


_MONITOR = NotificationMonitor()


def notification_monitor_start() -> JsonDict:
    return _MONITOR.start()


def notification_monitor_read(clear: bool = True) -> JsonDict:
    return _MONITOR.read(clear=clear)


def notification_monitor_stop() -> JsonDict:
    return _MONITOR.stop()


def dismiss_notification(notification_id: int) -> JsonDict:
    """Dismiss a notification by calling CloseNotification via D-Bus."""
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        bus.call_sync(
            "org.freedesktop.Notifications",
            "/org/freedesktop/Notifications",
            "org.freedesktop.Notifications",
            "CloseNotification",
            GLib.Variant("(u)", (notification_id,)),
            None,
            Gio.DBusCallFlags.NONE,
            5000,
            None,
        )
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "notification_id": notification_id,
        }

    return {
        "success": True,
        "notification_id": notification_id,
        "action": "dismissed",
    }


def click_notification_action(notification_id: int, action_key: str) -> JsonDict:
    """Invoke a notification action by emitting the ActionInvoked D-Bus signal.

    ActionInvoked is a *signal*, not a method, so we broadcast it with
    ``emit_signal`` rather than ``call_sync``.  This is best-effort --
    GNOME Shell may handle some actions internally and ignore the signal.
    """
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        bus.emit_signal(
            None,  # destination (broadcast)
            "/org/freedesktop/Notifications",
            "org.freedesktop.Notifications",
            "ActionInvoked",
            GLib.Variant("(us)", (notification_id, action_key)),
        )
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "notification_id": notification_id,
            "action_key": action_key,
        }

    return {
        "success": True,
        "notification_id": notification_id,
        "action_key": action_key,
    }
