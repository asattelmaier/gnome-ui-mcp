"""Workspace management via D-Bus and keyboard shortcuts."""

from __future__ import annotations

from dataclasses import dataclass

from ..desktop import input as _desktop_input
from ..desktop.types import unpack_variant
from ..runtime.gi_env import Gio, GLib

_VALID_DIRECTIONS = {"up", "down"}

_SWITCH_KEYS: dict[str, str] = {
    "up": "ctrl+alt+Up",
    "down": "ctrl+alt+Down",
}

_MOVE_KEYS: dict[str, str] = {
    "up": "ctrl+shift+alt+Up",
    "down": "ctrl+shift+alt+Down",
}


@dataclass
class WorkspaceWindow:
    title: str
    app_id: str
    wm_class: str


@dataclass
class Workspace:
    index: int
    windows: list[WorkspaceWindow]


def switch_workspace(direction: str) -> None:
    """Switch workspace. Raises on invalid direction."""
    if direction not in _VALID_DIRECTIONS:
        msg = f"direction must be 'up' or 'down', got {direction!r}"
        raise ValueError(msg)
    _desktop_input.key_combo(_SWITCH_KEYS[direction])


def move_window_to_workspace(direction: str) -> None:
    """Move focused window to adjacent workspace. Raises on invalid direction."""
    if direction not in _VALID_DIRECTIONS:
        msg = f"direction must be 'up' or 'down', got {direction!r}"
        raise ValueError(msg)
    _desktop_input.key_combo(_MOVE_KEYS[direction])


def list_workspaces() -> list[Workspace]:
    """Return all workspaces with their windows.

    Raises RuntimeError if the Shell Introspect interface is not
    accessible (e.g. AccessDenied in sandboxed sessions).
    """
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
        msg = (
            f"Cannot query workspaces: {exc}. "
            "The Shell Introspect interface may not be available "
            "in this session."
        )
        raise RuntimeError(msg) from exc
    unpacked = unpack_variant(result)
    raw_windows = unpacked[0] if unpacked else {}

    workspace_map: dict[int, list[WorkspaceWindow]] = {}
    for _window_id, props in raw_windows.items():
        ws_index = int(props.get("workspace-index", -1))
        win = WorkspaceWindow(
            title=props.get("title", ""),
            app_id=props.get("app-id", ""),
            wm_class=props.get("wm-class", ""),
        )
        workspace_map.setdefault(ws_index, []).append(win)

    return [Workspace(index=idx, windows=windows) for idx, windows in sorted(workspace_map.items())]


def toggle_overview(active: bool | None = None) -> bool:
    """Toggle GNOME Shell overview. Returns the new state."""
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    if active is None:
        active = True
    bus.call_sync(
        "org.gnome.Shell",
        "/org/gnome/Shell",
        "org.freedesktop.DBus.Properties",
        "Set",
        GLib.Variant(
            "(ssv)",
            ("org.gnome.Shell", "OverviewActive", GLib.Variant("b", active)),
        ),
        None,
        Gio.DBusCallFlags.NONE,
        5000,
        None,
    )
    return active
