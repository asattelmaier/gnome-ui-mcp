"""Tests for system tools (ping)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.mcp_context import McpContext, RemoteDesktopBackend, ScreenshotBackend
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.tools import system
from gnome_ui_mcp.tools.tool_definition import ToolRequest


class TestPing:
    @patch("gnome_ui_mcp.adapters.accessibility.list_applications")
    def test_ping_populates_response(self, mock_apps) -> None:
        from gnome_ui_mcp.adapters.accessibility import AppInfo

        mock_apps.return_value = [
            AppInfo(id="0", name="Firefox", role="application", children=2),
            AppInfo(id="1", name="Terminal", role="application", children=1),
        ]

        ctx = MagicMock(spec=McpContext)
        ctx.desktop_count.return_value = 1
        ctx.screenshot_backend.return_value = ScreenshotBackend(
            available=True,
            backend="dbus",
        )
        ctx.remote_desktop_backend.return_value = RemoteDesktopBackend(
            available=True,
            version=1,
        )

        response = McpResponse()
        system._ping(ToolRequest({}), response, ctx)

        assert response.is_error is False
        assert "2 applications" in response.text_lines[0]

        structured = response.to_tool_result().structuredContent
        assert structured["desktop_count"] == 1
        assert structured["application_count"] == 2
        assert structured["screenshot"]["available"] is True
