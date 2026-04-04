"""State management tools."""

from __future__ import annotations

from dataclasses import asdict

from ..adapters import state
from ..adapters.state import ActionHistoryResult
from ..formatters.state_formatter import ActionHistoryFormatter
from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory
from .tool_definition import ToolRequest, define_tool

# -- snapshot_state --


def _snapshot_state(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    result = state.snapshot_state()
    response.set_data("snapshot_id", result.snapshot_id)
    response.append_text(f"Captured state snapshot: {result.snapshot_id}")


snapshot_state = define_tool(
    name="snapshot_state",
    description="Capture a snapshot of the current desktop state.",
    handler=_snapshot_state,
    category=ToolCategory.STATE,
)


# -- compare_state --


def _compare_state(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    before_id = request.params.get("before_id", "")
    after_id = request.params.get("after_id", "")
    result = state.compare_state(before_id=before_id, after_id=after_id)
    response.set_data("apps_added", result.apps_added)
    response.set_data("apps_removed", result.apps_removed)
    response.set_data("windows_added", result.windows_added)
    response.set_data("windows_removed", result.windows_removed)
    response.set_data("focus_changed", result.focus_changed)
    response.set_data("popups_changed", result.popups_changed)
    total_changes = (
        len(result.apps_added)
        + len(result.apps_removed)
        + len(result.windows_added)
        + len(result.windows_removed)
        + int(result.focus_changed)
        + int(result.popups_changed)
    )
    response.append_text(f"Compared snapshots: {total_changes} changes found.")


compare_state = define_tool(
    name="compare_state",
    description="Compare two desktop state snapshots and return changes.",
    handler=_compare_state,
    category=ToolCategory.STATE,
    parameters={
        "before_id": {"type": "string", "description": "Snapshot ID for before state."},
        "after_id": {"type": "string", "description": "Snapshot ID for after state."},
    },
)


# -- set_boundaries --


def _set_boundaries(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    app_name = request.params.get("app_name", None)
    allow_global_keys = request.params.get("allow_global_keys", None)
    context.set_boundary(app_name, allow_keys=allow_global_keys)
    response.append_text(f"Boundaries set for app: {app_name or 'none'}")


set_boundaries = define_tool(
    name="set_boundaries",
    description="Restrict automation to a specific application.",
    handler=_set_boundaries,
    category=ToolCategory.STATE,
    read_only=False,
    parameters={
        "app_name": {
            "type": "string",
            "default": None,
            "description": "Application name to restrict automation to.",
        },
        "allow_global_keys": {
            "type": "array",
            "items_type": "string",
            "default": None,
            "description": "Key combos allowed outside the boundary.",
        },
    },
)


# -- clear_boundaries --


def _clear_boundaries(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    context.clear_boundary()
    response.append_text("Automation boundaries cleared.")


clear_boundaries = define_tool(
    name="clear_boundaries",
    description="Remove automation boundaries.",
    handler=_clear_boundaries,
    category=ToolCategory.STATE,
    read_only=False,
)


# -- get_action_history --


def _get_action_history(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    last_n = request.params.get("last_n", 10)
    records = context.get_history(last_n=last_n)
    actions = [asdict(r) for r in records]
    result = ActionHistoryResult(actions=actions, count=context.history_count)
    fmt = ActionHistoryFormatter(result)
    response.set_items("actions", fmt.to_json())
    response.set_data("count", result.count)
    response.append_text(fmt.to_string())


get_action_history = define_tool(
    name="get_action_history",
    description="Get recent automation actions with undo hints.",
    handler=_get_action_history,
    category=ToolCategory.STATE,
    parameters={
        "last_n": {
            "type": "integer",
            "default": 10,
            "description": "Number of recent actions to return.",
        },
    },
)
