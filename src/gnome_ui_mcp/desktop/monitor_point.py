"""Determine which monitor contains a screen coordinate (Item 18)."""

from __future__ import annotations

from typing import Any

from ..runtime.gi_env import Gdk

JsonDict = dict[str, Any]


def get_monitor_for_point(x: int, y: int) -> JsonDict:
    """Return the monitor geometry for the monitor containing (*x*, *y*).

    Uses GDK to enumerate monitors and performs a simple bounds check.
    """
    display = Gdk.Display.get_default()
    if display is None:
        return {"success": False, "error": "GDK display is not available"}

    n_monitors = display.get_n_monitors()
    for index in range(n_monitors):
        monitor = display.get_monitor(index)
        geom = monitor.get_geometry()
        if geom.x <= x < geom.x + geom.width and geom.y <= y < geom.y + geom.height:
            return {
                "success": True,
                "monitor_index": index,
                "model": monitor.get_model(),
                "geometry": {
                    "x": geom.x,
                    "y": geom.y,
                    "width": geom.width,
                    "height": geom.height,
                },
            }

    return {
        "success": False,
        "error": f"Point ({x}, {y}) is not contained in any monitor",
        "x": x,
        "y": y,
    }
