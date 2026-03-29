"""Window management operations: close, move, resize, snap, toggle state."""

from __future__ import annotations

from typing import Any

from . import input

JsonDict = dict[str, Any]

_SNAP_COMBOS: dict[str, str] = {
    "maximize": "super+Up",
    "restore": "super+Down",
    "left": "super+Left",
    "right": "super+Right",
}


def close_window() -> JsonDict:
    """Close the currently focused window via Alt+F4."""
    result = input.key_combo("alt+F4")
    return {
        "success": result.get("success", False),
        "action": "close_window",
    }


def _send_arrow_keys(dx: int, dy: int) -> None:
    """Send arrow key presses proportional to dx/dy (1 press per 10 pixels)."""
    h_count = abs(dx) // 10
    v_count = abs(dy) // 10
    h_key = "Right" if dx >= 0 else "Left"
    v_key = "Down" if dy >= 0 else "Up"

    for _ in range(h_count):
        input.press_key(h_key)
    for _ in range(v_count):
        input.press_key(v_key)


def move_window(dx: int, dy: int) -> JsonDict:
    """Move the focused window by (dx, dy) pixels using keyboard move mode.

    Sends Alt+F7 to enter move mode, arrow keys for displacement, then Return.
    """
    combo_result = input.key_combo("alt+F7")
    if not combo_result.get("success"):
        return {"success": False, "action": "move_window", "error": "Failed to enter move mode"}

    _send_arrow_keys(dx, dy)
    input.press_key("Return")

    return {
        "success": True,
        "action": "move_window",
        "dx": dx,
        "dy": dy,
    }


def resize_window(dw: int, dh: int) -> JsonDict:
    """Resize the focused window by (dw, dh) pixels using keyboard resize mode.

    Sends Alt+F8 to enter resize mode, arrow keys for change, then Return.
    """
    combo_result = input.key_combo("alt+F8")
    if not combo_result.get("success"):
        return {"success": False, "action": "resize_window", "error": "Failed to enter resize mode"}

    _send_arrow_keys(dw, dh)
    input.press_key("Return")

    return {
        "success": True,
        "action": "resize_window",
        "dw": dw,
        "dh": dh,
    }


def snap_window(position: str) -> JsonDict:
    """Snap the focused window to a screen position.

    Valid positions: maximize, restore, left, right.
    """
    combo = _SNAP_COMBOS.get(position)
    if combo is None:
        valid = ", ".join(sorted(_SNAP_COMBOS))
        return {
            "success": False,
            "action": "snap_window",
            "error": f"Invalid position {position!r}. Valid: {valid}",
        }

    result = input.key_combo(combo)
    return {
        "success": result.get("success", False),
        "action": "snap_window",
        "position": position,
    }


def toggle_window_state(state: str) -> JsonDict:
    """Toggle a window state (fullscreen, maximize, minimize)."""
    if state == "fullscreen":
        result = input.press_key("F11")
    elif state == "maximize":
        result = input.key_combo("alt+F10")
    elif state == "minimize":
        result = input.key_combo("super+h")
    else:
        return {
            "success": False,
            "action": "toggle_window_state",
            "error": f"Invalid state {state!r}. Valid: fullscreen, maximize, minimize",
        }

    return {
        "success": result.get("success", False),
        "action": "toggle_window_state",
        "state": state,
    }
