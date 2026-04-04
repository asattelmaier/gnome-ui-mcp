"""Keyboard layout info and key name catalogue."""

from __future__ import annotations

from dataclasses import dataclass

from ..runtime.gi_env import Gio

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
    "editing": ["Return", "BackSpace", "Delete", "Insert", "Escape", "space"],
}

VALID_CATEGORIES = sorted([*_KEY_CATEGORIES, "all"])


@dataclass
class KeyboardLayout:
    layout: str
    variant: str | None
    source_type: str
    all_sources: list[tuple[str, str]]


def list_key_names(category: str = "all") -> tuple[str, list[str]]:
    """Return (category, keys) for the given category. Raises on invalid."""
    if category == "all":
        keys: list[str] = []
        for cat_keys in _KEY_CATEGORIES.values():
            keys.extend(cat_keys)
        return "all", keys

    cat_keys = _KEY_CATEGORIES.get(category)
    if cat_keys is None:
        msg = f"Unknown category {category!r}. Valid: {VALID_CATEGORIES}"
        raise ValueError(msg)
    return category, list(cat_keys)


def get_keyboard_layout() -> KeyboardLayout:
    """Read the active keyboard layout from GSettings. Raises on failure."""
    settings = Gio.Settings.new("org.gnome.desktop.input-sources")
    sources = settings.get_value("sources").unpack()

    if not sources:
        msg = "No input sources configured"
        raise ValueError(msg)

    source_type, value = sources[0]
    if "+" in value:
        layout, variant = value.split("+", 1)
    else:
        layout, variant = value, None

    return KeyboardLayout(
        layout=layout,
        variant=variant,
        source_type=source_type,
        all_sources=sources,
    )
