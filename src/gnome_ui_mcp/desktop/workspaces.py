from __future__ import annotations

from typing import Any

from ..runtime.gi_env import Gio, GLib
from . import input

JsonDict = dict[str, Any]

_VALID_DIRECTIONS = {"up", "down"}

_SWITCH_KEYS: dict[str, list[str]] = {
    "up": ["Control_L", "Alt_L", "Up"],
    "down": ["Control_L", "Alt_L", "Down"],
}

_MOVE_KEYS: dict[str, list[str]] = {
    "up": ["Control_L", "Shift_L", "Alt_L", "Up"],
    "down": ["Control_L", "Shift_L", "Alt_L", "Down"],
}


def _send_key_combo(keys: list[str]) -> JsonDict:
    results = []
    try:
        for key in keys:
            results.append(input.press_key(key))
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    return {"success": True, "keys": keys, "results": results}


def _unpack_variant(val: Any) -> Any:
    if isinstance(val, GLib.Variant):
        return _unpack_variant(val.unpack())
    if isinstance(val, dict):
        return {k: _unpack_variant(v) for k, v in val.items()}
    if isinstance(val, list | tuple):
        return [_unpack_variant(item) for item in val]
    return val


def switch_workspace(direction: str) -> JsonDict:
    if direction not in _VALID_DIRECTIONS:
        return {"success": False, "error": f"direction must be 'up' or 'down', got {direction!r}"}

    combo_result = _send_key_combo(_SWITCH_KEYS[direction])
    return {
        "success": combo_result["success"],
        "action": "switch_workspace",
        "direction": direction,
        **combo_result,
    }


def move_window_to_workspace(direction: str) -> JsonDict:
    if direction not in _VALID_DIRECTIONS:
        return {"success": False, "error": f"direction must be 'up' or 'down', got {direction!r}"}

    combo_result = _send_key_combo(_MOVE_KEYS[direction])
    return {
        "success": combo_result["success"],
        "action": "move_window_to_workspace",
        "direction": direction,
        **combo_result,
    }


def list_workspaces() -> JsonDict:
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        result = bus.call_sync(
            "org.gnome.Shell",
            "/org/gnome/Shell/Introspect",
            "org.gnome.Shell.Introspect",
            "GetWindows",
            None,
            None,
            Gio.DBusCallFlags.NONE,
            5000,
            None,
        )
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    unpacked = _unpack_variant(result)
    raw_windows = unpacked[0] if unpacked else {}

    workspace_map: dict[int, list[JsonDict]] = {}
    for _window_id, props in raw_windows.items():
        ws_index = props.get("workspace-index", -1)
        window_info = {
            "title": props.get("title", ""),
            "app_id": props.get("app-id", ""),
            "wm_class": props.get("wm-class", ""),
        }
        workspace_map.setdefault(int(ws_index), []).append(window_info)

    workspaces = [
        {"index": idx, "windows": windows, "window_count": len(windows)}
        for idx, windows in sorted(workspace_map.items())
    ]

    return {"success": True, "workspaces": workspaces, "workspace_count": len(workspaces)}


def toggle_overview(active: bool | None = None) -> JsonDict:
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        if active is None:
            active = True

        bus.call_sync(
            "org.gnome.Shell",
            "/org/gnome/Shell",
            "org.freedesktop.DBus.Properties",
            "Set",
            GLib.Variant("(ssv)", ("org.gnome.Shell", "OverviewActive", GLib.Variant("b", active))),
            None,
            Gio.DBusCallFlags.NONE,
            5000,
            None,
        )
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    return {"success": True, "overview_active": active}
