"""Tests for workspace tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.adapters.workspaces import Workspace, WorkspaceWindow
from gnome_ui_mcp.mcp_context import McpContext
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.tools import workspace
from gnome_ui_mcp.tools.tool_definition import ToolRequest


@pytest.fixture()
def ctx() -> McpContext:
    return MagicMock(spec=McpContext)


class TestSwitchWorkspace:
    @patch("gnome_ui_mcp.adapters.workspaces.switch_workspace")
    def test_switch_down(self, mock_sw, ctx) -> None:
        response = McpResponse()
        workspace._switch_workspace(ToolRequest({"direction": "down"}), response, ctx)

        assert response.is_error is False
        assert "down" in response.text_lines[0]
        mock_sw.assert_called_once_with("down")

    @patch("gnome_ui_mcp.adapters.workspaces.switch_workspace")
    def test_invalid_direction_raises(self, mock_sw, ctx) -> None:
        mock_sw.side_effect = ValueError("direction must be")
        response = McpResponse()
        with pytest.raises(ValueError, match="direction must be"):
            workspace._switch_workspace(ToolRequest({"direction": "sideways"}), response, ctx)


class TestListWorkspaces:
    @patch("gnome_ui_mcp.adapters.workspaces.list_workspaces")
    def test_returns_workspaces_via_formatter(self, mock_lw, ctx) -> None:
        mock_lw.return_value = [
            Workspace(
                index=0,
                windows=[
                    WorkspaceWindow(title="Firefox", app_id="firefox", wm_class="firefox"),
                ],
            ),
            Workspace(index=1, windows=[]),
        ]
        response = McpResponse()
        workspace._list_workspaces(ToolRequest({}), response, ctx)

        structured = response.to_tool_result().structuredContent
        assert structured["workspace_count"] == 2
        assert len(structured["workspaces"]) == 2
        assert "2 workspaces" in response.text_lines[0]


class TestToggleOverview:
    @patch("gnome_ui_mcp.adapters.workspaces.toggle_overview")
    def test_activate(self, mock_to, ctx) -> None:
        mock_to.return_value = True
        response = McpResponse()
        workspace._toggle_overview(ToolRequest({"active": True}), response, ctx)

        structured = response.to_tool_result().structuredContent
        assert structured["overview_active"] is True
        assert "activated" in response.text_lines[0]
