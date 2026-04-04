"""System tools: ping, health checks."""

from __future__ import annotations

from dataclasses import asdict

from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory
from .tool_definition import ToolRequest, define_tool


def _ping(request: ToolRequest, response: McpResponse, context: McpContext) -> None:
    from ..adapters import accessibility

    apps = accessibility.list_applications()

    response.set_data("desktop_count", context.desktop_count())
    response.set_data("application_count", len(apps))
    response.set_data("screenshot", asdict(context.screenshot_backend()))
    response.set_data("mutter_remote_desktop", asdict(context.remote_desktop_backend()))
    response.append_text(f"Desktop ready: {len(apps)} applications running.")


ping = define_tool(
    name="ping",
    description="Return basic health information for the desktop backend.",
    handler=_ping,
    category=ToolCategory.SYSTEM,
)
