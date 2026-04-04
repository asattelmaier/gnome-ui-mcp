"""Tests for visual tools (screenshot, area, window)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.adapters.input import ScreenshotResult
from gnome_ui_mcp.adapters.screenshots import (
    AreaScreenshotResult,
    WindowScreenshotResult,
    screenshot_window,
)
from gnome_ui_mcp.mcp_context import McpContext
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.tools import visual
from gnome_ui_mcp.tools.tool_definition import ToolRequest


@pytest.fixture()
def ctx() -> McpContext:
    return MagicMock(spec=McpContext)


class TestScreenshot:
    @patch("gnome_ui_mcp.adapters.input.screenshot")
    def test_screenshot_success(self, mock_ss, ctx) -> None:
        mock_ss.return_value = ScreenshotResult(
            path="/tmp/screenshot.png",
            scale_factor=1,
            pixel_size=[1920, 1080],
            logical_size=[1920, 1080],
        )
        response = McpResponse()
        visual._screenshot(ToolRequest({}), response, ctx)

        assert response.is_error is False
        structured = response.to_tool_result().structuredContent
        assert structured["path"] == "/tmp/screenshot.png"
        result = response.to_tool_result()
        assert len(result.content) == 1  # No image

    @patch("gnome_ui_mcp.adapters.input.screenshot")
    def test_screenshot_with_base64_as_image_content(self, mock_ss, ctx) -> None:
        mock_ss.return_value = ScreenshotResult(
            path="/tmp/s.png",
            scale_factor=1,
            image_base64="iVBOR...",
        )
        response = McpResponse()
        visual._screenshot(ToolRequest({"return_base64": True}), response, ctx)

        result = response.to_tool_result()
        assert len(result.content) == 2
        assert result.content[1].type == "image"
        assert result.content[1].data == "iVBOR..."

    @patch("gnome_ui_mcp.adapters.input.screenshot")
    def test_screenshot_error_raises(self, mock_ss, ctx) -> None:
        mock_ss.side_effect = ValueError("D-Bus call failed")

        response = McpResponse()
        with pytest.raises(ValueError, match="D-Bus call failed"):
            visual._screenshot(ToolRequest({}), response, ctx)


class TestScreenshotArea:
    @patch("gnome_ui_mcp.adapters.screenshots.screenshot_area")
    def test_area_success(self, mock_ss, ctx) -> None:
        mock_ss.return_value = AreaScreenshotResult(path="/tmp/area.png")
        response = McpResponse()
        visual._screenshot_area(
            ToolRequest({"x": 0, "y": 0, "width": 100, "height": 100}), response, ctx
        )

        assert "/tmp/area.png" in response.text_lines[0]
        structured = response.to_tool_result().structuredContent
        assert structured["path"] == "/tmp/area.png"

    @patch("gnome_ui_mcp.adapters.screenshots.screenshot_area")
    def test_area_failure(self, mock_ss, ctx) -> None:
        mock_ss.side_effect = ValueError("Region out of bounds")
        response = McpResponse()
        with pytest.raises(ValueError, match="Region out of bounds"):
            visual._screenshot_area(
                ToolRequest({"x": 0, "y": 0, "width": 100, "height": 100}), response, ctx
            )


class TestScreenshotWindow:
    @patch("gnome_ui_mcp.adapters.screenshots.screenshot_window")
    def test_window_success(self, mock_ss, ctx) -> None:
        mock_ss.return_value = WindowScreenshotResult(
            path="/tmp/win.png",
            window_element_id="0/1",
        )
        response = McpResponse()
        visual._screenshot_window(ToolRequest({"window_element_id": "0/1"}), response, ctx)

        assert "/tmp/win.png" in response.text_lines[0]


class TestWindowScreenshotAdapter:
    @patch("gnome_ui_mcp.desktop.input.screenshot_window")
    @patch("gnome_ui_mcp.desktop.accessibility.focus_element")
    def test_focuses_window_before_capture(self, mock_focus, mock_capture) -> None:
        mock_focus.return_value = {"success": True, "element_id": "0/1"}
        mock_capture.return_value = {"success": True, "path": "/tmp/win.png"}

        with patch("time.sleep"):
            result = screenshot_window(window_element_id="0/1")

        mock_focus.assert_called_once_with(element_id="0/1")
        assert result.path == "/tmp/win.png"

    @patch("gnome_ui_mcp.desktop.accessibility.focus_element")
    def test_fails_if_focus_fails(self, mock_focus) -> None:
        mock_focus.return_value = {"success": False, "error": "no component"}

        with pytest.raises(ValueError, match="Could not focus window"):
            screenshot_window(window_element_id="0/1")
