"""Tests for screenshot path traversal protection."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop.input import CACHE_DIR, screenshot


class TestScreenshotPathTraversal:
    """Filenames outside CACHE_DIR must be rejected before any D-Bus call."""

    def test_traversal_attempt_rejected(self) -> None:
        result = screenshot(filename="/tmp/evil.png")
        assert result["success"] is False
        assert "Path must be within" in result["error"]

    def test_dot_dot_traversal_rejected(self) -> None:
        malicious = str(CACHE_DIR / ".." / ".." / "etc" / "passwd")
        result = screenshot(filename=malicious)
        assert result["success"] is False
        assert "Path must be within" in result["error"]

    def test_home_relative_traversal_rejected(self) -> None:
        result = screenshot(filename="~/Desktop/leak.png")
        assert result["success"] is False
        assert "Path must be within" in result["error"]

    @patch("gnome_ui_mcp.desktop.input.Image")
    @patch("gnome_ui_mcp.desktop.input._screenshot_dbus")
    def test_valid_path_within_cache_accepted(
        self, mock_dbus: MagicMock, mock_image: MagicMock
    ) -> None:
        valid_path = str(CACHE_DIR / "test-capture.png")
        mock_dbus.return_value = (True, valid_path)
        mock_img = MagicMock()
        mock_img.size = (1920, 1080)
        mock_image.open.return_value = mock_img
        result = screenshot(filename=valid_path)
        assert result["success"] is True
        mock_dbus.assert_called_once()

    @patch("gnome_ui_mcp.desktop.input.Image")
    @patch("gnome_ui_mcp.desktop.input._screenshot_dbus")
    def test_no_filename_auto_generates(self, mock_dbus: MagicMock, mock_image: MagicMock) -> None:
        valid_path = str(CACHE_DIR / "auto-generated.png")
        mock_dbus.return_value = (True, valid_path)
        mock_img = MagicMock()
        mock_img.size = (1920, 1080)
        mock_image.open.return_value = mock_img
        result = screenshot(filename=None)
        assert result["success"] is True
        mock_dbus.assert_called_once()
