"""Session isolation and file dialog tools."""

from __future__ import annotations

from ..adapters import session
from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory
from .tool_definition import ToolRequest, define_tool

# -- session_start --


def _session_start(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    width = request.params.get("width", 1920)
    height = request.params.get("height", 1080)
    result = session.session_start(width=width, height=height)
    response.set_data("pid", result.pid)
    response.set_data("bus_address", result.bus_address)
    response.set_data("width", result.width)
    response.set_data("height", result.height)
    response.set_data("already_running", result.already_running)
    response.append_text(f"Session started at {width}x{height}. Bus: {result.bus_address}")


session_start = define_tool(
    name="session_start",
    description=(
        "Start an isolated GNOME Shell session via gnome-shell --headless. "
        "Creates a private D-Bus session with its own display and input."
    ),
    handler=_session_start,
    category=ToolCategory.SESSION,
    read_only=False,
    parameters={
        "width": {
            "type": "integer",
            "default": 1920,
            "description": "Display width in pixels.",
        },
        "height": {
            "type": "integer",
            "default": 1080,
            "description": "Display height in pixels.",
        },
    },
)


# -- session_stop --


def _session_stop(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    session.session_stop()
    response.append_text("Isolated session stopped.")


session_stop = define_tool(
    name="session_stop",
    description="Stop the isolated GNOME Shell session.",
    handler=_session_stop,
    category=ToolCategory.SESSION,
    read_only=False,
)


# -- session_info --


def _session_info(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    result = session.session_info()
    response.set_data("running", result.running)
    response.set_data("pid", result.pid)
    response.set_data("bus_address", result.bus_address)
    response.set_data("width", result.width)
    response.set_data("height", result.height)
    response.append_text(f"Session {'running' if result.running else 'not running'}.")


session_info = define_tool(
    name="session_info",
    description="Get information about the current isolated session.",
    handler=_session_info,
    category=ToolCategory.SESSION,
)


# -- file_dialog_set_path --


def _file_dialog_set_path(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    path = request.params.get("path", "")
    session.file_dialog_set_path(path=path)
    response.append_text(f"File dialog path set to: {path}")


file_dialog_set_path = define_tool(
    name="file_dialog_set_path",
    description=(
        "Set a file path in a GTK file dialog by sending Ctrl+L to activate "
        "the location entry, typing the path, and pressing Return."
    ),
    handler=_file_dialog_set_path,
    category=ToolCategory.SESSION,
    read_only=False,
    parameters={
        "path": {
            "type": "string",
            "description": "File path to set in the dialog.",
        },
    },
)
