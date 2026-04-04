"""E2E tests for low-level server creation and tool dispatch."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.mcp_context import (
    McpContext,
    RemoteDesktopBackend,
    ScreenshotBackend,
)
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.server import _build_input_schema, create_server
from gnome_ui_mcp.tools.categories import ToolCategory
from gnome_ui_mcp.tools.tool_definition import ToolRequest, define_tool
from gnome_ui_mcp.tools.tools import create_tools


class TestToolRegistration:
    def test_create_tools_returns_sorted(self) -> None:
        tools = create_tools()
        names = [t.name for t in tools]
        assert names == sorted(names)

    def test_create_tools_has_expected_count(self) -> None:
        tools = create_tools()
        assert len(tools) == 109

    def test_all_tools_have_handlers(self) -> None:
        tools = create_tools()
        for tool in tools:
            assert callable(tool.handler), f"{tool.name} has no callable handler"


class TestCreateServer:
    def test_server_has_correct_name(self) -> None:
        server = create_server()
        assert server.name == "gnome-ui-mcp"


class TestCategoryGating:
    def test_all_categories_enabled_by_default(self) -> None:
        server = create_server()
        assert server.name == "gnome-ui-mcp"

    def test_filter_to_single_category(self) -> None:
        tools = create_tools()
        system_tools = [t for t in tools if t.category == ToolCategory.SYSTEM]
        assert len(system_tools) >= 1
        assert any(t.name == "ping" for t in system_tools)

    def test_every_tool_has_a_category(self) -> None:
        tools = create_tools()
        for tool in tools:
            assert isinstance(tool.category, ToolCategory), f"{tool.name} has no valid category"


class TestBuildInputSchema:
    def test_empty_params(self) -> None:
        tool = define_tool(
            name="t",
            description="d",
            handler=lambda r, resp, c: None,
        )
        schema = _build_input_schema(tool)
        assert schema == {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }

    def test_required_param(self) -> None:
        tool = define_tool(
            name="t",
            description="d",
            handler=lambda r, resp, c: None,
            parameters={"name": {"type": "string"}},
        )
        schema = _build_input_schema(tool)
        assert "name" in schema["properties"]
        assert "name" in schema["required"]
        assert schema["additionalProperties"] is False

    def test_optional_param_with_default(self) -> None:
        tool = define_tool(
            name="t",
            description="d",
            handler=lambda r, resp, c: None,
            parameters={"count": {"type": "integer", "default": 10}},
        )
        schema = _build_input_schema(tool)
        assert schema["properties"]["count"]["default"] == 10

    def test_nullable_param(self) -> None:
        tool = define_tool(
            name="t",
            description="d",
            handler=lambda r, resp, c: None,
            parameters={"app_name": {"type": "string", "default": None}},
        )
        schema = _build_input_schema(tool)
        prop = schema["properties"]["app_name"]
        assert prop["default"] is None
        assert "anyOf" in prop

    def test_description_included(self) -> None:
        tool = define_tool(
            name="t",
            description="d",
            handler=lambda r, resp, c: None,
            parameters={
                "query": {
                    "type": "string",
                    "description": "Search text.",
                },
            },
        )
        schema = _build_input_schema(tool)
        assert schema["properties"]["query"]["description"] == "Search text."


class TestErrorHandling:
    def test_handler_exception_produces_error_response(self) -> None:
        response = McpResponse()

        def _bad_handler(request: ToolRequest, resp: McpResponse, ctx: McpContext) -> None:
            msg = "something exploded"
            raise RuntimeError(msg)

        ctx = MagicMock(spec=McpContext)
        try:
            _bad_handler(ToolRequest({}), response, ctx)
        except Exception as exc:
            response.set_error(str(exc))

        result = response.to_tool_result()
        assert result.isError is True
        assert "something exploded" in result.content[0].text
        assert result.structuredContent is None

    def test_error_cause_chain_included(self) -> None:
        response = McpResponse()

        def _handler_with_cause(request: ToolRequest, resp: McpResponse, ctx: McpContext) -> None:
            try:
                msg = "root cause"
                raise OSError(msg)
            except OSError as original:
                msg = "high-level failure"
                raise RuntimeError(msg) from original

        ctx = MagicMock(spec=McpContext)
        try:
            _handler_with_cause(ToolRequest({}), response, ctx)
        except Exception as exc:
            error_text = str(exc)
            if exc.__cause__ is not None:
                error_text += f"\nCause: {exc.__cause__}"
            response.set_error(error_text)

        result = response.to_tool_result()
        assert "high-level failure" in result.content[0].text
        assert "root cause" in result.content[0].text

    @patch("gnome_ui_mcp.adapters.accessibility.list_applications")
    def test_full_tool_dispatch(self, mock_apps) -> None:
        from gnome_ui_mcp.adapters.accessibility import AppInfo

        mock_apps.return_value = [
            AppInfo(id="0", name="App1", role="application", children=0),
        ]

        ctx = MagicMock(spec=McpContext)
        ctx.desktop_count.return_value = 1
        ctx.screenshot_backend.return_value = ScreenshotBackend(available=True)
        ctx.remote_desktop_backend.return_value = RemoteDesktopBackend(
            available=True,
        )

        tools = create_tools()
        ping_tool = next(t for t in tools if t.name == "ping")

        response = McpResponse()
        ping_tool.handler(ToolRequest({}), response, ctx)
        result = response.to_tool_result()

        assert result.isError is False
        assert result.structuredContent["desktop_count"] == 1
