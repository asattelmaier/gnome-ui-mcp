from __future__ import annotations

import json
from collections.abc import Callable
from typing import Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent

from . import __version__, backend
from .desktop.types import JsonDict

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
    button: Literal["left", "middle", "right"] = "left",
) -> CallToolResult:
    return _run_tool(
        lambda: backend.click_element(
            element_id=element_id,
            action_name=action_name,
            click_count=click_count,
            button=button,
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


@mcp.tool(
    description=(
        "Smoothly move the mouse cursor from one position to another over a given duration. "
        "Interpolates intermediate positions for natural-looking movement."
    )
)
def mouse_move_smooth(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration_ms: int = 300,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.mouse_move_smooth(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            duration_ms=duration_ms,
        )
    )


@mcp.tool(description="Replace the text contents of an editable element.")
def set_element_text(element_id: str, text: str) -> CallToolResult:
    return _run_tool(lambda: backend.set_element_text(element_id=element_id, text=text))


@mcp.tool(
    description=(
        "Set the numeric value of a slider, spinbutton, or progress bar "
        "via the AT-SPI Value interface."
    )
)
def set_element_value(element_id: str, value: float) -> CallToolResult:
    return _run_tool(lambda: backend.set_element_value(element_id=element_id, value=value))


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


@mcp.tool(
    description=(
        "Navigate a menu hierarchy by sequentially activating each item in the path. "
        "Waits for sub-menus to appear between levels."
    )
)
def navigate_menu(
    menu_path: list[str],
    app_name: str | None = None,
) -> CallToolResult:
    return _run_tool(lambda: backend.navigate_menu(menu_path=menu_path, app_name=app_name))


@mcp.tool(
    description=(
        "Set a file path in a GTK file dialog by sending Ctrl+L to activate the "
        "location entry, typing the path, and pressing Return."
    )
)
def file_dialog_set_path(path: str) -> CallToolResult:
    return _run_tool(lambda: backend.file_dialog_set_path(path=path))


@mcp.tool(description="Dismiss a desktop notification by its ID via D-Bus CloseNotification.")
def dismiss_notification(notification_id: int) -> CallToolResult:
    return _run_tool(lambda: backend.dismiss_notification(notification_id=notification_id))


@mcp.tool(description="Invoke an action on a desktop notification by its ID and action key.")
def click_notification_action(notification_id: int, action_key: str) -> CallToolResult:
    return _run_tool(
        lambda: backend.click_notification_action(
            notification_id=notification_id, action_key=action_key
        )
    )


@mcp.tool(description="Return metadata about the currently focused element.")
def get_focused_element() -> CallToolResult:
    return _run_tool(backend.get_focused_element)


@mcp.tool(description="Expand a tree or expander node if it is currently collapsed.")
def expand_node(element_id: str) -> CallToolResult:
    return _run_tool(lambda: backend.expand_node(element_id=element_id))


@mcp.tool(description="Collapse a tree or expander node if it is currently expanded.")
def collapse_node(element_id: str) -> CallToolResult:
    return _run_tool(lambda: backend.collapse_node(element_id=element_id))


@mcp.tool(
    description=(
        "Select a child item within a container element via the AT-SPI Selection "
        "interface. Use for combo boxes, list boxes, and menus."
    )
)
def select_option(element_id: str, child_index: int) -> CallToolResult:
    return _run_tool(lambda: backend.select_option(element_id=element_id, child_index=child_index))


@mcp.tool(
    description=(
        "Set a toggle button or checkbox to a desired on/off state. "
        "Returns no-op if already in the desired state."
    )
)
def set_toggle_state(element_id: str, desired_state: bool) -> CallToolResult:
    return _run_tool(
        lambda: backend.set_toggle_state(element_id=element_id, desired_state=desired_state)
    )


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


# --- Input tools ---


@mcp.tool(description="Read text from the system clipboard or primary selection.")
def clipboard_read(
    selection: Literal["clipboard", "primary"] = "clipboard",
) -> CallToolResult:
    return _run_tool(lambda: backend.clipboard_read(selection=selection))


@mcp.tool(description="Write text to the system clipboard or primary selection.")
def clipboard_write(
    text: str,
    selection: Literal["clipboard", "primary"] = "clipboard",
) -> CallToolResult:
    return _run_tool(lambda: backend.clipboard_write(text=text, selection=selection))


@mcp.tool(description=("Drag from one screen position to another with smooth interpolation."))
def drag(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    button: Literal["left", "middle", "right"] = "left",
    steps: int = 10,
    duration_ms: int = 300,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.drag(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            button=button,
            steps=steps,
            duration_ms=duration_ms,
        )
    )


@mcp.tool(description="Move cursor to an element's center without clicking.")
def hover_element(element_id: str) -> CallToolResult:
    return _run_tool(lambda: backend.hover_element(element_id=element_id))


# --- OCR and vision tools ---


@mcp.tool(
    description=(
        "Extract text from the screen or a region using OCR. Use for apps with poor accessibility."
    )
)
def ocr_screen(
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> CallToolResult:
    return _run_tool(lambda: backend.ocr_screen(x=x, y=y, width=width, height=height))


@mcp.tool(description="Find text on screen via OCR and return its coordinates.")
def find_text_ocr(
    target: str,
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.find_text_ocr(target=target, x=x, y=y, width=width, height=height)
    )


@mcp.tool(description="Find text on screen via OCR and click it.")
def click_text_ocr(
    target: str,
    button: Literal["left", "middle", "right"] = "left",
) -> CallToolResult:
    return _run_tool(lambda: backend.click_text_ocr(target=target, button=button))


@mcp.tool(
    description=("Find an input field by label text and type into it. AT-SPI first, OCR fallback.")
)
def type_into(
    label: str,
    text: str,
    submit: bool = False,
) -> CallToolResult:
    return _run_tool(lambda: backend.type_into(label=label, text=text, submit=submit))


@mcp.tool(description="Analyze a screenshot using a vision language model.")
def analyze_screenshot(
    prompt: str,
    provider: Literal["openrouter", "anthropic", "ollama"] = "openrouter",
    model: str | None = None,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.analyze_screenshot(prompt=prompt, provider=provider, model=model)
    )


@mcp.tool(description="Compare two screenshots using a vision language model.")
def compare_screenshots(
    image_path_1: str,
    image_path_2: str,
    prompt: str | None = None,
    provider: Literal["openrouter", "anthropic", "ollama"] = "openrouter",
    model: str | None = None,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.compare_screenshots(
            image_path_1=image_path_1,
            image_path_2=image_path_2,
            prompt=prompt,
            provider=provider,
            model=model,
        )
    )


@mcp.tool(description="Get the pixel color at screen coordinates.")
def get_pixel_color(x: int, y: int) -> CallToolResult:
    return _run_tool(lambda: backend.get_pixel_color(x=x, y=y))


@mcp.tool(description="Get the average color of a screen region.")
def get_region_color(x: int, y: int, width: int, height: int) -> CallToolResult:
    return _run_tool(lambda: backend.get_region_color(x=x, y=y, width=width, height=height))


@mcp.tool(description="Compare two screenshots and return changed regions.")
def visual_diff(
    image_path_1: str,
    image_path_2: str,
    threshold: int = 30,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.visual_diff(
            image_path_1=image_path_1,
            image_path_2=image_path_2,
            threshold=threshold,
        )
    )


# --- System integration tools ---


@mcp.tool(description="Call any D-Bus method on the session bus.")
def dbus_call(
    bus_name: str,
    object_path: str,
    interface: str,
    method: str,
    signature: str | None = None,
    args: list | None = None,
    timeout_ms: int = 5000,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.dbus_call(
            bus_name=bus_name,
            object_path=object_path,
            interface=interface,
            method=method,
            signature=signature,
            args=args,
            timeout_ms=timeout_ms,
        )
    )


@mcp.tool(
    description=("List all connected monitors with resolution, position, scale, and hardware info.")
)
def list_monitors() -> CallToolResult:
    return _run_tool(backend.list_monitors)


@mcp.tool(description="Read a GNOME setting value.")
def gsettings_get(schema: str, key: str) -> CallToolResult:
    return _run_tool(lambda: backend.gsettings_get(schema=schema, key=key))


@mcp.tool(description="Write a GNOME setting value.")
def gsettings_set(schema: str, key: str, value: str | int | float | bool) -> CallToolResult:
    return _run_tool(lambda: backend.gsettings_set(schema=schema, key=key, value=value))


@mcp.tool(description="List all keys in a GSettings schema.")
def gsettings_list_keys(schema: str) -> CallToolResult:
    return _run_tool(lambda: backend.gsettings_list_keys(schema=schema))


@mcp.tool(description="Reset a GNOME setting to its default value.")
def gsettings_reset(schema: str, key: str) -> CallToolResult:
    return _run_tool(lambda: backend.gsettings_reset(schema=schema, key=key))


@mcp.tool(description="Start monitoring desktop notifications.")
def notification_monitor_start() -> CallToolResult:
    return _run_tool(backend.notification_monitor_start)


@mcp.tool(description="Read captured notifications since monitoring started.")
def notification_monitor_read(clear: bool = True) -> CallToolResult:
    return _run_tool(lambda: backend.notification_monitor_read(clear=clear))


@mcp.tool(description="Stop monitoring desktop notifications.")
def notification_monitor_stop() -> CallToolResult:
    return _run_tool(backend.notification_monitor_stop)


@mcp.tool(description="Start recording the screen or a region to video.")
def screen_record_start(
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
    framerate: int = 30,
    draw_cursor: bool = True,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.screen_record_start(
            x=x,
            y=y,
            width=width,
            height=height,
            framerate=framerate,
            draw_cursor=draw_cursor,
        )
    )


@mcp.tool(description="Stop recording and optionally convert to GIF.")
def screen_record_stop(
    to_gif: bool = False,
    gif_fps: int = 10,
    gif_width: int = 640,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.screen_record_stop(to_gif=to_gif, gif_fps=gif_fps, gif_width=gif_width)
    )


@mcp.tool(description="List Wayland protocols available in the session.")
def wayland_protocols(filter_protocol: str | None = None) -> CallToolResult:
    return _run_tool(lambda: backend.wayland_protocols(filter_protocol=filter_protocol))


# --- Workspace and window management tools ---


@mcp.tool(description="Switch to a workspace by direction.")
def switch_workspace(
    direction: Literal["up", "down"],
) -> CallToolResult:
    return _run_tool(lambda: backend.switch_workspace(direction=direction))


@mcp.tool(description="Move the focused window to another workspace.")
def move_window_to_workspace(
    direction: Literal["up", "down"],
) -> CallToolResult:
    return _run_tool(lambda: backend.move_window_to_workspace(direction=direction))


@mcp.tool(description="List workspaces and their windows.")
def list_workspaces() -> CallToolResult:
    return _run_tool(backend.list_workspaces)


@mcp.tool(description="Toggle the GNOME Activities overview.")
def toggle_overview(active: bool | None = None) -> CallToolResult:
    return _run_tool(lambda: backend.toggle_overview(active=active))


@mcp.tool(description="Close the focused window.")
def close_window() -> CallToolResult:
    return _run_tool(backend.close_window)


@mcp.tool(description="Move the focused window by pixel offset.")
def move_window(dx: int, dy: int) -> CallToolResult:
    return _run_tool(lambda: backend.move_window(dx=dx, dy=dy))


@mcp.tool(description="Resize the focused window by pixel offset.")
def resize_window(dw: int, dh: int) -> CallToolResult:
    return _run_tool(lambda: backend.resize_window(dw=dw, dh=dh))


@mcp.tool(description="Snap the focused window to a position.")
def snap_window(
    position: Literal["maximize", "restore", "left", "right"],
) -> CallToolResult:
    return _run_tool(lambda: backend.snap_window(position=position))


@mcp.tool(description="Toggle the focused window's state.")
def toggle_window_state(
    state: Literal["fullscreen", "maximize", "minimize"],
) -> CallToolResult:
    return _run_tool(lambda: backend.toggle_window_state(state=state))


# --- App management tools ---


@mcp.tool(description="List installed desktop applications.")
def list_desktop_apps(
    query: str = "",
    include_hidden: bool = False,
    max_results: int = 50,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.list_desktop_apps(
            query=query,
            include_hidden=include_hidden,
            max_results=max_results,
        )
    )


@mcp.tool(description="Launch an application by desktop ID.")
def launch_app(desktop_id: str) -> CallToolResult:
    return _run_tool(lambda: backend.launch_app(desktop_id=desktop_id))


@mcp.tool(description="Launch an application with stdout/stderr capture.")
def launch_with_logging(command: str) -> CallToolResult:
    return _run_tool(lambda: backend.launch_with_logging(command=command))


@mcp.tool(description="Read stdout/stderr of a launched application by PID.")
def read_app_log(pid: int, last_n_lines: int = 0) -> CallToolResult:
    return _run_tool(lambda: backend.read_app_log(pid=pid, last_n_lines=last_n_lines))
