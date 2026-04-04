"""Tests for discovery tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.adapters.accessibility import AppInfo, WindowInfo
from gnome_ui_mcp.mcp_context import McpContext
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.tools import discovery
from gnome_ui_mcp.tools.tool_definition import ToolRequest


@pytest.fixture()
def ctx() -> McpContext:
    return MagicMock(spec=McpContext)


class TestListApplications:
    @patch("gnome_ui_mcp.adapters.accessibility.list_applications")
    def test_returns_items_with_formatted_text(self, mock_la, ctx) -> None:
        mock_la.return_value = [
            AppInfo(id="0", name="Firefox", role="application", children=2),
            AppInfo(id="1", name="Terminal", role="application", children=1),
        ]
        response = McpResponse()
        discovery._list_applications(ToolRequest({}), response, ctx)

        structured = response.to_tool_result().structuredContent
        assert len(structured["applications"]) == 2
        assert structured["applications"][0]["name"] == "Firefox"
        assert "2 applications" in response.text_lines[0]

    @patch("gnome_ui_mcp.adapters.accessibility.list_applications")
    def test_empty_list(self, mock_la, ctx) -> None:
        mock_la.return_value = []
        response = McpResponse()
        discovery._list_applications(ToolRequest({}), response, ctx)

        structured = response.to_tool_result().structuredContent
        assert structured["applications"] == []
        assert "No applications found" in response.text_lines[0]


class TestListWindows:
    @patch("gnome_ui_mcp.adapters.accessibility.list_windows")
    def test_returns_windows_with_formatted_text(self, mock_lw, ctx) -> None:
        mock_lw.return_value = [
            WindowInfo(
                id="0/0",
                name="My Window",
                role="frame",
                application="Firefox",
            ),
        ]
        response = McpResponse()
        discovery._list_windows(ToolRequest({"app_name": "Firefox"}), response, ctx)

        structured = response.to_tool_result().structuredContent
        assert len(structured["windows"]) == 1
        mock_lw.assert_called_once_with("Firefox")


class TestAccessibilityTree:
    @patch("gnome_ui_mcp.adapters.accessibility.accessibility_tree")
    def test_returns_trees(self, mock_at, ctx) -> None:
        mock_at.return_value = [{"name": "Firefox", "children": []}]
        response = McpResponse()
        discovery._accessibility_tree(ToolRequest({"app_name": "Firefox"}), response, ctx)

        structured = response.to_tool_result().structuredContent
        assert len(structured["trees"]) == 1

    @patch("gnome_ui_mcp.adapters.accessibility.accessibility_tree")
    def test_error_raises(self, mock_at, ctx) -> None:
        mock_at.side_effect = ValueError("No application matched 'Nonexistent'")
        response = McpResponse()
        with pytest.raises(ValueError, match="No application matched"):
            discovery._accessibility_tree(ToolRequest({"app_name": "Nonexistent"}), response, ctx)


class TestFindElements:
    @patch("gnome_ui_mcp.adapters.accessibility.find_elements")
    def test_returns_matches(self, mock_fe, ctx) -> None:
        mock_fe.return_value = [{"id": "0/1/2", "name": "Save"}]
        response = McpResponse()
        discovery._find_elements(ToolRequest({"query": "Save"}), response, ctx)

        structured = response.to_tool_result().structuredContent
        assert len(structured["matches"]) == 1

    @patch("gnome_ui_mcp.adapters.accessibility.find_elements")
    def test_empty_results(self, mock_fe, ctx) -> None:
        mock_fe.return_value = []
        response = McpResponse()
        discovery._find_elements(ToolRequest({"query": "Nonexistent"}), response, ctx)

        structured = response.to_tool_result().structuredContent
        assert structured["matches"] == []
