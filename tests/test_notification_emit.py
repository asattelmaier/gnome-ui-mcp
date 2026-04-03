"""Tests for click_notification_action using emit_signal instead of call_sync."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import notifications


class TestClickNotificationActionEmit:
    """click_notification_action should use emit_signal (not call_sync)."""

    def test_emit_signal_called_with_correct_params(self) -> None:
        mock_bus = MagicMock()

        with patch.object(
            notifications.Gio,
            "bus_get_sync",
            return_value=mock_bus,
        ):
            result = notifications.click_notification_action(42, "default")

        assert result["success"] is True
        mock_bus.emit_signal.assert_called_once()
        call_args = mock_bus.emit_signal.call_args
        assert call_args.args[1] == "/org/freedesktop/Notifications"
        assert call_args.args[2] == "org.freedesktop.Notifications"
        assert call_args.args[3] == "ActionInvoked"

    def test_exception_during_emit_returns_error(self) -> None:
        mock_bus = MagicMock()
        mock_bus.emit_signal.side_effect = Exception("D-Bus error")

        with patch.object(
            notifications.Gio,
            "bus_get_sync",
            return_value=mock_bus,
        ):
            result = notifications.click_notification_action(42, "default")

        assert result["success"] is False
        assert "error" in result
        assert "D-Bus error" in result["error"]
