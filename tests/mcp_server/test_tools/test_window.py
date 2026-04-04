"""Tests for window management tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.mcp_context import McpContext
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.tools import window
from gnome_ui_mcp.tools.tool_definition import ToolRequest


@pytest.fixture()
def ctx() -> McpContext:
    return MagicMock(spec=McpContext)


class TestCloseWindow:
    @patch("gnome_ui_mcp.adapters.window_mgmt.close_window")
    def test_close(self, mock_cw, ctx) -> None:
        response = McpResponse()
        window._close_window(ToolRequest({}), response, ctx)

        assert response.is_error is False
        assert "Closed" in response.text_lines[0]
        mock_cw.assert_called_once()


class TestMoveWindow:
    @patch("gnome_ui_mcp.adapters.window_mgmt.move_window")
    def test_move(self, mock_mw, ctx) -> None:
        response = McpResponse()
        window._move_window(ToolRequest({"dx": 100, "dy": -50}), response, ctx)

        structured = response.to_tool_result().structuredContent
        assert structured["dx"] == 100
        assert structured["dy"] == -50
        mock_mw.assert_called_once_with(100, -50)

    @patch("gnome_ui_mcp.adapters.window_mgmt.move_window")
    def test_move_failure_raises(self, mock_mw, ctx) -> None:
        mock_mw.side_effect = RuntimeError("Failed to enter move mode")
        response = McpResponse()
        with pytest.raises(RuntimeError, match="move mode"):
            window._move_window(ToolRequest({"dx": 10, "dy": 10}), response, ctx)


class TestSnapWindow:
    @patch("gnome_ui_mcp.adapters.window_mgmt.snap_window")
    def test_snap_left(self, mock_sw, ctx) -> None:
        response = McpResponse()
        window._snap_window(ToolRequest({"position": "left"}), response, ctx)

        assert "left" in response.text_lines[0]
        mock_sw.assert_called_once_with("left")

    @patch("gnome_ui_mcp.adapters.window_mgmt.snap_window")
    def test_invalid_position_raises(self, mock_sw, ctx) -> None:
        mock_sw.side_effect = ValueError("Invalid position")
        response = McpResponse()
        with pytest.raises(ValueError, match="Invalid position"):
            window._snap_window(ToolRequest({"position": "center"}), response, ctx)


class TestToggleWindowState:
    @patch("gnome_ui_mcp.adapters.window_mgmt.toggle_window_state")
    def test_fullscreen(self, mock_tws, ctx) -> None:
        response = McpResponse()
        window._toggle_window_state(ToolRequest({"state": "fullscreen"}), response, ctx)

        assert "fullscreen" in response.text_lines[0]
        mock_tws.assert_called_once_with("fullscreen")
