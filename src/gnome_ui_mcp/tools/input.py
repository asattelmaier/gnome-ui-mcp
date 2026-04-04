"""Input tools: mouse, keyboard, clipboard, drag, scroll."""

from __future__ import annotations

from ..adapters import input_actions
from ..desktop.types import SettleOptions
from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory
from .tool_definition import ToolRequest, define_tool

# -- click_at --


def _click_at(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    x = request.params.get("x", 0)
    y = request.params.get("y", 0)
    button = request.params.get("button", "left")
    click_count = request.params.get("click_count", 1)
    result = input_actions.click_at(x=x, y=y, button=button, click_count=click_count)
    context.record_action("click_at", {"x": x, "y": y, "button": button})
    response.set_result(result)
    response.append_text(f"Clicked at ({x}, {y}) with {button} button.")


click_at = define_tool(
    name="click_at",
    description=(
        "Click at absolute screen coordinates and report input injection "
        "plus any observable effect verification."
    ),
    handler=_click_at,
    category=ToolCategory.INPUT,
    read_only=False,
    parameters={
        "x": {"type": "integer", "description": "X screen coordinate."},
        "y": {"type": "integer", "description": "Y screen coordinate."},
        "button": {
            "type": "string",
            "default": "left",
            "description": "Mouse button.",
            "enum": ["left", "middle", "right"],
        },
        "click_count": {
            "type": "integer",
            "default": 1,
            "description": "Number of clicks (1=single, 2=double, 3=triple).",
        },
    },
)


# -- mouse_move --


def _mouse_move(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    x = request.params.get("x", 0)
    y = request.params.get("y", 0)
    input_actions.mouse_move(x=x, y=y)
    response.append_text(f"Mouse moved to ({x}, {y}).")


mouse_move = define_tool(
    name="mouse_move",
    description=(
        "Move the mouse cursor to absolute screen coordinates without clicking. "
        "Useful for hover effects, tooltips, and drag preparation."
    ),
    handler=_mouse_move,
    category=ToolCategory.INPUT,
    read_only=False,
    parameters={
        "x": {"type": "integer", "description": "X screen coordinate."},
        "y": {"type": "integer", "description": "Y screen coordinate."},
    },
)


# -- mouse_move_relative --


def _mouse_move_relative(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    dx = request.params.get("dx", 0.0)
    dy = request.params.get("dy", 0.0)
    input_actions.mouse_move_relative(dx=dx, dy=dy)
    response.append_text(f"Mouse moved by ({dx}, {dy}) relative offset.")


mouse_move_relative = define_tool(
    name="mouse_move_relative",
    description=(
        "Move the mouse cursor by a relative offset (dx, dy) from its current position. "
        "Useful when absolute coordinates are not known."
    ),
    handler=_mouse_move_relative,
    category=ToolCategory.INPUT,
    read_only=False,
    parameters={
        "dx": {"type": "number", "description": "Horizontal offset in pixels."},
        "dy": {"type": "number", "description": "Vertical offset in pixels."},
    },
)


# -- mouse_move_smooth --


def _mouse_move_smooth(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    start_x = request.params.get("start_x", 0)
    start_y = request.params.get("start_y", 0)
    end_x = request.params.get("end_x", 0)
    end_y = request.params.get("end_y", 0)
    duration_ms = request.params.get("duration_ms", 300)
    input_actions.mouse_move_smooth(
        start_x=start_x,
        start_y=start_y,
        end_x=end_x,
        end_y=end_y,
        duration_ms=duration_ms,
    )
    response.append_text(f"Mouse smoothly moved from ({start_x}, {start_y}) to ({end_x}, {end_y}).")


mouse_move_smooth = define_tool(
    name="mouse_move_smooth",
    description=(
        "Smoothly move the mouse cursor from one position to another over a given duration. "
        "Interpolates intermediate positions for natural-looking movement."
    ),
    handler=_mouse_move_smooth,
    category=ToolCategory.INPUT,
    read_only=False,
    parameters={
        "start_x": {"type": "integer", "description": "Starting X coordinate."},
        "start_y": {"type": "integer", "description": "Starting Y coordinate."},
        "end_x": {"type": "integer", "description": "Ending X coordinate."},
        "end_y": {"type": "integer", "description": "Ending Y coordinate."},
        "duration_ms": {
            "type": "integer",
            "default": 300,
            "description": "Duration of the movement in milliseconds.",
        },
    },
)


# -- scroll --


def _scroll(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    direction = request.params.get("direction", "down")
    clicks = request.params.get("clicks", 3)
    x = request.params.get("x", None)
    y = request.params.get("y", None)
    input_actions.scroll(direction=direction, clicks=clicks, x=x, y=y)
    pos = f" at ({x}, {y})" if x is not None and y is not None else ""
    response.append_text(f"Scrolled {direction} {clicks} clicks{pos}.")


scroll = define_tool(
    name="scroll",
    description=(
        "Scroll the mouse wheel at the current pointer position or at given screen "
        "coordinates. Use direction and clicks for discrete mouse-wheel steps."
    ),
    handler=_scroll,
    category=ToolCategory.INPUT,
    read_only=False,
    parameters={
        "direction": {
            "type": "string",
            "default": "down",
            "description": "Scroll direction.",
            "enum": ["up", "down", "left", "right"],
        },
        "clicks": {
            "type": "integer",
            "default": 3,
            "description": "Number of discrete scroll steps.",
        },
        "x": {
            "type": "integer",
            "default": None,
            "description": "Optional X coordinate to scroll at.",
        },
        "y": {
            "type": "integer",
            "default": None,
            "description": "Optional Y coordinate to scroll at.",
        },
    },
)


# -- scroll_smooth --


def _scroll_smooth(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    x = request.params.get("x", 0)
    y = request.params.get("y", 0)
    dx = request.params.get("dx", 0.0)
    dy = request.params.get("dy", 0.0)
    input_actions.scroll_smooth(x=x, y=y, dx=dx, dy=dy)
    response.append_text(f"Smooth scroll at ({x}, {y}) with offset ({dx}, {dy}).")


scroll_smooth = define_tool(
    name="scroll_smooth",
    description=(
        "Perform smooth (non-discrete) scrolling at a given position. "
        "Use dx/dy for horizontal/vertical scroll amounts as floating-point values."
    ),
    handler=_scroll_smooth,
    category=ToolCategory.INPUT,
    read_only=False,
    parameters={
        "x": {"type": "integer", "description": "X coordinate to scroll at."},
        "y": {"type": "integer", "description": "Y coordinate to scroll at."},
        "dx": {
            "type": "number",
            "default": 0.0,
            "description": "Horizontal scroll amount.",
        },
        "dy": {
            "type": "number",
            "default": 0.0,
            "description": "Vertical scroll amount.",
        },
    },
)


# -- drag --


def _drag(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    start_x = request.params.get("start_x", 0)
    start_y = request.params.get("start_y", 0)
    end_x = request.params.get("end_x", 0)
    end_y = request.params.get("end_y", 0)
    button = request.params.get("button", "left")
    steps = request.params.get("steps", 10)
    duration_ms = request.params.get("duration_ms", 300)
    input_actions.drag(
        start_x=start_x,
        start_y=start_y,
        end_x=end_x,
        end_y=end_y,
        button=button,
        steps=steps,
        duration_ms=duration_ms,
    )
    context.record_action(
        "drag",
        {"start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y},
    )
    response.append_text(f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y}).")


drag = define_tool(
    name="drag",
    description="Drag from one screen position to another with smooth interpolation.",
    handler=_drag,
    category=ToolCategory.INPUT,
    read_only=False,
    parameters={
        "start_x": {"type": "integer", "description": "Starting X coordinate."},
        "start_y": {"type": "integer", "description": "Starting Y coordinate."},
        "end_x": {"type": "integer", "description": "Ending X coordinate."},
        "end_y": {"type": "integer", "description": "Ending Y coordinate."},
        "button": {
            "type": "string",
            "default": "left",
            "description": "Mouse button.",
            "enum": ["left", "middle", "right"],
        },
        "steps": {
            "type": "integer",
            "default": 10,
            "description": "Number of interpolation steps.",
        },
        "duration_ms": {
            "type": "integer",
            "default": 300,
            "description": "Duration of the drag in milliseconds.",
        },
    },
)


# -- touch_rotate --


def _touch_rotate(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    center_x = request.params.get("center_x", 0)
    center_y = request.params.get("center_y", 0)
    start_angle = request.params.get("start_angle", 0.0)
    end_angle = request.params.get("end_angle", 0.0)
    radius = request.params.get("radius", 100.0)
    duration_ms = request.params.get("duration_ms", 400)
    input_actions.touch_rotate(
        center_x=center_x,
        center_y=center_y,
        start_angle=start_angle,
        end_angle=end_angle,
        radius=radius,
        duration_ms=duration_ms,
    )
    response.append_text(
        f"Touch rotation at ({center_x}, {center_y}) from {start_angle} to {end_angle} radians."
    )


touch_rotate = define_tool(
    name="touch_rotate",
    description=(
        "Perform a two-finger rotation gesture around a center point. "
        "Angles are in radians. Two touch slots trace circular arcs on opposite sides."
    ),
    handler=_touch_rotate,
    category=ToolCategory.INPUT,
    read_only=False,
    parameters={
        "center_x": {"type": "integer", "description": "Center X coordinate."},
        "center_y": {"type": "integer", "description": "Center Y coordinate."},
        "start_angle": {"type": "number", "description": "Start angle in radians."},
        "end_angle": {"type": "number", "description": "End angle in radians."},
        "radius": {"type": "number", "description": "Radius of the rotation arc."},
        "duration_ms": {
            "type": "integer",
            "default": 400,
            "description": "Duration of the gesture in milliseconds.",
        },
    },
)


# -- type_text --


def _type_text(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    text = request.params.get("text", "")
    input_actions.type_text(text=text)
    context.record_action("type_text", {"text": text})
    response.append_text(f"Typed {len(text)} characters.")


type_text = define_tool(
    name="type_text",
    description="Type text into the currently focused element.",
    handler=_type_text,
    category=ToolCategory.INPUT,
    read_only=False,
    parameters={
        "text": {"type": "string", "description": "Text to type."},
    },
)


# -- press_key --


def _press_key(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    key_name = request.params.get("key_name", "")
    element_id = request.params.get("element_id", None)
    settle_timeout_ms = request.params.get("settle_timeout_ms", 1500)
    stable_for_ms = request.params.get("stable_for_ms", 250)
    poll_interval_ms = request.params.get("poll_interval_ms", 50)
    if element_id is not None:
        context.check_boundary(element_id)
    opts = SettleOptions(
        settle_timeout_ms=settle_timeout_ms,
        stable_for_ms=stable_for_ms,
        poll_interval_ms=poll_interval_ms,
    )
    result = input_actions.press_key(key_name=key_name, element_id=element_id, opts=opts)
    context.record_action("press_key", {"key_name": key_name, "element_id": element_id})
    response.set_data("key_name", result.key_name)
    response.set_data("method", result.method)
    response.set_data("input_injected", result.input_injected)
    response.set_data("effect_verified", result.effect_verified)
    response.append_text(f"Pressed key '{key_name}'.")


press_key = define_tool(
    name="press_key",
    description=(
        "Press and release a key by GDK key name, optionally verifying the effect "
        "against a target element and settled GNOME Shell popup state."
    ),
    handler=_press_key,
    category=ToolCategory.INPUT,
    read_only=False,
    parameters={
        "key_name": {"type": "string", "description": "GDK key name (e.g. Return, Escape)."},
        "element_id": {
            "type": "string",
            "default": None,
            "description": "Optional element to verify effect against.",
        },
        "settle_timeout_ms": {
            "type": "integer",
            "default": 1500,
            "description": "Max time to wait for shell to settle.",
        },
        "stable_for_ms": {
            "type": "integer",
            "default": 250,
            "description": "How long shell must be stable.",
        },
        "poll_interval_ms": {
            "type": "integer",
            "default": 50,
            "description": "Polling interval for settle check.",
        },
    },
)


# -- key_combo --


def _key_combo(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    combo = request.params.get("combo", "")
    element_id = request.params.get("element_id", None)
    settle_timeout_ms = request.params.get("settle_timeout_ms", 1500)
    stable_for_ms = request.params.get("stable_for_ms", 250)
    poll_interval_ms = request.params.get("poll_interval_ms", 50)
    if element_id is not None:
        context.check_boundary(element_id)
    opts = SettleOptions(
        settle_timeout_ms=settle_timeout_ms,
        stable_for_ms=stable_for_ms,
        poll_interval_ms=poll_interval_ms,
    )
    result = input_actions.key_combo(combo=combo, element_id=element_id, opts=opts)
    context.record_action("key_combo", {"combo": combo, "element_id": element_id})
    response.set_data("combo", result.combo)
    response.set_data("method", result.method)
    response.set_data("input_injected", result.input_injected)
    response.set_data("effect_verified", result.effect_verified)
    response.append_text(f"Pressed key combo '{combo}'.")


key_combo = define_tool(
    name="key_combo",
    description=(
        "Send a key combination such as ctrl+c, alt+F4, ctrl+shift+t, or super. "
        "Modifiers are pressed in order before the principal key and released in "
        "reverse order after. Optionally verify the effect against a target element."
    ),
    handler=_key_combo,
    category=ToolCategory.INPUT,
    read_only=False,
    parameters={
        "combo": {
            "type": "string",
            "description": "Key combination string (e.g. ctrl+c, alt+F4).",
        },
        "element_id": {
            "type": "string",
            "default": None,
            "description": "Optional element to verify effect against.",
        },
        "settle_timeout_ms": {
            "type": "integer",
            "default": 1500,
            "description": "Max time to wait for shell to settle.",
        },
        "stable_for_ms": {
            "type": "integer",
            "default": 250,
            "description": "How long shell must be stable.",
        },
        "poll_interval_ms": {
            "type": "integer",
            "default": 50,
            "description": "Polling interval for settle check.",
        },
    },
)


# -- clipboard_read --


def _clipboard_read(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    selection = request.params.get("selection", "clipboard")
    mime_type = request.params.get("mime_type", "text/plain")
    result = input_actions.clipboard_read(selection=selection, mime_type=mime_type)
    response.set_data("content", result.content)
    response.set_data("selection", result.selection)
    response.set_data("mime_type", result.mime_type)
    response.set_data("encoding", result.encoding)
    response.append_text(f"Read {selection} clipboard ({mime_type}).")


clipboard_read = define_tool(
    name="clipboard_read",
    description=(
        "Read the Wayland clipboard contents. Supports custom MIME types "
        "for reading binary data (returned as base64)."
    ),
    handler=_clipboard_read,
    category=ToolCategory.INPUT,
    parameters={
        "selection": {
            "type": "string",
            "default": "clipboard",
            "description": "Selection type: clipboard or primary.",
        },
        "mime_type": {
            "type": "string",
            "default": "text/plain",
            "description": "MIME type to request.",
        },
    },
)


# -- clipboard_write --


def _clipboard_write(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    text = request.params.get("text", "")
    selection = request.params.get("selection", "clipboard")
    mime_type = request.params.get("mime_type", "text/plain")
    input_actions.clipboard_write(text=text, selection=selection, mime_type=mime_type)
    response.append_text(f"Wrote to {selection} clipboard ({mime_type}).")


clipboard_write = define_tool(
    name="clipboard_write",
    description=(
        "Write to the Wayland clipboard. Supports custom MIME types. "
        "For binary types, pass base64-encoded data as text."
    ),
    handler=_clipboard_write,
    category=ToolCategory.INPUT,
    read_only=False,
    parameters={
        "text": {"type": "string", "description": "Text to write to clipboard."},
        "selection": {
            "type": "string",
            "default": "clipboard",
            "description": "Selection type: clipboard or primary.",
        },
        "mime_type": {
            "type": "string",
            "default": "text/plain",
            "description": "MIME type for the data.",
        },
    },
)
