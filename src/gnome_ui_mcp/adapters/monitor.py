"""Monitor/display information."""

from __future__ import annotations

from dataclasses import dataclass

from ..runtime.gi_env import Gdk


@dataclass
class MonitorGeometry:
    x: int
    y: int
    width: int
    height: int


@dataclass
class MonitorInfo:
    index: int
    model: str
    geometry: MonitorGeometry


def get_monitor_for_point(x: int, y: int) -> MonitorInfo:
    """Return the monitor containing (x, y). Raises if not found."""
    display = Gdk.Display.get_default()
    if display is None:
        msg = "GDK display is not available"
        raise RuntimeError(msg)

    n_monitors = display.get_n_monitors()
    for index in range(n_monitors):
        monitor = display.get_monitor(index)
        geom = monitor.get_geometry()
        if geom.x <= x < geom.x + geom.width and geom.y <= y < geom.y + geom.height:
            return MonitorInfo(
                index=index,
                model=monitor.get_model(),
                geometry=MonitorGeometry(
                    x=geom.x,
                    y=geom.y,
                    width=geom.width,
                    height=geom.height,
                ),
            )

    msg = f"Point ({x}, {y}) is not contained in any monitor"
    raise ValueError(msg)
