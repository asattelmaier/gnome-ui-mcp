"""Tests for waiting and assertion tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.adapters.waiting import (
    AssertElementResult,
    WaitForAppResult,
    WaitForElementResult,
)
from gnome_ui_mcp.mcp_context import McpContext
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.tools import waiting
from gnome_ui_mcp.tools.tool_definition import ToolRequest


@pytest.fixture()
def ctx() -> McpContext:
    return MagicMock(spec=McpContext)


class TestWaitForElement:
    @patch("gnome_ui_mcp.adapters.waiting.wait_for_element")
    def test_wait_success(self, mock_wait, ctx) -> None:
        mock_wait.return_value = WaitForElementResult(
            element={"id": "0/1/2", "name": "Save"},
        )
        response = McpResponse()
        waiting._wait_for_element(ToolRequest({"query": "Save"}), response, ctx)

        assert "Save" in response.text_lines[0]

    @patch("gnome_ui_mcp.adapters.waiting.wait_for_element")
    def test_wait_timeout(self, mock_wait, ctx) -> None:
        mock_wait.side_effect = ValueError("Timeout")
        response = McpResponse()
        with pytest.raises(ValueError, match="Timeout"):
            waiting._wait_for_element(ToolRequest({"query": "Missing"}), response, ctx)


class TestAssertElement:
    @patch("gnome_ui_mcp.adapters.waiting.assert_element")
    def test_assert_passed(self, mock_assert, ctx) -> None:
        mock_assert.return_value = AssertElementResult(
            passed=True, checks=[], element={"id": "0/1/2"}
        )
        response = McpResponse()
        waiting._assert_element(ToolRequest({"query": "Save"}), response, ctx)

        assert "passed" in response.text_lines[0]

    @patch("gnome_ui_mcp.adapters.waiting.assert_element")
    def test_assert_failed(self, mock_assert, ctx) -> None:
        mock_assert.return_value = AssertElementResult(passed=False, checks=[], element=None)
        response = McpResponse()
        waiting._assert_element(ToolRequest({"query": "Missing"}), response, ctx)

        assert "failed" in response.text_lines[0]


class TestWaitForApp:
    @patch("gnome_ui_mcp.adapters.waiting.wait_for_app")
    def test_wait_for_app_success(self, mock_wait, ctx) -> None:
        mock_wait.return_value = WaitForAppResult(
            app_id="0",
            waited_ms=100,
            windows=[],
        )
        response = McpResponse()
        waiting._wait_for_app(ToolRequest({"app_name": "Firefox"}), response, ctx)

        assert "Firefox" in response.text_lines[0]
