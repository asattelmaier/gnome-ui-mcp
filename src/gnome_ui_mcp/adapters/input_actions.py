"""Input actions: mouse, keyboard, clipboard, drag, scroll.

Wraps desktop input and interaction modules. Returns typed data and raises
exceptions on failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..desktop import input as _desktop_input
from ..desktop import interaction as _desktop_interaction
from ..desktop.types import SettleOptions


def _require(result: dict) -> dict:
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Operation failed")))
    return result


# -- dataclasses --


@dataclass
class ClickAtResult:
    x: int
    y: int
    button: str
    method: str
    input_injected: bool
    effect_verified: bool | None


@dataclass
class PressKeyResult:
    key_name: str
    element_id: str | None
    method: str
    input_injected: bool
    effect_verified: bool | None


@dataclass
class KeyComboResult:
    combo: str
    element_id: str | None
    method: str
    input_injected: bool
    effect_verified: bool | None


@dataclass
class ClipboardContent:
    content: str
    selection: str
    mime_type: str
    encoding: str


# -- public API --


def click_at(
    x: int,
    y: int,
    button: str = "left",
    click_count: int = 1,
) -> ClickAtResult:
    """Click at screen coordinates. Raises on failure."""
    result = _require(
        _desktop_interaction.click_at(
            x=x,
            y=y,
            button=button,
            click_count=click_count,
        )
    )
    return ClickAtResult(
        x=x,
        y=y,
        button=button,
        method=result.get("method", ""),
        input_injected=result.get("input_injected", False),
        effect_verified=result.get("effect_verified"),
    )


def mouse_move(x: int, y: int) -> None:
    """Move mouse to absolute coordinates. Raises on failure."""
    _require(_desktop_input.perform_mouse_move(x=x, y=y))


def mouse_move_relative(dx: float, dy: float) -> None:
    """Move mouse by a relative offset. Raises on failure."""
    _require(_desktop_input.mouse_move_relative(dx=dx, dy=dy))


def mouse_move_smooth(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration_ms: int = 300,
) -> None:
    """Smoothly move mouse. Raises on failure."""
    _require(
        _desktop_input.mouse_move_smooth(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            duration_ms=duration_ms,
        )
    )


def scroll(
    direction: str = "down",
    clicks: int = 3,
    x: int | None = None,
    y: int | None = None,
) -> None:
    """Scroll the mouse wheel. Raises on failure."""
    _require(_desktop_input.perform_scroll(direction=direction, clicks=clicks, x=x, y=y))


def scroll_smooth(x: int, y: int, dx: float, dy: float) -> None:
    """Perform smooth scrolling. Raises on failure."""
    _require(_desktop_input.scroll_smooth(x=x, y=y, dx=dx, dy=dy))


def drag(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    button: str = "left",
    steps: int = 10,
    duration_ms: int = 300,
) -> None:
    """Drag from one position to another. Raises on failure."""
    _require(
        _desktop_input.perform_drag(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            button=button,
            steps=steps,
            duration_ms=duration_ms,
        )
    )


def touch_rotate(
    center_x: int,
    center_y: int,
    start_angle: float,
    end_angle: float,
    radius: float = 100.0,
    duration_ms: int = 400,
) -> None:
    """Perform a two-finger rotation gesture. Raises on failure."""
    _require(
        _desktop_input.touch_rotate(
            center_x=center_x,
            center_y=center_y,
            start_angle=start_angle,
            end_angle=end_angle,
            radius=radius,
            duration_ms=duration_ms,
        )
    )


def type_text(text: str) -> None:
    """Type text into the focused element. Raises on failure."""
    _require(_desktop_input.type_text(text=text))


def press_key(
    key_name: str,
    element_id: str | None = None,
    opts: SettleOptions | None = None,
) -> PressKeyResult:
    """Press a key with optional effect verification. Raises on failure."""
    if opts is None:
        opts = SettleOptions()
    result = _require(
        _desktop_interaction.press_key(key_name=key_name, element_id=element_id, opts=opts)
    )
    return PressKeyResult(
        key_name=key_name,
        element_id=element_id,
        method=result.get("method", ""),
        input_injected=result.get("input_injected", False),
        effect_verified=result.get("effect_verified"),
    )


def key_combo(
    combo: str,
    element_id: str | None = None,
    opts: SettleOptions | None = None,
) -> KeyComboResult:
    """Send a key combination with optional verification. Raises on failure."""
    if opts is None:
        opts = SettleOptions()
    result = _require(_desktop_interaction.key_combo(combo=combo, element_id=element_id, opts=opts))
    return KeyComboResult(
        combo=combo,
        element_id=element_id,
        method=result.get("method", ""),
        input_injected=result.get("input_injected", False),
        effect_verified=result.get("effect_verified"),
    )


def clipboard_read(
    selection: str = "clipboard",
    mime_type: str = "text/plain",
) -> ClipboardContent:
    """Read clipboard contents. Raises on failure."""
    result = _require(_desktop_input.clipboard_read(selection=selection, mime_type=mime_type))
    return ClipboardContent(
        content=result.get("content", result.get("text", "")),
        selection=selection,
        mime_type=mime_type,
        encoding=result.get("encoding", "utf-8"),
    )


def clipboard_write(
    text: str,
    selection: str = "clipboard",
    mime_type: str = "text/plain",
) -> None:
    """Write to clipboard. Raises on failure."""
    _require(_desktop_input.clipboard_write(text=text, selection=selection, mime_type=mime_type))
