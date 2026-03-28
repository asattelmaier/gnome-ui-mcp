"""Tests for region and window screenshot support."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import input as input_mod


def _mock_screenshot_proxy(success: bool = True, filename: str = "/tmp/shot.png") -> MagicMock:
    """Create a mock proxy whose call_sync returns (success, filename)."""
    proxy = MagicMock()
    result = MagicMock()
    result.unpack.return_value = (success, filename)
    proxy.call_sync.return_value = result
    return proxy


class TestScreenshotArea:
    def test_calls_dbus_with_correct_params(self) -> None:
        proxy = _mock_screenshot_proxy()
        with (
            patch.object(input_mod, "_screenshot_proxy", return_value=proxy),
            patch.object(input_mod, "_acquire_screenshot_bus"),
            patch.object(input_mod, "_release_screenshot_bus"),
        ):
            result = input_mod.screenshot_area(100, 200, 300, 400)

        proxy.call_sync.assert_called_once()
        call_args = proxy.call_sync.call_args
        assert call_args.args[0] == "ScreenshotArea"
        assert result["success"] is True

    def test_returns_failure_on_shell_error(self) -> None:
        proxy = _mock_screenshot_proxy(success=False)
        with (
            patch.object(input_mod, "_screenshot_proxy", return_value=proxy),
            patch.object(input_mod, "_acquire_screenshot_bus"),
            patch.object(input_mod, "_release_screenshot_bus"),
        ):
            result = input_mod.screenshot_area(100, 200, 300, 400)

        assert result["success"] is False

    def test_rejects_zero_width(self) -> None:
        result = input_mod.screenshot_area(100, 200, 0, 400)
        assert result["success"] is False
        assert "width" in result["error"].lower() or "dimension" in result["error"].lower()

    def test_rejects_negative_height(self) -> None:
        result = input_mod.screenshot_area(100, 200, 300, -1)
        assert result["success"] is False


class TestScreenshotWindow:
    def test_calls_dbus_with_correct_params(self) -> None:
        proxy = _mock_screenshot_proxy()
        with (
            patch.object(input_mod, "_screenshot_proxy", return_value=proxy),
            patch.object(input_mod, "_acquire_screenshot_bus"),
            patch.object(input_mod, "_release_screenshot_bus"),
        ):
            result = input_mod.screenshot_window(include_frame=True)

        proxy.call_sync.assert_called_once()
        call_args = proxy.call_sync.call_args
        assert call_args.args[0] == "ScreenshotWindow"
        assert result["success"] is True

    def test_include_frame_false(self) -> None:
        proxy = _mock_screenshot_proxy()
        with (
            patch.object(input_mod, "_screenshot_proxy", return_value=proxy),
            patch.object(input_mod, "_acquire_screenshot_bus"),
            patch.object(input_mod, "_release_screenshot_bus"),
        ):
            input_mod.screenshot_window(include_frame=False)

        variant = proxy.call_sync.call_args.args[1]
        include_frame_val = variant.unpack()[0]
        assert include_frame_val is False

    def test_returns_failure_on_shell_error(self) -> None:
        proxy = _mock_screenshot_proxy(success=False)
        with (
            patch.object(input_mod, "_screenshot_proxy", return_value=proxy),
            patch.object(input_mod, "_acquire_screenshot_bus"),
            patch.object(input_mod, "_release_screenshot_bus"),
        ):
            result = input_mod.screenshot_window()

        assert result["success"] is False


class TestBackendScreenshotWindow:
    def test_focuses_window_before_capture(self) -> None:
        from gnome_ui_mcp import backend

        with (
            patch.object(
                backend.accessibility,
                "focus_element",
                return_value={"success": True, "element_id": "0/1"},
            ) as mock_focus,
            patch.object(
                backend.input,
                "screenshot_window",
                return_value={"success": True, "path": "/tmp/win.png"},
            ),
            patch("time.sleep"),
        ):
            result = backend.screenshot_window(window_element_id="0/1")

        mock_focus.assert_called_once_with(element_id="0/1")
        assert result["success"] is True

    def test_fails_if_focus_fails(self) -> None:
        from gnome_ui_mcp import backend

        with patch.object(
            backend.accessibility,
            "focus_element",
            return_value={"success": False, "error": "no component"},
        ):
            result = backend.screenshot_window(window_element_id="0/1")

        assert result["success"] is False
        assert "focus" in result["error"].lower()
