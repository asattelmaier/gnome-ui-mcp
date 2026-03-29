"""Keyboard layout info and key name catalogue (Item 17)."""

from __future__ import annotations

from typing import Any

from ..runtime.gi_env import Gio

JsonDict = dict[str, Any]

_KEY_CATEGORIES: dict[str, list[str]] = {
    "navigation": [
        "Up",
        "Down",
        "Left",
        "Right",
        "Home",
        "End",
        "Page_Up",
        "Page_Down",
        "Tab",
    ],
    "function": [f"F{i}" for i in range(1, 13)],
    "modifier": [
        "Control_L",
        "Control_R",
        "Shift_L",
        "Shift_R",
        "Alt_L",
        "Alt_R",
        "Super_L",
        "Super_R",
        "Meta_L",
        "Meta_R",
    ],
    "editing": [
        "Return",
        "BackSpace",
        "Delete",
        "Insert",
        "Escape",
        "space",
    ],
}


def list_key_names(category: str) -> JsonDict:
    """Return a list of symbolic key names for *category*.

    Valid categories: ``navigation``, ``function``, ``modifier``, ``editing``.
    """
    keys = _KEY_CATEGORIES.get(category)
    if keys is None:
        return {
            "success": False,
            "error": f"Unknown category {category!r}. Valid: {sorted(_KEY_CATEGORIES.keys())}",
        }
    return {"success": True, "category": category, "keys": list(keys)}


def get_keyboard_layout() -> JsonDict:
    """Read the active keyboard layout from GSettings."""
    try:
        settings = Gio.Settings.new("org.gnome.desktop.input-sources")
        sources = settings.get_value("sources").unpack()
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    if not sources:
        return {"success": False, "error": "No input sources configured"}

    _type, value = sources[0]
    if "+" in value:
        layout, variant = value.split("+", 1)
    else:
        layout, variant = value, ""

    return {
        "success": True,
        "layout": layout,
        "variant": variant or None,
        "type": _type,
        "all_sources": sources,
    }
