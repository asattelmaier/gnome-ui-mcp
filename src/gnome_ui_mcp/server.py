from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent

from . import __version__, backend

JsonDict = dict[str, Any]

mcp = FastMCP(
    name="gnome-ui-mcp",
    instructions=(
        "Use the GNOME accessibility stack to inspect and control the current desktop session."
    ),
)


def _to_tool_result(response: JsonDict) -> CallToolResult:
    is_error = response.get("success") is False
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(response, indent=2))],
        structuredContent=response,
        isError=is_error,
        _meta={"serverVersion": __version__},
    )


def _run_tool(operation: Callable[[], JsonDict]) -> CallToolResult:
    try:
        return _to_tool_result(operation())
    except Exception as exc:
        return _to_tool_result({"success": False, "error": str(exc)})


@mcp.tool(description="Return basic health information for the desktop backend.")
def ping() -> CallToolResult:
    return _run_tool(backend.ping)


@mcp.tool(description="List applications currently visible through the AT-SPI desktop tree.")
def list_applications() -> CallToolResult:
    return _run_tool(backend.list_applications)


@mcp.tool(description="List top-level windows across the desktop or for one application.")
def list_windows(app_name: str | None = None) -> CallToolResult:
    return _run_tool(lambda: backend.list_windows(app_name=app_name))


@mcp.tool(
    description=(
        "Return the accessibility tree for the whole desktop or a specific application. "
        "Optionally filter by roles, states, or showing-only."
    )
)
def accessibility_tree(
    app_name: str | None = None,
    max_depth: int = 4,
    include_actions: bool = False,
    include_text: bool = False,
    filter_roles: list[str] | None = None,
    filter_states: list[str] | None = None,
    showing_only: bool = False,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.accessibility_tree(
            app_name=app_name,
            max_depth=max_depth,
            include_actions=include_actions,
            include_text=include_text,
            filter_roles=filter_roles,
            filter_states=filter_states,
            showing_only=showing_only,
        )
    )


@mcp.tool(
    description=(
        "Search accessible elements by text and optional role filter, with optional clickable "
        "and bounds filters, optionally scoped to a subtree or visible popup."
    )
)
def find_elements(
    query: str = "",
    app_name: str | None = None,
    role: str | None = None,
    max_depth: int = 8,
    max_results: int = 20,
    showing_only: bool = True,
    clickable_only: bool = False,
    bounds_only: bool = False,
    within_element_id: str | None = None,
    within_popup: bool = False,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.find_elements(
            query=query,
            app_name=app_name,
            role=role,
            max_depth=max_depth,
            max_results=max_results,
            showing_only=showing_only,
            clickable_only=clickable_only,
            bounds_only=bounds_only,
            within_element_id=within_element_id,
            within_popup=within_popup,
        )
    )


@mcp.tool(description="Focus an element through the AT-SPI component interface.")
def focus_element(element_id: str) -> CallToolResult:
    return _run_tool(lambda: backend.focus_element(element_id=element_id))


@mcp.tool(
    description=(
        "Resolve the nearest actionable ancestor for an element so labels can map to clickable "
        "parents."
    )
)
def resolve_click_target(element_id: str) -> CallToolResult:
    return _run_tool(lambda: backend.resolve_click_target(element_id=element_id))


@mcp.tool(
    description=(
        "Click an element or its resolved clickable ancestor, and report input injection plus "
        "observable effect verification."
    )
)
def click_element(
    element_id: str,
    action_name: str | None = None,
    click_count: Literal[1, 2, 3] = 1,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.click_element(
            element_id=element_id,
            action_name=action_name,
            click_count=click_count,
        )
    )


@mcp.tool(
    description=(
        "Activate an element with action first, then focus plus keyboard, then mouse fallback."
    )
)
def activate_element(element_id: str, action_name: str | None = None) -> CallToolResult:
    return _run_tool(
        lambda: backend.activate_element(
            element_id=element_id,
            action_name=action_name,
        )
    )


@mcp.tool(
    description=(
        "Find the best matching element and activate it, optionally scoped to a subtree or "
        "visible popup."
    )
)
def find_and_activate(
    query: str,
    app_name: str | None = None,
    role: str | None = None,
    max_depth: int = 8,
    showing_only: bool = True,
    clickable_only: bool = False,
    bounds_only: bool = False,
    within_element_id: str | None = None,
    within_popup: bool = False,
    action_name: str | None = None,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.find_and_activate(
            query=query,
            app_name=app_name,
            role=role,
            max_depth=max_depth,
            showing_only=showing_only,
            clickable_only=clickable_only,
            bounds_only=bounds_only,
            within_element_id=within_element_id,
            within_popup=within_popup,
            action_name=action_name,
        )
    )


@mcp.tool(
    description=(
        "Click at absolute screen coordinates and report input injection plus any observable "
        "effect verification."
    )
)
def click_at(
    x: int,
    y: int,
    button: Literal["left", "middle", "right"] = "left",
    click_count: Literal[1, 2, 3] = 1,
) -> CallToolResult:
    return _run_tool(lambda: backend.click_at(x=x, y=y, button=button, click_count=click_count))


@mcp.tool(
    description=(
        "Scroll the mouse wheel at the current pointer position or at given screen "
        "coordinates. Use direction and clicks for discrete mouse-wheel steps."
    )
)
def scroll(
    direction: Literal["up", "down", "left", "right"] = "down",
    clicks: int = 3,
    x: int | None = None,
    y: int | None = None,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.scroll(
            direction=direction,
            clicks=clicks,
            x=x,
            y=y,
        )
    )


@mcp.tool(
    description=(
        "Move the mouse cursor to absolute screen coordinates without clicking. "
        "Useful for hover effects, tooltips, and drag preparation."
    )
)
def mouse_move(x: int, y: int) -> CallToolResult:
    return _run_tool(lambda: backend.mouse_move(x=x, y=y))


@mcp.tool(description="Replace the text contents of an editable element.")
def set_element_text(element_id: str, text: str) -> CallToolResult:
    return _run_tool(lambda: backend.set_element_text(element_id=element_id, text=text))


@mcp.tool(
    description=(
        "Select text within an element using the AT-SPI Text interface. "
        "Provide start_offset and end_offset for a range, or omit both to select all text."
    )
)
def select_element_text(
    element_id: str,
    start_offset: int | None = None,
    end_offset: int | None = None,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.select_element_text(
            element_id=element_id,
            start_offset=start_offset,
            end_offset=end_offset,
        )
    )


@mcp.tool(description="Type text into the currently focused element.")
def type_text(text: str) -> CallToolResult:
    return _run_tool(lambda: backend.type_text(text=text))


@mcp.tool(
    description=(
        "Press and release a key by GDK key name, optionally verifying the effect against a "
        "target element and settled GNOME Shell popup state."
    )
)
def press_key(
    key_name: str,
    element_id: str | None = None,
    settle_timeout_ms: int = 1_500,
    stable_for_ms: int = 250,
    poll_interval_ms: int = 50,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.press_key(
            key_name=key_name,
            element_id=element_id,
            settle_timeout_ms=settle_timeout_ms,
            stable_for_ms=stable_for_ms,
            poll_interval_ms=poll_interval_ms,
        )
    )


@mcp.tool(
    description=(
        "Send a key combination such as ctrl+c, alt+F4, ctrl+shift+t, or super. "
        "Modifiers are pressed in order before the principal key and released in "
        "reverse order after. Optionally verify the effect against a target element."
    )
)
def key_combo(
    combo: str,
    element_id: str | None = None,
    settle_timeout_ms: int = 1_500,
    stable_for_ms: int = 250,
    poll_interval_ms: int = 50,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.key_combo(
            combo=combo,
            element_id=element_id,
            settle_timeout_ms=settle_timeout_ms,
            stable_for_ms=stable_for_ms,
            poll_interval_ms=poll_interval_ms,
        )
    )


@mcp.tool(description="Capture the current GNOME desktop to a PNG file.")
def screenshot(filename: str | None = None) -> CallToolResult:
    return _run_tool(lambda: backend.screenshot(filename=filename))


@mcp.tool(description="Capture a rectangular region of the screen to a PNG file.")
def screenshot_area(
    x: int,
    y: int,
    width: int,
    height: int,
    filename: str | None = None,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.screenshot_area(x=x, y=y, width=width, height=height, filename=filename)
    )


@mcp.tool(
    description=(
        "Capture a window to a PNG file. Focuses the window by element_id first, "
        "then captures the currently focused window via D-Bus ScreenshotWindow."
    )
)
def screenshot_window(
    window_element_id: str,
    include_frame: bool = True,
    include_cursor: bool = False,
    filename: str | None = None,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.screenshot_window(
            window_element_id=window_element_id,
            include_frame=include_frame,
            include_cursor=include_cursor,
            filename=filename,
        )
    )


@mcp.tool(description="Return the deepest visible element at a given screen coordinate.")
def element_at_point(
    x: int,
    y: int,
    app_name: str | None = None,
    max_depth: int = 10,
    include_click_target: bool = True,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.element_at_point(
            x=x,
            y=y,
            app_name=app_name,
            max_depth=max_depth,
            include_click_target=include_click_target,
        )
    )


@mcp.tool(description="Return visible GNOME Shell popup or menu containers.")
def visible_shell_popups() -> CallToolResult:
    return _run_tool(backend.visible_shell_popups)


@mcp.tool(description="Poll the GNOME Shell until the number of visible popups matches a count.")
def wait_for_popup_count(
    count: int,
    timeout_ms: int = 5_000,
    poll_interval_ms: int = 100,
    max_depth: int = 10,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.wait_for_popup_count(
            count=count,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
            max_depth=max_depth,
        )
    )


@mcp.tool(description="Poll until GNOME Shell popup state has stayed unchanged for a short time.")
def wait_for_shell_settled(
    timeout_ms: int = 1_500,
    stable_for_ms: int = 250,
    poll_interval_ms: int = 50,
    max_depth: int = 10,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.wait_for_shell_settled(
            timeout_ms=timeout_ms,
            stable_for_ms=stable_for_ms,
            poll_interval_ms=poll_interval_ms,
            max_depth=max_depth,
        )
    )


@mcp.tool(
    description=(
        "Poll the accessibility tree until a matching element appears or the timeout expires, "
        "optionally scoped to a subtree or visible popup."
    )
)
def wait_for_element(
    query: str,
    app_name: str | None = None,
    role: str | None = None,
    timeout_ms: int = 5_000,
    poll_interval_ms: int = 250,
    showing_only: bool = True,
    clickable_only: bool = False,
    bounds_only: bool = False,
    within_element_id: str | None = None,
    within_popup: bool = False,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.wait_for_element(
            query=query,
            app_name=app_name,
            role=role,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
            showing_only=showing_only,
            clickable_only=clickable_only,
            bounds_only=bounds_only,
            within_element_id=within_element_id,
            within_popup=within_popup,
        )
    )


@mcp.tool(
    description=(
        "Poll the accessibility tree until a matching element disappears or the timeout "
        "expires, optionally scoped to a subtree or visible popup."
    )
)
def wait_for_element_gone(
    query: str,
    app_name: str | None = None,
    role: str | None = None,
    timeout_ms: int = 5_000,
    poll_interval_ms: int = 250,
    showing_only: bool = True,
    clickable_only: bool = False,
    bounds_only: bool = False,
    within_element_id: str | None = None,
    within_popup: bool = False,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.wait_for_element_gone(
            query=query,
            app_name=app_name,
            role=role,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
            showing_only=showing_only,
            clickable_only=clickable_only,
            bounds_only=bounds_only,
            within_element_id=within_element_id,
            within_popup=within_popup,
        )
    )


@mcp.tool(description="Return metadata about the currently focused element.")
def get_focused_element() -> CallToolResult:
    return _run_tool(backend.get_focused_element)


@mcp.tool(
    description=(
        "Return extended AT-SPI properties for an element: value, selection, "
        "relations, attributes, and image info."
    )
)
def get_element_properties(element_id: str) -> CallToolResult:
    return _run_tool(lambda: backend.get_element_properties(element_id=element_id))


@mcp.tool(
    description=(
        "Return detailed text information for an element: full text, caret offset, "
        "selections, and text attributes at the caret position."
    )
)
def get_element_text(element_id: str) -> CallToolResult:
    return _run_tool(lambda: backend.get_element_text(element_id=element_id))


@mcp.tool(description="Return table dimensions, column headers, and caption for a table element.")
def get_table_info(element_id: str) -> CallToolResult:
    return _run_tool(lambda: backend.get_table_info(element_id=element_id))


@mcp.tool(description="Return information about a specific cell in a table element.")
def get_table_cell(element_id: str, row: int, col: int) -> CallToolResult:
    return _run_tool(lambda: backend.get_table_cell(element_id=element_id, row=row, col=col))


@mcp.tool(description="Return the ancestry chain from root to a given element as a list of nodes.")
def get_element_path(element_id: str) -> CallToolResult:
    return _run_tool(lambda: backend.get_element_path(element_id=element_id))


@mcp.tool(
    description=(
        "Resolve multiple element IDs in one call, returning summaries for found "
        "elements and a list of missing IDs."
    )
)
def get_elements_by_ids(element_ids: list[str]) -> CallToolResult:
    return _run_tool(lambda: backend.get_elements_by_ids(element_ids=element_ids))


# Phase 7b: Wait/action patterns


@mcp.tool(description="Wait for an application to appear in the AT-SPI tree.")
def wait_for_app(
    app_name: str,
    timeout_ms: int = 10000,
    poll_interval_ms: int = 250,
    require_window: bool = True,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.wait_for_app(
            app_name=app_name,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
            require_window=require_window,
        )
    )


@mcp.tool(description="Wait for a window to appear.")
def wait_for_window(
    query: str,
    app_name: str | None = None,
    role: str | None = None,
    timeout_ms: int = 10000,
    poll_interval_ms: int = 250,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.wait_for_window(
            query=query,
            app_name=app_name,
            role=role,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
        )
    )


@mcp.tool(
    description=("Wait for an element to appear, then act on it. Atomic wait+act in one MCP call.")
)
def wait_and_act(
    wait_query: str,
    wait_role: str | None = None,
    wait_app_name: str | None = None,
    then_action: Literal["activate", "click", "focus", "set_text"] = "activate",
    then_query: str | None = None,
    then_role: str | None = None,
    then_text: str | None = None,
    timeout_ms: int = 5000,
    poll_interval_ms: int = 250,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.wait_and_act(
            wait_query=wait_query,
            wait_role=wait_role,
            wait_app_name=wait_app_name,
            then_action=then_action,
            then_query=then_query,
            then_role=then_role,
            then_text=then_text,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
        )
    )


@mcp.tool(description="Scroll an element into view if it is off-screen.")
def scroll_to_element(
    element_id: str,
    max_scrolls: int = 20,
    scroll_clicks: int = 3,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.scroll_to_element(
            element_id=element_id,
            max_scrolls=max_scrolls,
            scroll_clicks=scroll_clicks,
        )
    )


# Phase 7c: Assertions, events, snapshots, boundaries, history


@mcp.tool(
    description=(
        "Assert that an element exists with expected states. "
        "Returns pass/fail with structured checks."
    )
)
def assert_element(
    query: str,
    app_name: str | None = None,
    role: str | None = None,
    expected_states: list[str] | None = None,
    unexpected_states: list[str] | None = None,
    timeout_ms: int = 3000,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.assert_element(
            query=query,
            app_name=app_name,
            role=role,
            expected_states=expected_states,
            unexpected_states=unexpected_states,
            timeout_ms=timeout_ms,
        )
    )


@mcp.tool(description="Assert that an element's text matches expected value.")
def assert_text(
    element_id: str,
    expected: str,
    match: Literal["exact", "contains", "startswith", "regex"] = "contains",
) -> CallToolResult:
    return _run_tool(
        lambda: backend.assert_text(
            element_id=element_id,
            expected=expected,
            match=match,
        )
    )


@mcp.tool(description="Subscribe to AT-SPI events. Returns subscription ID.")
def subscribe_events(
    event_types: list[str],
    app_name: str | None = None,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.subscribe_events(
            event_types=event_types,
            app_name=app_name,
        )
    )


@mcp.tool(description="Poll for captured AT-SPI events.")
def poll_events(
    subscription_id: str,
    timeout_ms: int = 5000,
    max_events: int = 100,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.poll_events(
            subscription_id=subscription_id,
            timeout_ms=timeout_ms,
            max_events=max_events,
        )
    )


@mcp.tool(description="Unsubscribe from AT-SPI events.")
def unsubscribe_events(subscription_id: str) -> CallToolResult:
    return _run_tool(lambda: backend.unsubscribe_events(subscription_id=subscription_id))


@mcp.tool(description="Capture a snapshot of the current desktop state.")
def snapshot_state() -> CallToolResult:
    return _run_tool(backend.snapshot_state)


@mcp.tool(description="Compare two desktop state snapshots and return changes.")
def compare_state(before_id: str, after_id: str) -> CallToolResult:
    return _run_tool(lambda: backend.compare_state(before_id=before_id, after_id=after_id))


@mcp.tool(description="Restrict automation to a specific application.")
def set_boundaries(
    app_name: str | None = None,
    allow_global_keys: list[str] | None = None,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.set_boundaries(
            app_name=app_name,
            allow_global_keys=allow_global_keys,
        )
    )


@mcp.tool(description="Remove automation boundaries.")
def clear_boundaries() -> CallToolResult:
    return _run_tool(backend.clear_boundaries)


@mcp.tool(description="Get recent automation actions with undo hints.")
def get_action_history(last_n: int = 10) -> CallToolResult:
    return _run_tool(lambda: backend.get_action_history(last_n=last_n))


# Phase 7d: Utilities


@mcp.tool(
    description=(
        "Take a screenshot with a colored rectangle highlighting an element for visual debugging."
    )
)
def highlight_element(
    element_id: str,
    color: str = "red",
    label: str | None = None,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.highlight_element(
            element_id=element_id,
            color=color,
            label=label,
        )
    )


@mcp.tool(description="Get the current keyboard layout.")
def get_keyboard_layout() -> CallToolResult:
    return _run_tool(backend.get_keyboard_layout)


@mcp.tool(description="List valid key names by category.")
def list_key_names(
    category: Literal["navigation", "function", "modifier", "editing", "all"] = "all",
) -> CallToolResult:
    return _run_tool(lambda: backend.list_key_names(category=category))


@mcp.tool(description="Get which monitor contains a screen coordinate.")
def get_monitor_for_point(x: int, y: int) -> CallToolResult:
    return _run_tool(lambda: backend.get_monitor_for_point(x=x, y=y))


# Session isolation


@mcp.tool(
    description=(
        "Start an isolated GNOME Shell session via gnome-shell --headless. "
        "Creates a private D-Bus session with its own display and input."
    )
)
def session_start(width: int = 1920, height: int = 1080) -> CallToolResult:
    return _run_tool(lambda: backend.session_start(width=width, height=height))


@mcp.tool(description="Stop the isolated GNOME Shell session.")
def session_stop() -> CallToolResult:
    return _run_tool(backend.session_stop)


@mcp.tool(description="Get information about the current isolated session.")
def session_info() -> CallToolResult:
    return _run_tool(backend.session_info)
