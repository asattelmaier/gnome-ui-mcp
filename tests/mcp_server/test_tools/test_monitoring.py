"""Tests for monitoring tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.adapters.monitoring import EventSubscription, PollResult
from gnome_ui_mcp.mcp_context import McpContext
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.tools import monitoring
from gnome_ui_mcp.tools.tool_definition import ToolRequest


@pytest.fixture()
def ctx() -> McpContext:
    return MagicMock(spec=McpContext)


class TestSubscribeEvents:
    @patch("gnome_ui_mcp.adapters.monitoring.subscribe_events")
    def test_subscribe_success(self, mock_sub, ctx) -> None:
        mock_sub.return_value = EventSubscription(
            subscription_id="sub-123",
            event_types=["focus:"],
        )
        response = McpResponse()
        monitoring._subscribe_events(ToolRequest({"event_types": ["focus:"]}), response, ctx)

        assert "sub-123" in response.text_lines[0]
        structured = response.to_tool_result().structuredContent
        assert structured["subscription_id"] == "sub-123"


class TestPollEvents:
    @patch("gnome_ui_mcp.adapters.monitoring.poll_events")
    def test_poll_success(self, mock_poll, ctx) -> None:
        mock_poll.return_value = PollResult(
            events=[{"type": "focus:", "detail": "button"}],
            count=1,
        )
        response = McpResponse()
        monitoring._poll_events(ToolRequest({"subscription_id": "sub-123"}), response, ctx)

        assert "1 events" in response.text_lines[0]


class TestVisibleShellPopups:
    @patch("gnome_ui_mcp.adapters.monitoring.visible_shell_popups")
    def test_popups_success(self, mock_popups, ctx) -> None:
        mock_popups.return_value = [{"name": "menu"}]
        response = McpResponse()
        monitoring._visible_shell_popups(ToolRequest({}), response, ctx)

        assert "1 visible" in response.text_lines[0]
