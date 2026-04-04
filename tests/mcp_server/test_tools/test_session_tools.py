"""Tests for session tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.adapters.session import SessionInfo, SessionStartResult
from gnome_ui_mcp.mcp_context import McpContext
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.tools import session_tools
from gnome_ui_mcp.tools.tool_definition import ToolRequest


@pytest.fixture()
def ctx() -> McpContext:
    return MagicMock(spec=McpContext)


class TestSessionStart:
    @patch("gnome_ui_mcp.adapters.session.session_start")
    def test_start_success(self, mock_start, ctx) -> None:
        mock_start.return_value = SessionStartResult(
            pid=1234,
            bus_address="unix:abstract=/tmp/dbus-test",
            width=1920,
            height=1080,
            already_running=False,
        )
        response = McpResponse()
        session_tools._session_start(ToolRequest({}), response, ctx)

        assert "1920x1080" in response.text_lines[0]
        structured = response.to_tool_result().structuredContent
        assert structured["pid"] == 1234


class TestSessionInfo:
    @patch("gnome_ui_mcp.adapters.session.session_info")
    def test_info_running(self, mock_info, ctx) -> None:
        mock_info.return_value = SessionInfo(
            running=True,
            pid=1234,
            bus_address="unix:abstract=/tmp/dbus-test",
            width=1920,
            height=1080,
        )
        response = McpResponse()
        session_tools._session_info(ToolRequest({}), response, ctx)

        assert "running" in response.text_lines[0]


class TestFileDialogSetPath:
    @patch("gnome_ui_mcp.adapters.session.file_dialog_set_path")
    def test_set_path_success(self, mock_set, ctx) -> None:
        response = McpResponse()
        session_tools._file_dialog_set_path(
            ToolRequest({"path": "/home/user/file.txt"}), response, ctx
        )

        assert "/home/user/file.txt" in response.text_lines[0]
