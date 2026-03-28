"""Tests for screenshot burst after actions."""

from __future__ import annotations

from unittest.mock import patch

from gnome_ui_mcp.desktop import interaction


class TestScreenshotBurst:
    def test_no_screenshots_by_default(self) -> None:
        """Without screenshot_after_ms, no extra screenshots are taken."""
        with patch("gnome_ui_mcp.desktop.interaction.input") as mock_input:
            mock_input.screenshot.return_value = {"success": True, "path": "/tmp/shot.png"}

            screenshots = interaction._capture_burst(None)

        assert screenshots is None
        mock_input.screenshot.assert_not_called()

    def test_single_screenshot_at_zero(self) -> None:
        with (
            patch("gnome_ui_mcp.desktop.interaction.input") as mock_input,
            patch("time.sleep"),
        ):
            mock_input.screenshot.return_value = {"success": True, "path": "/tmp/burst0.png"}

            screenshots = interaction._capture_burst([0])

        assert len(screenshots) == 1
        assert screenshots[0]["path"] == "/tmp/burst0.png"

    def test_multiple_screenshots_in_order(self) -> None:
        with (
            patch("gnome_ui_mcp.desktop.interaction.input") as mock_input,
            patch("time.sleep") as mock_sleep,
        ):
            mock_input.screenshot.side_effect = [
                {"success": True, "path": "/tmp/b0.png"},
                {"success": True, "path": "/tmp/b1.png"},
                {"success": True, "path": "/tmp/b2.png"},
            ]

            screenshots = interaction._capture_burst([0, 100, 500])

        assert len(screenshots) == 3
        assert screenshots[0]["path"] == "/tmp/b0.png"
        assert screenshots[2]["path"] == "/tmp/b2.png"
        # Should have slept between captures
        assert mock_sleep.call_count >= 2

    def test_empty_list_returns_none(self) -> None:
        screenshots = interaction._capture_burst([])
        assert screenshots is None
