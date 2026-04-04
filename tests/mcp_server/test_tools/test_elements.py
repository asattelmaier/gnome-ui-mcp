"""Tests for element tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.adapters.elements import ClickResult
from gnome_ui_mcp.mcp_context import McpContext
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.tools import elements
from gnome_ui_mcp.tools.tool_definition import ToolRequest


@pytest.fixture()
def ctx() -> McpContext:
    return MagicMock(spec=McpContext)


class TestFocusElement:
    @patch("gnome_ui_mcp.adapters.elements.focus_element")
    def test_focus_success(self, mock_focus, ctx) -> None:
        response = McpResponse()
        elements._focus_element(ToolRequest({"element_id": "0/1/2"}), response, ctx)

        assert "0/1/2" in response.text_lines[0]
        mock_focus.assert_called_once_with(element_id="0/1/2")
        ctx.check_boundary.assert_called_once_with("0/1/2")

    def test_focus_boundary_violation(self, ctx) -> None:
        ctx.check_boundary.side_effect = ValueError("Outside boundary")
        response = McpResponse()
        with pytest.raises(ValueError, match="Outside boundary"):
            elements._focus_element(ToolRequest({"element_id": "0/1/2"}), response, ctx)


class TestClickElement:
    @patch("gnome_ui_mcp.adapters.elements.click_element")
    def test_click_success(self, mock_click, ctx) -> None:
        mock_click.return_value = ClickResult(
            element_id="0/1/2",
            method="action",
            input_injected=True,
            effect_verified=True,
        )
        response = McpResponse()
        elements._click_element(ToolRequest({"element_id": "0/1/2"}), response, ctx)

        assert "0/1/2" in response.text_lines[0]
        ctx.check_boundary.assert_called_once_with("0/1/2")
        ctx.record_action.assert_called_once()
        structured = response.to_tool_result().structuredContent
        assert structured["method"] == "action"

    def test_click_boundary_violation(self, ctx) -> None:
        ctx.check_boundary.side_effect = ValueError("Outside boundary")
        response = McpResponse()

        with pytest.raises(ValueError, match="Outside boundary"):
            elements._click_element(ToolRequest({"element_id": "0/1/2"}), response, ctx)


class TestSetElementText:
    @patch("gnome_ui_mcp.adapters.elements.set_element_text")
    def test_set_text_success(self, mock_set_text, ctx) -> None:
        response = McpResponse()

        elements._set_element_text(
            ToolRequest({"element_id": "0/1/2", "text": "hello"}),
            response,
            ctx,
        )

        mock_set_text.assert_called_once_with(element_id="0/1/2", text="hello")
        ctx.check_boundary.assert_called_once_with("0/1/2")
        ctx.record_action.assert_called_once()

    def test_set_text_boundary_violation(self, ctx) -> None:
        ctx.check_boundary.side_effect = ValueError("Outside boundary")
        response = McpResponse()

        with pytest.raises(ValueError, match="Outside boundary"):
            elements._set_element_text(
                ToolRequest({"element_id": "0/1/2", "text": "hello"}),
                response,
                ctx,
            )


class TestSetElementValue:
    @patch("gnome_ui_mcp.adapters.elements.set_element_value")
    def test_set_value_success(self, mock_set_value, ctx) -> None:
        response = McpResponse()

        elements._set_element_value(
            ToolRequest({"element_id": "0/1/2", "value": 42.0}),
            response,
            ctx,
        )

        mock_set_value.assert_called_once_with(element_id="0/1/2", value=42.0)
        ctx.check_boundary.assert_called_once_with("0/1/2")
        ctx.record_action.assert_called_once()

    def test_set_value_boundary_violation(self, ctx) -> None:
        ctx.check_boundary.side_effect = ValueError("Outside boundary")
        response = McpResponse()

        with pytest.raises(ValueError, match="Outside boundary"):
            elements._set_element_value(
                ToolRequest({"element_id": "0/1/2", "value": 42.0}),
                response,
                ctx,
            )


class TestGetFocusedElement:
    @patch("gnome_ui_mcp.adapters.elements.get_focused_element")
    def test_returns_focused(self, mock_gfe, ctx) -> None:
        mock_gfe.return_value = {"name": "Save Button", "role": "push button", "id": "0/1/2"}
        response = McpResponse()
        elements._get_focused_element(ToolRequest({}), response, ctx)

        assert "Save Button" in response.text_lines[0]
        structured = response.to_tool_result().structuredContent
        assert structured["name"] == "Save Button"
