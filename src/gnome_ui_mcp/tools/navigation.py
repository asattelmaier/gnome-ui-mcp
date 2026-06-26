"""Navigation core: snapshot-driven, uid-addressed interaction.

This is the blessed surface for navigating GNOME: capture a snapshot to get
stable element uids, then click/fill/hover/fill_form those uids. Every action
auto-waits for the shell to settle and can attach a fresh snapshot
(``include_snapshot``) so the agent sees the result in one turn.

The lower-level, path-id-based tools in ``elements``/``input`` remain available
as advanced building blocks; this module is what most automation should use.
"""

from __future__ import annotations

from ..adapters import elements
from ..formatters.snapshot_formatter import SnapshotFormatter
from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory
from .tool_definition import ToolRequest, define_tool


def _attach_snapshot(response: McpResponse, context: McpContext) -> None:
    """Capture a fresh snapshot and append it to the response."""
    snapshot = context.take_snapshot()
    fmt = SnapshotFormatter(snapshot)
    response.set_data("snapshot_id", snapshot.id)
    response.set_items("elements", fmt.to_json())
    response.append_text("")
    response.append_text(fmt.to_string())


# -- take_snapshot --


def _take_snapshot(request: ToolRequest, response: McpResponse, context: McpContext) -> None:
    window = request.params.get("window", None)
    app_name = request.params.get("app_name", None)
    max_depth = request.params.get("max_depth", None)

    snapshot = context.take_snapshot(window_id=window, app_name=app_name, max_depth=max_depth)
    if window is not None:
        context.select_window(window)

    fmt = SnapshotFormatter(snapshot)
    response.set_data("snapshot_id", snapshot.id)
    response.set_data("scope", snapshot.scope)
    response.set_items("elements", fmt.to_json())
    response.append_text(fmt.to_string())


take_snapshot = define_tool(
    name="take_snapshot",
    description=(
        "Capture a snapshot of the accessibility tree and assign every element a "
        "stable uid. Reference these uids in click, fill, hover, and fill_form. "
        "Defaults to the active window; pass 'window' (from list_windows) or "
        "'app_name' to scope it. Taking a new snapshot invalidates older uids."
    ),
    handler=_take_snapshot,
    category=ToolCategory.NAVIGATION,
    parameters={
        "window": {
            "type": "string",
            "default": None,
            "description": "Window id from list_windows. Defaults to the active window.",
        },
        "app_name": {
            "type": "string",
            "default": None,
            "description": "Snapshot this application instead of a single window.",
        },
        "max_depth": {
            "type": "integer",
            "default": None,
            "description": "Maximum tree depth to capture.",
        },
    },
)


# -- select_window --


def _select_window(request: ToolRequest, response: McpResponse, context: McpContext) -> None:
    window = request.params.get("window", "")
    focused = False
    focus_error: str | None = None
    try:
        elements.focus_element(element_id=window)
        focused = True
    except Exception as exc:  # best-effort: AT-SPI focus on a frame may not work
        focus_error = str(exc)

    context.select_window(window)
    response.set_data("selected_window", window)
    response.set_data("focused", focused)
    if focus_error is not None:
        response.set_data("focus_error", focus_error)
    response.append_text(
        f"Selected window {window} as the snapshot scope"
        + (" and focused it." if focused else " (focus not confirmed).")
    )


select_window = define_tool(
    name="select_window",
    description=(
        "Choose a window (from list_windows) as the implicit scope for take_snapshot, "
        "and try to focus it. Subsequent take_snapshot calls without a 'window' argument "
        "capture this window."
    ),
    handler=_select_window,
    category=ToolCategory.NAVIGATION,
    read_only=False,
    parameters={
        "window": {"type": "string", "description": "Window id from list_windows."},
    },
)


# -- click --


def _click(request: ToolRequest, response: McpResponse, context: McpContext) -> None:
    uid = request.params.get("uid", "")
    dbl_click = request.params.get("dbl_click", False)
    include_snapshot = request.params.get("include_snapshot", False)

    element_id = context.resolve_uid(uid)
    context.check_boundary(element_id)
    result = elements.click_element(
        element_id=element_id, click_count=2 if dbl_click else 1, settle=True
    )
    context.record_action("click", {"uid": uid}, element_id=element_id)

    response.set_data("uid", uid)
    response.set_data("method", result.method)
    response.set_data("input_injected", result.input_injected)
    response.set_data("effect_verified", result.effect_verified)
    response.append_text(f"Clicked uid {uid}.")
    if include_snapshot:
        _attach_snapshot(response, context)


click = define_tool(
    name="click",
    description=(
        "Click the element referenced by a uid from the latest snapshot. "
        "Auto-waits for the UI to settle and reports effect verification."
    ),
    handler=_click,
    category=ToolCategory.INPUT,
    read_only=False,
    parameters={
        "uid": {"type": "string", "description": "Element uid from the latest snapshot."},
        "dbl_click": {
            "type": "boolean",
            "default": False,
            "description": "Set true for a double click.",
        },
        "include_snapshot": {
            "type": "boolean",
            "default": False,
            "description": "Attach a fresh snapshot of the result to the response.",
        },
    },
)


# -- fill --


def _fill(request: ToolRequest, response: McpResponse, context: McpContext) -> None:
    uid = request.params.get("uid", "")
    value = request.params.get("value", "")
    include_snapshot = request.params.get("include_snapshot", False)

    element_id = context.resolve_uid(uid)
    context.check_boundary(element_id)
    result = elements.fill_element(element_id=element_id, value=value)
    context.record_action("fill", {"uid": uid, "value": value}, element_id=element_id)

    response.set_data("uid", uid)
    response.set_data("method", result.method)
    response.set_data("input_injected", result.input_injected)
    response.set_data("effect_verified", result.effect_verified)
    response.append_text(f"Filled uid {uid}.")
    if include_snapshot:
        _attach_snapshot(response, context)


fill = define_tool(
    name="fill",
    description=(
        "Type text into an input, or set a checkbox/radio/switch from a boolean "
        "value (true/false), for the element referenced by a uid from the latest "
        "snapshot. Auto-waits for the UI to settle."
    ),
    handler=_fill,
    category=ToolCategory.INPUT,
    read_only=False,
    parameters={
        "uid": {"type": "string", "description": "Element uid from the latest snapshot."},
        "value": {
            "type": "string",
            "description": "Text to type, or 'true'/'false' for toggles.",
        },
        "include_snapshot": {
            "type": "boolean",
            "default": False,
            "description": "Attach a fresh snapshot of the result to the response.",
        },
    },
)


# -- hover --


def _hover(request: ToolRequest, response: McpResponse, context: McpContext) -> None:
    uid = request.params.get("uid", "")
    include_snapshot = request.params.get("include_snapshot", False)

    element_id = context.resolve_uid(uid)
    context.check_boundary(element_id)
    elements.hover_element(element_id=element_id)
    context.record_action("hover", {"uid": uid}, element_id=element_id)

    response.set_data("uid", uid)
    response.append_text(f"Hovered uid {uid}.")
    if include_snapshot:
        _attach_snapshot(response, context)


hover = define_tool(
    name="hover",
    description=(
        "Move the pointer over the element referenced by a uid from the latest "
        "snapshot (e.g. to reveal a hover menu or tooltip)."
    ),
    handler=_hover,
    category=ToolCategory.INPUT,
    read_only=False,
    parameters={
        "uid": {"type": "string", "description": "Element uid from the latest snapshot."},
        "include_snapshot": {
            "type": "boolean",
            "default": False,
            "description": "Attach a fresh snapshot of the result to the response.",
        },
    },
)


# -- fill_form --


def _fill_form(request: ToolRequest, response: McpResponse, context: McpContext) -> None:
    raw_fields = request.params.get("fields", [])
    if not isinstance(raw_fields, list) or not raw_fields:
        raise ValueError("fill_form requires a non-empty 'fields' list of {uid, value} objects.")

    include_snapshot = request.params.get("include_snapshot", False)
    results: list[dict[str, object]] = []

    for index, field in enumerate(raw_fields):
        if not isinstance(field, dict) or "uid" not in field or "value" not in field:
            raise ValueError(f"fields[{index}] must be an object with 'uid' and 'value'.")
        uid = str(field["uid"])
        value = str(field["value"])
        element_id = context.resolve_uid(uid)
        context.check_boundary(element_id)
        result = elements.fill_element(element_id=element_id, value=value)
        results.append(
            {
                "uid": uid,
                "method": result.method,
                "input_injected": result.input_injected,
                "effect_verified": result.effect_verified,
            }
        )

    context.record_action("fill_form", {"count": len(results)})
    response.set_items("results", results)
    response.append_text(f"Filled {len(results)} fields.")
    if include_snapshot:
        _attach_snapshot(response, context)


fill_form = define_tool(
    name="fill_form",
    description=(
        "Fill multiple elements in one call from a list of {uid, value} objects "
        "(uids from the latest snapshot). Prefer this over repeated fill calls for "
        "forms: fewer round trips. Auto-waits for the UI to settle."
    ),
    handler=_fill_form,
    category=ToolCategory.INPUT,
    read_only=False,
    parameters={
        "fields": {
            "type": "array",
            "items_type": "object",
            "description": "List of {uid, value} objects to fill, in order.",
        },
        "include_snapshot": {
            "type": "boolean",
            "default": False,
            "description": "Attach a fresh snapshot of the result to the response.",
        },
    },
)
