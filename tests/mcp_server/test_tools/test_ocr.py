"""Tests for OCR tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.adapters.state import OcrResult
from gnome_ui_mcp.mcp_context import McpContext
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.tools import ocr
from gnome_ui_mcp.tools.tool_definition import ToolRequest


@pytest.fixture()
def ctx() -> McpContext:
    return MagicMock(spec=McpContext)


class TestOcrScreen:
    @patch("gnome_ui_mcp.adapters.state.ocr_screen")
    def test_ocr_success(self, mock_ocr, ctx) -> None:
        mock_ocr.return_value = OcrResult(
            text="Hello World",
            words=[],
            word_count=2,
            screenshot_path="/tmp/s.png",
        )
        response = McpResponse()
        ocr._ocr_screen(ToolRequest({}), response, ctx)

        assert "11 characters" in response.text_lines[0]
