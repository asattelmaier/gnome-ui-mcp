from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

from ..runtime.gi_env import Gio, GLib

JsonDict = dict[str, Any]

CACHE_DIR = Path.home() / ".cache" / "gnome-ui-mcp" / "recordings"
GNOME_SHELL_SCREENCAST_BUS = "org.gnome.Shell.Screencast"
GNOME_SHELL_SCREENCAST_PATH = "/org/gnome/Shell/Screencast"
GNOME_SHELL_SCREENCAST_IFACE = "org.gnome.Shell.Screencast"

_bus: Gio.DBusConnection | None = None
_recording_path: str | None = None


def _get_bus() -> Gio.DBusConnection:
    global _bus
    if _bus is None:
        _bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    return _bus


def screen_record_start(
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
    framerate: int = 30,
    draw_cursor: bool = True,
) -> JsonDict:
    global _recording_path

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    file_template = str(CACHE_DIR / f"recording-{int(time.time() * 1000)}")

    try:
        bus = _get_bus()
        is_area = all(v is not None for v in (x, y, width, height))

        options = GLib.Variant(
            "a{sv}",
            {
                "framerate": GLib.Variant("i", framerate),
                "draw-cursor": GLib.Variant("b", draw_cursor),
            },
        )

        if is_area:
            params = GLib.Variant.new_tuple(
                GLib.Variant("i", x),
                GLib.Variant("i", y),
                GLib.Variant("i", width),
                GLib.Variant("i", height),
                GLib.Variant("s", file_template),
                options,
            )
            result = bus.call_sync(
                GNOME_SHELL_SCREENCAST_BUS,
                GNOME_SHELL_SCREENCAST_PATH,
                GNOME_SHELL_SCREENCAST_IFACE,
                "ScreencastArea",
                params,
                None,
                Gio.DBusCallFlags.NONE,
                5000,
                None,
            )
        else:
            params = GLib.Variant.new_tuple(
                GLib.Variant("s", file_template),
                options,
            )
            result = bus.call_sync(
                GNOME_SHELL_SCREENCAST_BUS,
                GNOME_SHELL_SCREENCAST_PATH,
                GNOME_SHELL_SCREENCAST_IFACE,
                "Screencast",
                params,
                None,
                Gio.DBusCallFlags.NONE,
                5000,
                None,
            )

        success, filename_used = result.unpack()
        if not success:
            return {"success": False, "error": "Shell Screencast returned failure"}

        _recording_path = filename_used
        return {
            "success": True,
            "recording": True,
            "path": filename_used,
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def screen_record_stop(
    to_gif: bool = False,
    gif_fps: int = 10,
    gif_width: int = 640,
) -> JsonDict:
    global _recording_path

    if _recording_path is None:
        return {"success": False, "error": "No recording in progress"}

    path = _recording_path

    try:
        bus = _get_bus()
        result = bus.call_sync(
            GNOME_SHELL_SCREENCAST_BUS,
            GNOME_SHELL_SCREENCAST_PATH,
            GNOME_SHELL_SCREENCAST_IFACE,
            "StopScreencast",
            None,
            None,
            Gio.DBusCallFlags.NONE,
            5000,
            None,
        )
        success = result.unpack()[0]
        _recording_path = None

        if not success:
            return {"success": False, "error": "StopScreencast returned failure", "path": path}
    except Exception as exc:
        _recording_path = None
        return {"success": False, "error": str(exc), "path": path}

    response: JsonDict = {"success": True, "path": path}

    if to_gif:
        gif_path = Path(path).with_suffix(".gif")
        vf = (
            f"fps={gif_fps},scale={gif_width}:-1:flags=lanczos,"
            f"split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
        )
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", path, "-vf", vf, "-loop", "0", str(gif_path)],
                capture_output=True,
                timeout=60,
            )
            response["gif_path"] = str(gif_path)
        except Exception as exc:
            response["gif_error"] = str(exc)

    return response
