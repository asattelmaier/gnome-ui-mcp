"""Tests for window management: close, move, resize, snap, toggle state."""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

from gnome_ui_mcp.desktop import window_management


class TestCloseWindow:
    """F1: close_window sends Alt+F4."""

    @patch("gnome_ui_mcp.desktop.window_management.input")
    def test_close_window_calls_key_combo(self, mock_input: MagicMock) -> None:
        mock_input.key_combo.return_value = {"success": True}
        result = window_management.close_window()
        mock_input.key_combo.assert_called_once_with("alt+F4")
        assert result["success"] is True

    @patch("gnome_ui_mcp.desktop.window_management.input")
    def test_close_window_returns_action(self, mock_input: MagicMock) -> None:
        mock_input.key_combo.return_value = {"success": True}
        result = window_management.close_window()
        assert result["action"] == "close_window"


class TestMoveWindow:
    """F2: move_window sends Alt+F7 then arrow keys then Return."""

    @patch("gnome_ui_mcp.desktop.window_management.input")
    def test_move_positive(self, mock_input: MagicMock) -> None:
        mock_input.key_combo.return_value = {"success": True}
        mock_input.press_key.return_value = {"success": True}
        result = window_management.move_window(50, 30)
        # Alt+F7 to start move
        mock_input.key_combo.assert_any_call("alt+F7")
        # 50//10=5 Right presses, 30//10=3 Down presses, then Return
        calls = mock_input.press_key.call_args_list
        right_calls = [c for c in calls if c == call("Right")]
        down_calls = [c for c in calls if c == call("Down")]
        assert len(right_calls) == 5
        assert len(down_calls) == 3
        # Last call is Return
        assert calls[-1] == call("Return")
        assert result["success"] is True

    @patch("gnome_ui_mcp.desktop.window_management.input")
    def test_move_negative(self, mock_input: MagicMock) -> None:
        mock_input.key_combo.return_value = {"success": True}
        mock_input.press_key.return_value = {"success": True}
        result = window_management.move_window(-20, -40)
        calls = mock_input.press_key.call_args_list
        left_calls = [c for c in calls if c == call("Left")]
        up_calls = [c for c in calls if c == call("Up")]
        assert len(left_calls) == 2
        assert len(up_calls) == 4
        assert result["success"] is True

    @patch("gnome_ui_mcp.desktop.window_management.input")
    def test_move_zero(self, mock_input: MagicMock) -> None:
        mock_input.key_combo.return_value = {"success": True}
        mock_input.press_key.return_value = {"success": True}
        result = window_management.move_window(0, 0)
        calls = mock_input.press_key.call_args_list
        # Only Return should be sent (no arrow keys for zero movement)
        assert calls == [call("Return")]
        assert result["success"] is True


class TestResizeWindow:
    """F2: resize_window sends Alt+F8 then arrow keys then Return."""

    @patch("gnome_ui_mcp.desktop.window_management.input")
    def test_resize_positive(self, mock_input: MagicMock) -> None:
        mock_input.key_combo.return_value = {"success": True}
        mock_input.press_key.return_value = {"success": True}
        result = window_management.resize_window(30, 20)
        mock_input.key_combo.assert_any_call("alt+F8")
        calls = mock_input.press_key.call_args_list
        right_calls = [c for c in calls if c == call("Right")]
        down_calls = [c for c in calls if c == call("Down")]
        assert len(right_calls) == 3
        assert len(down_calls) == 2
        assert calls[-1] == call("Return")
        assert result["success"] is True

    @patch("gnome_ui_mcp.desktop.window_management.input")
    def test_resize_negative(self, mock_input: MagicMock) -> None:
        mock_input.key_combo.return_value = {"success": True}
        mock_input.press_key.return_value = {"success": True}
        result = window_management.resize_window(-10, -20)
        calls = mock_input.press_key.call_args_list
        left_calls = [c for c in calls if c == call("Left")]
        up_calls = [c for c in calls if c == call("Up")]
        assert len(left_calls) == 1
        assert len(up_calls) == 2
        assert result["success"] is True


class TestSnapWindow:
    """F2: snap_window sends Super+Arrow or Super+Up/Down."""

    @patch("gnome_ui_mcp.desktop.window_management.input")
    def test_snap_maximize(self, mock_input: MagicMock) -> None:
        mock_input.key_combo.return_value = {"success": True}
        result = window_management.snap_window("maximize")
        mock_input.key_combo.assert_called_once_with("super+Up")
        assert result["success"] is True

    @patch("gnome_ui_mcp.desktop.window_management.input")
    def test_snap_restore(self, mock_input: MagicMock) -> None:
        mock_input.key_combo.return_value = {"success": True}
        result = window_management.snap_window("restore")
        mock_input.key_combo.assert_called_once_with("super+Down")
        assert result["success"] is True

    @patch("gnome_ui_mcp.desktop.window_management.input")
    def test_snap_left(self, mock_input: MagicMock) -> None:
        mock_input.key_combo.return_value = {"success": True}
        result = window_management.snap_window("left")
        mock_input.key_combo.assert_called_once_with("super+Left")
        assert result["success"] is True

    @patch("gnome_ui_mcp.desktop.window_management.input")
    def test_snap_right(self, mock_input: MagicMock) -> None:
        mock_input.key_combo.return_value = {"success": True}
        result = window_management.snap_window("right")
        mock_input.key_combo.assert_called_once_with("super+Right")
        assert result["success"] is True

    @patch("gnome_ui_mcp.desktop.window_management.input")
    def test_snap_invalid_returns_error(self, mock_input: MagicMock) -> None:
        result = window_management.snap_window("diagonal")
        assert result["success"] is False
        assert "error" in result


class TestToggleWindowState:
    """F3: toggle_window_state sends the right key(s) for each state."""

    @patch("gnome_ui_mcp.desktop.window_management.input")
    def test_fullscreen(self, mock_input: MagicMock) -> None:
        mock_input.press_key.return_value = {"success": True}
        result = window_management.toggle_window_state("fullscreen")
        mock_input.press_key.assert_called_once_with("F11")
        assert result["success"] is True

    @patch("gnome_ui_mcp.desktop.window_management.input")
    def test_maximize(self, mock_input: MagicMock) -> None:
        mock_input.key_combo.return_value = {"success": True}
        result = window_management.toggle_window_state("maximize")
        mock_input.key_combo.assert_called_once_with("alt+F10")
        assert result["success"] is True

    @patch("gnome_ui_mcp.desktop.window_management.input")
    def test_minimize(self, mock_input: MagicMock) -> None:
        mock_input.key_combo.return_value = {"success": True}
        result = window_management.toggle_window_state("minimize")
        mock_input.key_combo.assert_called_once_with("super+h")
        assert result["success"] is True

    @patch("gnome_ui_mcp.desktop.window_management.input")
    def test_invalid_state_returns_error(self, mock_input: MagicMock) -> None:
        result = window_management.toggle_window_state("shaded")
        assert result["success"] is False
        assert "error" in result
