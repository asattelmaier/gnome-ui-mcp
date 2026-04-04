"""Tests for app management tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.adapters.apps import (
    AppLog,
    DesktopApp,
    DesktopAppList,
    LaunchResult,
    LaunchWithLoggingResult,
)
from gnome_ui_mcp.mcp_context import McpContext
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.tools import apps
from gnome_ui_mcp.tools.tool_definition import ToolRequest


@pytest.fixture()
def ctx() -> McpContext:
    return MagicMock(spec=McpContext)


class TestListDesktopApps:
    @patch("gnome_ui_mcp.adapters.apps.list_desktop_apps")
    def test_list_success(self, mock_list, ctx) -> None:
        mock_list.return_value = DesktopAppList(
            apps=[
                DesktopApp(
                    desktop_id="org.gnome.Calculator.desktop",
                    name="Calculator",
                    description="",
                    executable="gnome-calculator",
                    categories="",
                    icon=None,
                ),
            ],
            count=1,
        )
        response = McpResponse()
        apps._list_desktop_apps(ToolRequest({"query": "calc"}), response, ctx)

        assert "1 desktop" in response.text_lines[0]
        structured = response.to_tool_result().structuredContent
        assert structured["count"] == 1
        assert len(structured["apps"]) == 1


class TestLaunchApp:
    @patch("gnome_ui_mcp.adapters.apps.launch_app")
    def test_launch_success(self, mock_launch, ctx) -> None:
        mock_launch.return_value = LaunchResult(
            desktop_id="org.gnome.Calculator.desktop",
            name="Calculator",
            executable="gnome-calculator",
        )
        response = McpResponse()
        apps._launch_app(ToolRequest({"desktop_id": "org.gnome.Calculator.desktop"}), response, ctx)

        assert "Calculator" in response.text_lines[0]
        structured = response.to_tool_result().structuredContent
        assert structured["desktop_id"] == "org.gnome.Calculator.desktop"


class TestLaunchWithLogging:
    @patch("gnome_ui_mcp.adapters.apps.launch_with_logging")
    def test_launch_with_logging(self, mock_launch, ctx) -> None:
        mock_launch.return_value = LaunchWithLoggingResult(pid=1234, command="ls")
        response = McpResponse()
        apps._launch_with_logging(ToolRequest({"command": "ls"}), response, ctx)

        assert "1234" in response.text_lines[0]
        structured = response.to_tool_result().structuredContent
        assert structured["pid"] == 1234


class TestReadAppLog:
    @patch("gnome_ui_mcp.adapters.apps.read_app_log")
    def test_read_log(self, mock_read, ctx) -> None:
        mock_read.return_value = AppLog(
            pid=1234,
            command="ls",
            running=True,
            exit_code=None,
            stdout="output",
            stderr="",
        )
        response = McpResponse()
        apps._read_app_log(ToolRequest({"pid": 1234}), response, ctx)

        structured = response.to_tool_result().structuredContent
        assert structured["pid"] == 1234
        assert structured["stdout"] == "output"


class TestCloseApp:
    @patch("gnome_ui_mcp.adapters.apps.close_app")
    def test_close_success(self, mock_close, ctx) -> None:
        response = McpResponse()
        apps._close_app(ToolRequest({"app_name": "Calculator"}), response, ctx)

        assert "Calculator" in response.text_lines[0]
        mock_close.assert_called_once_with(app_name="Calculator")


class TestKillApp:
    @patch("gnome_ui_mcp.adapters.apps.kill_app")
    def test_kill_success(self, mock_kill, ctx) -> None:
        response = McpResponse()
        apps._kill_app(ToolRequest({"app_name": "Calculator"}), response, ctx)

        assert "Calculator" in response.text_lines[0]
        mock_kill.assert_called_once_with(app_name="Calculator")

    @patch("gnome_ui_mcp.adapters.apps.kill_app")
    def test_kill_failure_raises(self, mock_kill, ctx) -> None:
        mock_kill.side_effect = ValueError("Could not find PID")
        response = McpResponse()
        with pytest.raises(ValueError, match="Could not find PID"):
            apps._kill_app(ToolRequest({"app_name": "Missing"}), response, ctx)
