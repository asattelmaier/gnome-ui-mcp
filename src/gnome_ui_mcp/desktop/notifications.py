from __future__ import annotations

import time
from collections import deque
from typing import Any

from ..runtime.gi_env import Gio, GLib

JsonDict = dict[str, Any]


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
            pass


_MONITOR = NotificationMonitor()


def notification_monitor_start() -> JsonDict:
    return _MONITOR.start()


def notification_monitor_read(clear: bool = True) -> JsonDict:
    return _MONITOR.read(clear=clear)


def notification_monitor_stop() -> JsonDict:
    return _MONITOR.stop()
