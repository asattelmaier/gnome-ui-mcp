"""Window management: close, move, resize, snap, toggle state."""

from __future__ import annotations

from ..desktop import input as _desktop_input

_SNAP_COMBOS: dict[str, str] = {
    "maximize": "super+Up",
    "restore": "super+Down",
    "left": "super+Left",
    "right": "super+Right",
}

VALID_SNAP_POSITIONS = sorted(_SNAP_COMBOS)
VALID_TOGGLE_STATES = ["fullscreen", "maximize", "minimize"]


def close_window() -> None:
    """Close the currently focused window via Alt+F4."""
    _desktop_input.key_combo("alt+F4")


def _send_arrow_keys(dx: int, dy: int) -> None:
    h_count = abs(dx) // 10
    v_count = abs(dy) // 10
    h_key = "Right" if dx >= 0 else "Left"
    v_key = "Down" if dy >= 0 else "Up"
    for _ in range(h_count):
        _desktop_input.press_key(h_key)
    for _ in range(v_count):
        _desktop_input.press_key(v_key)


def move_window(dx: int, dy: int) -> None:
    """Move the focused window by (dx, dy) pixels. Raises on failure."""
    result = _desktop_input.key_combo("alt+F7")
    if not result.get("success"):
        msg = "Failed to enter move mode"
        raise RuntimeError(msg)
    _send_arrow_keys(dx, dy)
    _desktop_input.press_key("Return")


def resize_window(dw: int, dh: int) -> None:
    """Resize the focused window by (dw, dh) pixels. Raises on failure."""
    result = _desktop_input.key_combo("alt+F8")
    if not result.get("success"):
        msg = "Failed to enter resize mode"
        raise RuntimeError(msg)
    _send_arrow_keys(dw, dh)
    _desktop_input.press_key("Return")


def snap_window(position: str) -> None:
    """Snap the focused window. Raises on invalid position."""
    combo = _SNAP_COMBOS.get(position)
    if combo is None:
        valid = ", ".join(VALID_SNAP_POSITIONS)
        msg = f"Invalid position {position!r}. Valid: {valid}"
        raise ValueError(msg)
    _desktop_input.key_combo(combo)


def toggle_window_state(state: str) -> None:
    """Toggle a window state. Raises on invalid state."""
    if state == "fullscreen":
        _desktop_input.press_key("F11")
    elif state == "maximize":
        _desktop_input.key_combo("alt+F10")
    elif state == "minimize":
        _desktop_input.key_combo("super+h")
    else:
        valid = ", ".join(VALID_TOGGLE_STATES)
        msg = f"Invalid state {state!r}. Valid: {valid}"
        raise ValueError(msg)
