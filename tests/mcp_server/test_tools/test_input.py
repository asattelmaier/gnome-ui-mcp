"""Tests for input tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.adapters.input_actions import ClickAtResult
from gnome_ui_mcp.mcp_context import McpContext
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.tools import input as input_mod
from gnome_ui_mcp.tools.tool_definition import ToolRequest


@pytest.fixture()
def ctx() -> McpContext:
    return MagicMock(spec=McpContext)


class TestClickAt:
    @patch("gnome_ui_mcp.adapters.input_actions.click_at")
    def test_click_at_success(self, mock_click, ctx) -> None:
        mock_click.return_value = ClickAtResult(
            x=100,
            y=200,
            button="left",
            method="remote_desktop",
            input_injected=True,
            effect_verified=True,
        )
        response = McpResponse()
        input_mod._click_at(ToolRequest({"x": 100, "y": 200, "button": "left"}), response, ctx)

        assert response.is_error is False
        assert "100" in response.text_lines[0]
        assert "200" in response.text_lines[0]
        ctx.record_action.assert_called_once()

    @patch("gnome_ui_mcp.adapters.input_actions.click_at")
    def test_click_at_failure(self, mock_click, ctx) -> None:
        mock_click.side_effect = ValueError("No remote desktop")
        response = McpResponse()
        with pytest.raises(ValueError, match="No remote desktop"):
            input_mod._click_at(ToolRequest({"x": 100, "y": 200}), response, ctx)


class TestTypeText:
    @patch("gnome_ui_mcp.adapters.input_actions.type_text")
    def test_type_text_success(self, mock_type, ctx) -> None:
        response = McpResponse()
        input_mod._type_text(ToolRequest({"text": "hello"}), response, ctx)

        assert "5 characters" in response.text_lines[0]
        ctx.record_action.assert_called_once()


class TestScroll:
    @patch("gnome_ui_mcp.adapters.input_actions.scroll")
    def test_scroll_success(self, mock_scroll, ctx) -> None:
        response = McpResponse()
        input_mod._scroll(ToolRequest({"direction": "down", "clicks": 3}), response, ctx)

        assert "down" in response.text_lines[0]
        assert "3" in response.text_lines[0]
