"""Desktop state snapshots and comparison (Item 13)."""

from __future__ import annotations

import uuid
from typing import Any

from . import accessibility

JsonDict = dict[str, Any]

# Module-level snapshot store: id -> snapshot dict
_snapshots: dict[str, JsonDict] = {}


def snapshot_state() -> JsonDict:
    """Capture the current desktop state and store it by UUID.

    Returns the snapshot plus a ``snapshot_id`` key for later comparison.
    """
    apps = accessibility.list_applications()
    windows = accessibility.list_windows()
    focus = accessibility.current_focus_metadata()
    popups = accessibility._visible_shell_popup_state()

    snap_id = str(uuid.uuid4())
    snap: JsonDict = {
        "applications": apps,
        "windows": windows,
        "focus": focus,
        "popups": popups,
    }
    _snapshots[snap_id] = snap

    return {"success": True, "snapshot_id": snap_id, **snap}


def compare_state(before_id: str, after_id: str) -> JsonDict:
    """Diff two snapshots taken with :func:`snapshot_state`."""
    before = _snapshots.get(before_id)
    after = _snapshots.get(after_id)

    if before is None or after is None:
        missing = []
        if before is None:
            missing.append(before_id)
        if after is None:
            missing.append(after_id)
        return {"success": False, "error": f"Unknown snapshot(s): {missing!r}"}

    before_apps = {a["name"] for a in before["applications"].get("applications", [])}
    after_apps = {a["name"] for a in after["applications"].get("applications", [])}
    apps_added = [
        a for a in after["applications"].get("applications", []) if a["name"] not in before_apps
    ]
    apps_removed = [
        a for a in before["applications"].get("applications", []) if a["name"] not in after_apps
    ]

    before_wins = {w.get("id") for w in before["windows"].get("windows", [])}
    after_wins = {w.get("id") for w in after["windows"].get("windows", [])}
    windows_added = [
        w for w in after["windows"].get("windows", []) if w.get("id") not in before_wins
    ]
    windows_removed = [
        w for w in before["windows"].get("windows", []) if w.get("id") not in after_wins
    ]

    focus_changed = before.get("focus") != after.get("focus")
    popups_changed = before.get("popups") != after.get("popups")

    return {
        "success": True,
        "apps_added": apps_added,
        "apps_removed": apps_removed,
        "windows_added": windows_added,
        "windows_removed": windows_removed,
        "focus_changed": focus_changed,
        "popups_changed": popups_changed,
        "before_id": before_id,
        "after_id": after_id,
    }
