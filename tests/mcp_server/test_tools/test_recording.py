"""Tests for recording tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.adapters.recording import RecordingStartResult, RecordingStopResult
from gnome_ui_mcp.mcp_context import McpContext
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.tools import recording
from gnome_ui_mcp.tools.tool_definition import ToolRequest


@pytest.fixture()
def ctx() -> McpContext:
    return MagicMock(spec=McpContext)


class TestScreenRecordStart:
    @patch("gnome_ui_mcp.adapters.recording.screen_record_start")
    def test_start_success(self, mock_start, ctx) -> None:
        mock_start.return_value = RecordingStartResult(path="/tmp/rec.webm")
        response = McpResponse()
        recording._screen_record_start(ToolRequest({}), response, ctx)

        assert "/tmp/rec.webm" in response.text_lines[0]
        structured = response.to_tool_result().structuredContent
        assert structured["path"] == "/tmp/rec.webm"


class TestScreenRecordStop:
    @patch("gnome_ui_mcp.adapters.recording.screen_record_stop")
    def test_stop_success(self, mock_stop, ctx) -> None:
        mock_stop.return_value = RecordingStopResult(path="/tmp/rec.webm", gif_path=None)
        response = McpResponse()
        recording._screen_record_stop(ToolRequest({}), response, ctx)

        assert "/tmp/rec.webm" in response.text_lines[0]
