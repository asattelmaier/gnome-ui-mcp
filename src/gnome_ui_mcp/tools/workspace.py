"""Workspace management tools."""

from __future__ import annotations

from ..adapters import workspaces
from ..formatters.workspace_formatter import WorkspaceListFormatter
from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory
from .tool_definition import ToolRequest, define_tool

# -- switch_workspace --


def _switch_workspace(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    direction = request.params.get("direction", "down")
    workspaces.switch_workspace(direction)
    response.append_text(f"Switched workspace {direction}.")


switch_workspace = define_tool(
    name="switch_workspace",
    description="Switch to an adjacent workspace.",
    handler=_switch_workspace,
    category=ToolCategory.WORKSPACE,
    read_only=False,
    parameters={
        "direction": {
            "type": "string",
            "default": "down",
            "description": "Direction to switch.",
            "enum": ["up", "down"],
        },
    },
)


# -- move_window_to_workspace --


def _move_window_to_workspace(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    direction = request.params.get("direction", "down")
    workspaces.move_window_to_workspace(direction)
    response.append_text(f"Moved window to workspace {direction}.")


move_window_to_workspace = define_tool(
    name="move_window_to_workspace",
    description="Move the focused window to an adjacent workspace.",
    handler=_move_window_to_workspace,
    category=ToolCategory.WORKSPACE,
    read_only=False,
    parameters={
        "direction": {
            "type": "string",
            "default": "down",
            "description": "Direction to move.",
            "enum": ["up", "down"],
        },
    },
)


# -- list_workspaces --


def _list_workspaces(request: ToolRequest, response: McpResponse, context: McpContext) -> None:
    ws = workspaces.list_workspaces()
    fmt = WorkspaceListFormatter(ws)
    response.set_items("workspaces", fmt.to_json())
    response.set_data("workspace_count", len(ws))
    response.append_text(fmt.to_string())


list_workspaces = define_tool(
    name="list_workspaces",
    description="List all workspaces with their windows.",
    handler=_list_workspaces,
    category=ToolCategory.WORKSPACE,
)


# -- toggle_overview --


def _toggle_overview(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    active = request.params.get("active", None)
    new_state = workspaces.toggle_overview(active)
    response.set_data("overview_active", new_state)
    response.append_text(
        f"Overview {'activated' if new_state else 'deactivated'}.",
    )


toggle_overview = define_tool(
    name="toggle_overview",
    description="Toggle the GNOME Shell activities overview.",
    handler=_toggle_overview,
    category=ToolCategory.WORKSPACE,
    read_only=False,
    parameters={
        "active": {
            "type": "boolean",
            "default": None,
            "description": "Set overview state. Defaults to True if omitted.",
        },
    },
)
