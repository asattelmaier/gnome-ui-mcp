"""Tests for click_notification_action and dismiss_notification tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import notifications


class TestNotificationActions:
    def test_dismiss_calls_close_notification(self) -> None:
        mock_bus = MagicMock()
        mock_result = MagicMock()
        mock_result.unpack.return_value = (True,)
        mock_bus.call_sync.return_value = mock_result

        with patch.object(
            notifications.Gio,
            "bus_get_sync",
            return_value=mock_bus,
        ):
            result = notifications.dismiss_notification(42)

        assert result["success"] is True
        mock_bus.call_sync.assert_called_once()
        call_args = mock_bus.call_sync.call_args
        assert call_args.args[2] == "org.freedesktop.Notifications"
        assert call_args.args[3] == "CloseNotification"

    def test_action_invocation(self) -> None:
        mock_bus = MagicMock()
        mock_result = MagicMock()
        mock_result.unpack.return_value = (True,)
        mock_bus.call_sync.return_value = mock_result

        with patch.object(
            notifications.Gio,
            "bus_get_sync",
            return_value=mock_bus,
        ):
            result = notifications.click_notification_action(42, "default")

        assert result["success"] is True

    def test_invalid_id_error(self) -> None:
        mock_bus = MagicMock()
        mock_bus.call_sync.side_effect = Exception("Notification not found")

        with patch.object(
            notifications.Gio,
            "bus_get_sync",
            return_value=mock_bus,
        ):
            result = notifications.dismiss_notification(99999)

        assert result["success"] is False
        assert "error" in result
