"""Tests for state tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.adapters.state import SnapshotResult
from gnome_ui_mcp.mcp_context import McpContext
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.tools import state
from gnome_ui_mcp.tools.tool_definition import ToolRequest


@pytest.fixture()
def ctx() -> McpContext:
    return MagicMock(spec=McpContext)


class TestSnapshotState:
    @patch("gnome_ui_mcp.adapters.state.snapshot_state")
    def test_snapshot_success(self, mock_snap, ctx) -> None:
        mock_snap.return_value = SnapshotResult(snapshot_id="snap-1")
        response = McpResponse()
        state._snapshot_state(ToolRequest({}), response, ctx)

        assert "snap-1" in response.text_lines[0]
        structured = response.to_tool_result().structuredContent
        assert structured["snapshot_id"] == "snap-1"


class TestSetBoundaries:
    def test_set_success(self, ctx) -> None:
        response = McpResponse()
        state._set_boundaries(ToolRequest({"app_name": "Firefox"}), response, ctx)

        assert "Firefox" in response.text_lines[0]
        ctx.set_boundary.assert_called_once_with("Firefox", allow_keys=None)
