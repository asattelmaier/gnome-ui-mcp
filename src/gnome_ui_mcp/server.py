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
    description="Return the accessibility tree for the whole desktop or a specific application."
)
def accessibility_tree(
    app_name: str | None = None,
    max_depth: int = 4,
    include_actions: bool = False,
    include_text: bool = False,
) -> CallToolResult:
    return _run_tool(
        lambda: backend.accessibility_tree(
            app_name=app_name,
            max_depth=max_depth,
            include_actions=include_actions,
            include_text=include_text,
        )
    )


@mcp.tool(
    description=(
        "Search accessible elements by text and optional role filter, with optional clickable "
        "and bounds filters."
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
def click_element(element_id: str, action_name: str | None = None) -> CallToolResult:
    return _run_tool(
        lambda: backend.click_element(
            element_id=element_id,
            action_name=action_name,
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
        "Click at absolute screen coordinates and report input injection plus any observable "
        "effect verification."
    )
)
def click_at(
    x: int,
    y: int,
    button: Literal["left", "middle", "right"] = "left",
) -> CallToolResult:
    return _run_tool(lambda: backend.click_at(x=x, y=y, button=button))


@mcp.tool(description="Replace the text contents of an editable element.")
def set_element_text(element_id: str, text: str) -> CallToolResult:
    return _run_tool(lambda: backend.set_element_text(element_id=element_id, text=text))


@mcp.tool(description="Type text into the currently focused element.")
def type_text(text: str) -> CallToolResult:
    return _run_tool(lambda: backend.type_text(text=text))


@mcp.tool(description="Press and release a key by GDK key name, for example Return or Escape.")
def press_key(key_name: str) -> CallToolResult:
    return _run_tool(lambda: backend.press_key(key_name=key_name))


@mcp.tool(description="Capture the current GNOME desktop to a PNG file.")
def screenshot(filename: str | None = None) -> CallToolResult:
    return _run_tool(lambda: backend.screenshot(filename=filename))


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


@mcp.tool(
    description=(
        "Poll the accessibility tree until a matching element appears or the timeout expires."
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
        )
    )


@mcp.tool(
    description=(
        "Poll the accessibility tree until a matching element disappears or the timeout expires."
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
        )
    )
