"""Window management tools."""

from __future__ import annotations

from ..adapters import window_mgmt
from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory
from .tool_definition import ToolRequest, define_tool

# -- close_window --


def _close_window(request: ToolRequest, response: McpResponse, context: McpContext) -> None:
    window_mgmt.close_window()
    response.append_text("Closed the focused window.")


close_window = define_tool(
    name="close_window",
    description="Close the currently focused window via Alt+F4.",
    handler=_close_window,
    category=ToolCategory.WINDOW,
    read_only=False,
)


# -- move_window --


def _move_window(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    dx = request.params.get("dx", 0)
    dy = request.params.get("dy", 0)
    window_mgmt.move_window(dx, dy)
    response.set_data("dx", dx)
    response.set_data("dy", dy)
    response.append_text(f"Moved window by ({dx}, {dy}).")


move_window = define_tool(
    name="move_window",
    description="Move the focused window by a pixel offset using keyboard move mode.",
    handler=_move_window,
    category=ToolCategory.WINDOW,
    read_only=False,
    parameters={
        "dx": {"type": "integer", "description": "Horizontal offset in pixels."},
        "dy": {"type": "integer", "description": "Vertical offset in pixels."},
    },
)


# -- resize_window --


def _resize_window(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    dw = request.params.get("dw", 0)
    dh = request.params.get("dh", 0)
    window_mgmt.resize_window(dw, dh)
    response.set_data("dw", dw)
    response.set_data("dh", dh)
    response.append_text(f"Resized window by ({dw}, {dh}).")


resize_window = define_tool(
    name="resize_window",
    description="Resize the focused window by a pixel delta using keyboard resize mode.",
    handler=_resize_window,
    category=ToolCategory.WINDOW,
    read_only=False,
    parameters={
        "dw": {"type": "integer", "description": "Width change in pixels."},
        "dh": {"type": "integer", "description": "Height change in pixels."},
    },
)


# -- snap_window --


def _snap_window(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    position = request.params.get("position", "maximize")
    window_mgmt.snap_window(position)
    response.set_data("position", position)
    response.append_text(f"Snapped window to {position}.")


snap_window = define_tool(
    name="snap_window",
    description="Snap the focused window to a screen position.",
    handler=_snap_window,
    category=ToolCategory.WINDOW,
    read_only=False,
    parameters={
        "position": {
            "type": "string",
            "default": "maximize",
            "description": "Snap position.",
            "enum": ["maximize", "restore", "left", "right"],
        },
    },
)


# -- toggle_window_state --


def _toggle_window_state(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    state = request.params.get("state", "maximize")
    window_mgmt.toggle_window_state(state)
    response.set_data("state", state)
    response.append_text(f"Toggled window state: {state}.")


toggle_window_state = define_tool(
    name="toggle_window_state",
    description="Toggle the focused window's state.",
    handler=_toggle_window_state,
    category=ToolCategory.WINDOW,
    read_only=False,
    parameters={
        "state": {
            "type": "string",
            "default": "maximize",
            "description": "Window state to toggle.",
            "enum": ["fullscreen", "maximize", "minimize"],
        },
    },
)
