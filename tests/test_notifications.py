"""Tests for desktop notification monitoring."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import notifications as notif_mod


class TestNotificationMonitor:
    def test_start_initializes_state(self) -> None:
        monitor = notif_mod.NotificationMonitor()
        with patch("gnome_ui_mcp.desktop.notifications.Gio") as mock_gio:
            mock_bus = MagicMock()
            mock_gio.bus_get_sync.return_value = mock_bus
            mock_bus.signal_subscribe.return_value = 1

            result = monitor.start()

        assert result["success"] is True
        assert monitor._running is True

    def test_read_returns_captured_notifications(self) -> None:
        monitor = notif_mod.NotificationMonitor()
        monitor._running = True
        monitor._notifications.append(
            {
                "app_name": "Firefox",
                "summary": "Download complete",
                "body": "file.zip",
            }
        )

        result = monitor.read(clear=False)

        assert result["success"] is True
        assert len(result["notifications"]) == 1
        assert result["notifications"][0]["app_name"] == "Firefox"

    def test_read_clear_empties_buffer(self) -> None:
        monitor = notif_mod.NotificationMonitor()
        monitor._running = True
        monitor._notifications.append({"app_name": "test", "summary": "hi", "body": ""})

        monitor.read(clear=True)
        result = monitor.read()

        assert len(result["notifications"]) == 0

    def test_read_without_start_returns_error(self) -> None:
        monitor = notif_mod.NotificationMonitor()
        result = monitor.read()
        assert result["success"] is False

    def test_stop_cleans_up(self) -> None:
        monitor = notif_mod.NotificationMonitor()
        monitor._running = True
        monitor._bus = MagicMock()
        monitor._subscription_id = 42

        result = monitor.stop()

        assert result["success"] is True
        assert monitor._running is False
        monitor._bus.signal_unsubscribe.assert_called_once_with(42)

    def test_notification_callback_captures_fields(self) -> None:
        monitor = notif_mod.NotificationMonitor()
        monitor._running = True

        from gi.repository import GLib

        params = GLib.Variant(
            "(susssasa{sv}i)",
            (
                "TestApp",
                0,
                "icon",
                "Test Summary",
                "Test Body",
                [],
                {},
                5000,
            ),
        )

        monitor._on_notify(None, "sender", "/path", "iface", "Notify", params, None)

        assert len(monitor._notifications) == 1
        n = monitor._notifications[0]
        assert n["app_name"] == "TestApp"
        assert n["summary"] == "Test Summary"
        assert n["body"] == "Test Body"

    def test_multiple_notifications_ordered(self) -> None:
        monitor = notif_mod.NotificationMonitor()
        monitor._running = True

        from gi.repository import GLib

        for app in ["App1", "App2", "App3"]:
            params = GLib.Variant("(susssasa{sv}i)", (app, 0, "", "sum", "body", [], {}, -1))
            monitor._on_notify(None, "s", "/p", "i", "Notify", params, None)

        result = monitor.read()
        assert [n["app_name"] for n in result["notifications"]] == ["App1", "App2", "App3"]


class TestModuleLevelFunctions:
    def test_start_creates_monitor(self) -> None:
        with patch("gnome_ui_mcp.desktop.notifications.Gio") as mock_gio:
            mock_bus = MagicMock()
            mock_gio.bus_get_sync.return_value = mock_bus
            mock_bus.signal_subscribe.return_value = 1

            # Reset module-level monitor
            notif_mod._MONITOR = notif_mod.NotificationMonitor()
            result = notif_mod.notification_monitor_start()

        assert result["success"] is True

    def test_stop_after_start(self) -> None:
        notif_mod._MONITOR = notif_mod.NotificationMonitor()
        notif_mod._MONITOR._running = True
        notif_mod._MONITOR._bus = MagicMock()
        notif_mod._MONITOR._subscription_id = 1

        result = notif_mod.notification_monitor_stop()
        assert result["success"] is True
