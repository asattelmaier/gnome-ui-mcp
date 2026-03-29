from __future__ import annotations

import atexit
import os
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from ..runtime.gi_env import Atspi, Gdk, Gio, GLib

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

from .types import JsonDict


def get_display_scale_factor() -> int:
    try:
        display = Gdk.Display.get_default()
        if display is None:
            return 1
        count = display.get_n_monitors()
        if count <= 0:
            return 1
        monitor = display.get_monitor(0)
        return int(monitor.get_scale_factor())
    except Exception:
        return 1


CACHE_DIR = Path.home() / ".cache" / "gnome-ui-mcp" / "screenshots"
GNOME_SHELL_SCREENSHOT_BUS = "org.gnome.Shell.Screenshot"
GNOME_SHELL_SCREENSHOT_PATH = "/org/gnome/Shell/Screenshot"
GNOME_SHELL_SCREENSHOT_IFACE = "org.gnome.Shell.Screenshot"
GNOME_SCREENSHOT_WELL_KNOWN_NAME = "org.gnome.Screenshot"
MUTTER_REMOTE_DESKTOP_BUS = "org.gnome.Mutter.RemoteDesktop"
MUTTER_REMOTE_DESKTOP_PATH = "/org/gnome/Mutter/RemoteDesktop"
MUTTER_REMOTE_DESKTOP_IFACE = "org.gnome.Mutter.RemoteDesktop"
MUTTER_REMOTE_DESKTOP_SESSION_IFACE = "org.gnome.Mutter.RemoteDesktop.Session"
MUTTER_SCREENCAST_BUS = "org.gnome.Mutter.ScreenCast"
MUTTER_SCREENCAST_PATH = "/org/gnome/Mutter/ScreenCast"
MUTTER_SCREENCAST_IFACE = "org.gnome.Mutter.ScreenCast"
MUTTER_SCREENCAST_SESSION_IFACE = "org.gnome.Mutter.ScreenCast.Session"
REMOTE_POINTER_BUTTONS = {"left": 0x110, "right": 0x111, "middle": 0x112}
SCROLL_AXIS_VERTICAL = 0
SCROLL_AXIS_HORIZONTAL = 1
SCROLL_DIRECTION_MAP: dict[str, tuple[int, int]] = {
    "up": (SCROLL_AXIS_VERTICAL, -1),
    "down": (SCROLL_AXIS_VERTICAL, 1),
    "left": (SCROLL_AXIS_HORIZONTAL, -1),
    "right": (SCROLL_AXIS_HORIZONTAL, 1),
}
SCROLL_BUTTON_MAP = {"up": "b4c", "down": "b5c", "left": "b6c", "right": "b7c"}
TEXT_KEY_NAME_MAP = {
    "\n": "Return",
    "\r": "Return",
    "\t": "Tab",
    "\b": "BackSpace",
    "\x1b": "Escape",
}
MODIFIER_KEYVALS: dict[str, int] = {
    "ctrl": Gdk.keyval_from_name("Control_L"),
    "control": Gdk.keyval_from_name("Control_L"),
    "shift": Gdk.keyval_from_name("Shift_L"),
    "alt": Gdk.keyval_from_name("Alt_L"),
    "super": Gdk.keyval_from_name("Super_L"),
    "meta": Gdk.keyval_from_name("Meta_L"),
    "hyper": Gdk.keyval_from_name("Hyper_L"),
}


@dataclass(frozen=True)
class _StageArea:
    origin_x: int
    origin_y: int
    width: int
    height: int

    def local_coordinates(self, x: int, y: int) -> tuple[float, float]:
        if not (
            self.origin_x <= x < self.origin_x + self.width
            and self.origin_y <= y < self.origin_y + self.height
        ):
            msg = f"Coordinates ({x}, {y}) are outside the desktop stage"
            raise ValueError(msg)

        return float(x - self.origin_x), float(y - self.origin_y)


class _MutterRemoteDesktopInput:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._rd_proxy: Gio.DBusProxy | None = None
        self._sc_proxy: Gio.DBusProxy | None = None
        self._rd_session: Gio.DBusProxy | None = None
        self._stream_path: str | None = None
        self._stage_area: _StageArea | None = None
        self._started = False
        atexit.register(self.close)

    def info(self) -> JsonDict:
        try:
            proxy = self._root_proxy()
            version_variant = proxy.get_cached_property("Version")
            devices_variant = proxy.get_cached_property("SupportedDeviceTypes")
        except Exception as exc:
            return {"available": False, "error": str(exc)}

        return {
            "available": True,
            "version": version_variant.unpack() if version_variant is not None else None,
            "supported_device_types": (
                devices_variant.unpack() if devices_variant is not None else None
            ),
        }

    def click_at(self, x: int, y: int, *, button: str = "left", click_count: int = 1) -> JsonDict:
        button_code = REMOTE_POINTER_BUTTONS.get(button.lower())
        if button_code is None:
            msg = "button must be left, middle, or right"
            raise ValueError(msg)

        stream_path, stage_area = self._ensure_session()
        local_x, local_y = stage_area.local_coordinates(x, y)

        self._call_session(
            "NotifyPointerMotionAbsolute",
            GLib.Variant("(sdd)", (stream_path, local_x, local_y)),
        )
        time.sleep(0.02)
        with self._lock:
            for click_index in range(click_count):
                if click_index > 0:
                    time.sleep(0.05)
                self._call_session("NotifyPointerButton", GLib.Variant("(ib)", (button_code, True)))
                self._call_session(
                    "NotifyPointerButton", GLib.Variant("(ib)", (button_code, False))
                )

        return {
            "success": True,
            "x": x,
            "y": y,
            "button": button.lower(),
            "click_count": click_count,
            "backend": "mutter-remote-desktop",
            "stream_path": stream_path,
        }

    def move_to(self, x: int, y: int) -> JsonDict:
        stream_path, stage_area = self._ensure_session()
        local_x, local_y = stage_area.local_coordinates(x, y)

        self._call_session(
            "NotifyPointerMotionAbsolute",
            GLib.Variant("(sdd)", (stream_path, local_x, local_y)),
        )
        time.sleep(0.02)

        return {
            "success": True,
            "x": x,
            "y": y,
            "backend": "mutter-remote-desktop",
            "stream_path": stream_path,
        }

    def move_to_smooth(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        *,
        duration_ms: int = 300,
        steps: int = 20,
    ) -> JsonDict:
        stream_path, stage_area = self._ensure_session()
        start_lx, start_ly = stage_area.local_coordinates(start_x, start_y)
        end_lx, end_ly = stage_area.local_coordinates(end_x, end_y)

        actual_steps = max(1, steps)
        start_time = time.monotonic()

        self._call_session(
            "NotifyPointerMotionAbsolute",
            GLib.Variant("(sdd)", (stream_path, start_lx, start_ly)),
        )

        for i in range(1, actual_steps + 1):
            frac = i / actual_steps
            ix = start_lx + frac * (end_lx - start_lx)
            iy = start_ly + frac * (end_ly - start_ly)
            self._call_session(
                "NotifyPointerMotionAbsolute",
                GLib.Variant("(sdd)", (stream_path, ix, iy)),
            )
            if duration_ms > 0:
                target = start_time + (duration_ms / 1000) * i / actual_steps
                remaining = target - time.monotonic()
                if remaining > 0:
                    time.sleep(remaining)

        return {
            "success": True,
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y,
            "duration_ms": duration_ms,
            "steps": actual_steps,
            "backend": "mutter-remote-desktop",
            "stream_path": stream_path,
        }

    def drag_to(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        *,
        button: str = "left",
        steps: int = 10,
        duration_ms: int = 300,
    ) -> JsonDict:
        button_code = REMOTE_POINTER_BUTTONS.get(button.lower())
        if button_code is None:
            msg = "button must be left, middle, or right"
            raise ValueError(msg)

        stream_path, stage_area = self._ensure_session()
        start_lx, start_ly = stage_area.local_coordinates(start_x, start_y)
        end_lx, end_ly = stage_area.local_coordinates(end_x, end_y)

        def _call(method: str, params: GLib.Variant) -> None:
            self._rd_session.call_sync(method, params, Gio.DBusCallFlags.NONE, -1, None)

        with self._lock:
            if self._rd_session is None:
                msg = "Remote desktop session is not available"
                raise RuntimeError(msg)

            session = self._rd_session
            _call(
                "NotifyPointerMotionAbsolute",
                GLib.Variant("(sdd)", (stream_path, start_lx, start_ly)),
            )
            time.sleep(0.02)
            _call("NotifyPointerButton", GLib.Variant("(ib)", (button_code, True)))
            try:
                actual_steps = max(0, steps)
                start_time = time.monotonic()
                for i in range(1, actual_steps + 1):
                    frac = i / actual_steps if actual_steps else 1.0
                    ix = start_lx + frac * (end_lx - start_lx)
                    iy = start_ly + frac * (end_ly - start_ly)
                    _call(
                        "NotifyPointerMotionAbsolute",
                        GLib.Variant("(sdd)", (stream_path, ix, iy)),
                    )
                    if duration_ms > 0 and actual_steps > 0:
                        target = start_time + (duration_ms / 1000) * i / actual_steps
                        remaining = target - time.monotonic()
                        if remaining > 0:
                            time.sleep(remaining)

                if actual_steps == 0:
                    _call(
                        "NotifyPointerMotionAbsolute",
                        GLib.Variant("(sdd)", (stream_path, end_lx, end_ly)),
                    )
            finally:
                try:
                    session.call_sync(
                        "NotifyPointerButton",
                        GLib.Variant("(ib)", (button_code, False)),
                        Gio.DBusCallFlags.NONE,
                        -1,
                        None,
                    )
                except Exception:
                    pass

        return {
            "success": True,
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y,
            "button": button.lower(),
            "click_count": 1,
            "steps": steps,
            "duration_ms": duration_ms,
            "backend": "mutter-remote-desktop",
            "stream_path": stream_path,
        }

    def press_key(self, key_name: str) -> JsonDict:
        keyval = _key_name_to_keyval(key_name)

        self._ensure_session()
        self._call_session("NotifyKeyboardKeysym", GLib.Variant("(ub)", (keyval, True)))
        self._call_session("NotifyKeyboardKeysym", GLib.Variant("(ub)", (keyval, False)))

        return {
            "success": True,
            "key_name": key_name,
            "keyval": int(keyval),
            "backend": "mutter-remote-desktop",
        }

    def type_text(self, text: str) -> JsonDict:
        self._ensure_session()

        keyvals = [_text_unit_to_keyval(unit) for unit in _text_units(text)]
        for keyval in keyvals:
            self._call_session("NotifyKeyboardKeysym", GLib.Variant("(ub)", (keyval, True)))
            self._call_session("NotifyKeyboardKeysym", GLib.Variant("(ub)", (keyval, False)))

        return {
            "success": True,
            "text_length": len(text),
            "backend": "mutter-remote-desktop",
            "keyvals": keyvals,
        }

    def scroll(
        self,
        direction: str,
        clicks: int = 3,
        x: int | None = None,
        y: int | None = None,
    ) -> JsonDict:
        direction_lower = direction.lower()
        axis_sign = SCROLL_DIRECTION_MAP.get(direction_lower)
        if axis_sign is None:
            msg = "direction must be up, down, left, or right"
            raise ValueError(msg)

        axis, sign = axis_sign
        stream_path, stage_area = self._ensure_session()

        if x is not None and y is not None:
            local_x, local_y = stage_area.local_coordinates(x, y)
            self._call_session(
                "NotifyPointerMotionAbsolute",
                GLib.Variant("(sdd)", (stream_path, local_x, local_y)),
            )
            time.sleep(0.02)

        steps = sign * clicks
        self._call_session(
            "NotifyPointerAxisDiscrete",
            GLib.Variant("(ui)", (axis, steps)),
        )

        return {
            "success": True,
            "direction": direction_lower,
            "clicks": clicks,
            "axis": axis,
            "steps": steps,
            "x": x,
            "y": y,
            "backend": "mutter-remote-desktop",
        }

    def press_key_combo(
        self,
        modifier_keyvals: list[int],
        principal_keyval: int | None,
    ) -> JsonDict:
        self._ensure_session()

        pressed: list[int] = []
        for mkv in modifier_keyvals:
            self._call_session("NotifyKeyboardKeysym", GLib.Variant("(ub)", (mkv, True)))
            pressed.append(mkv)

        if principal_keyval is not None:
            time.sleep(0.01)
            self._call_session(
                "NotifyKeyboardKeysym", GLib.Variant("(ub)", (principal_keyval, True))
            )
            self._call_session(
                "NotifyKeyboardKeysym", GLib.Variant("(ub)", (principal_keyval, False))
            )
        else:
            time.sleep(0.05)

        for mkv in reversed(pressed):
            self._call_session("NotifyKeyboardKeysym", GLib.Variant("(ub)", (mkv, False)))

        return {
            "success": True,
            "modifier_keyvals": modifier_keyvals,
            "principal_keyval": principal_keyval,
            "backend": "mutter-remote-desktop",
        }

    def close(self) -> None:
        with self._lock:
            if self._rd_session is not None and self._started:
                try:
                    self._rd_session.call_sync("Stop", None, Gio.DBusCallFlags.NONE, -1, None)
                except Exception:
                    pass

            self._rd_session = None
            self._stream_path = None
            self._stage_area = None
            self._started = False

    def _root_proxy(self) -> Gio.DBusProxy:
        if self._rd_proxy is None:
            self._rd_proxy = self._dbus_proxy(
                MUTTER_REMOTE_DESKTOP_BUS,
                MUTTER_REMOTE_DESKTOP_PATH,
                MUTTER_REMOTE_DESKTOP_IFACE,
            )
        return self._rd_proxy

    def _screen_cast_proxy(self) -> Gio.DBusProxy:
        if self._sc_proxy is None:
            self._sc_proxy = self._dbus_proxy(
                MUTTER_SCREENCAST_BUS,
                MUTTER_SCREENCAST_PATH,
                MUTTER_SCREENCAST_IFACE,
            )
        return self._sc_proxy

    def _dbus_proxy(self, bus_name: str, object_path: str, interface_name: str) -> Gio.DBusProxy:
        return Gio.DBusProxy.new_for_bus_sync(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.DO_NOT_AUTO_START,
            None,
            bus_name,
            object_path,
            interface_name,
            None,
        )

    def _session_id(self, session_proxy: Gio.DBusProxy) -> str:
        session_id = session_proxy.get_cached_property("SessionId")
        if session_id is not None:
            return str(session_id.unpack())

        properties_proxy = self._dbus_proxy(
            MUTTER_REMOTE_DESKTOP_BUS,
            session_proxy.get_object_path(),
            "org.freedesktop.DBus.Properties",
        )
        result = properties_proxy.call_sync(
            "Get",
            GLib.Variant(
                "(ss)",
                (MUTTER_REMOTE_DESKTOP_SESSION_IFACE, "SessionId"),
            ),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )
        return str(result.unpack()[0])

    def _current_stage_area(self) -> _StageArea:
        display = Gdk.Display.get_default()
        if display is None:
            msg = "GDK display is not available"
            raise RuntimeError(msg)

        monitor_count = display.get_n_monitors()
        if monitor_count <= 0:
            msg = "No monitors are available via GDK"
            raise RuntimeError(msg)

        rectangles = []
        for index in range(monitor_count):
            monitor = display.get_monitor(index)
            geometry = monitor.get_geometry()
            rectangles.append((geometry.x, geometry.y, geometry.width, geometry.height))

        min_x = min(x for x, _y, _w, _h in rectangles)
        min_y = min(y for _x, y, _w, _h in rectangles)
        max_x = max(x + width for x, _y, width, _h in rectangles)
        max_y = max(y + height for _x, y, _w, height in rectangles)
        return _StageArea(
            origin_x=int(min_x),
            origin_y=int(min_y),
            width=int(max_x - min_x),
            height=int(max_y - min_y),
        )

    def _ensure_session(self) -> tuple[str, _StageArea]:
        with self._lock:
            if (
                self._rd_session is not None
                and self._stream_path
                and self._stage_area
                and self._started
            ):
                return self._stream_path, self._stage_area

            self.close()

            rd_path = (
                self._root_proxy()
                .call_sync(
                    "CreateSession",
                    None,
                    Gio.DBusCallFlags.NONE,
                    -1,
                    None,
                )
                .unpack()[0]
            )
            self._rd_session = self._dbus_proxy(
                MUTTER_REMOTE_DESKTOP_BUS,
                rd_path,
                MUTTER_REMOTE_DESKTOP_SESSION_IFACE,
            )
            session_id = self._session_id(self._rd_session)

            sc_path = (
                self._screen_cast_proxy()
                .call_sync(
                    "CreateSession",
                    GLib.Variant(
                        "(a{sv})",
                        ({"remote-desktop-session-id": GLib.Variant("s", session_id)},),
                    ),
                    Gio.DBusCallFlags.NONE,
                    -1,
                    None,
                )
                .unpack()[0]
            )
            screen_cast_session = self._dbus_proxy(
                MUTTER_SCREENCAST_BUS,
                sc_path,
                MUTTER_SCREENCAST_SESSION_IFACE,
            )

            self._stage_area = self._current_stage_area()
            self._stream_path = screen_cast_session.call_sync(
                "RecordArea",
                GLib.Variant(
                    "(iiiia{sv})",
                    (
                        self._stage_area.origin_x,
                        self._stage_area.origin_y,
                        self._stage_area.width,
                        self._stage_area.height,
                        {"cursor-mode": GLib.Variant("u", 0)},
                    ),
                ),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            ).unpack()[0]

            self._rd_session.call_sync("Start", None, Gio.DBusCallFlags.NONE, -1, None)
            self._started = True
            time.sleep(0.05)

            return self._stream_path, self._stage_area

    def _call_session(
        self,
        method_name: str,
        parameters: GLib.Variant,
    ) -> GLib.Variant:
        for attempt in range(2):
            with self._lock:
                self._ensure_session()
                if self._rd_session is None:
                    msg = "Remote desktop session is not available"
                    raise RuntimeError(msg)

                try:
                    return self._rd_session.call_sync(
                        method_name,
                        parameters,
                        Gio.DBusCallFlags.NONE,
                        -1,
                        None,
                    )
                except GLib.Error:
                    if attempt == 0:
                        self.close()
                        continue
                    raise

        msg = f"Failed to call {method_name!r} on the remote desktop session"
        raise RuntimeError(msg)


_REMOTE_INPUT = _MutterRemoteDesktopInput()


def _text_units(text: str) -> list[str]:
    return list(text)


def _key_name_to_keyval(key_name: str) -> int:
    keyval = Gdk.keyval_from_name(key_name)
    if keyval == Gdk.KEY_VoidSymbol and len(key_name) == 1:
        keyval = Gdk.unicode_to_keyval(ord(key_name))
    if keyval == Gdk.KEY_VoidSymbol:
        msg = f"Unknown key: {key_name}"
        raise ValueError(msg)
    return int(keyval)


def _text_unit_to_keyval(unit: str) -> int:
    mapped_key_name = TEXT_KEY_NAME_MAP.get(unit)
    if mapped_key_name is not None:
        return _key_name_to_keyval(mapped_key_name)

    if len(unit) != 1:
        msg = f"Expected a single text unit, got {unit!r}"
        raise ValueError(msg)

    keyval = Gdk.unicode_to_keyval(ord(unit))
    if keyval == Gdk.KEY_VoidSymbol:
        msg = f"Unable to convert text unit {unit!r} to a GDK keyval"
        raise ValueError(msg)
    return int(keyval)


ATSPI_CLICK_EVENTS = {
    "left": {1: "b1c", 2: "b1d"},
    "middle": {1: "b2c", 2: "b2d"},
    "right": {1: "b3c", 2: "b3d"},
}


def _perform_mouse_click_atspi(
    x: int, y: int, *, button: str = "left", click_count: int = 1
) -> JsonDict:
    btn = button.lower()
    click_events = ATSPI_CLICK_EVENTS.get(btn)
    if click_events is None:
        msg = "button must be left, middle, or right"
        raise ValueError(msg)

    Atspi.generate_mouse_event(x, y, "abs")
    time.sleep(0.05)

    if click_count <= 2:
        event_name = click_events.get(click_count, click_events[1])
        Atspi.generate_mouse_event(x, y, event_name)
    else:
        # Triple-click: double + single (no native triple in AT-SPI)
        Atspi.generate_mouse_event(x, y, click_events[2])
        time.sleep(0.05)
        Atspi.generate_mouse_event(x, y, click_events[1])

    return {
        "success": True,
        "x": x,
        "y": y,
        "button": btn,
        "click_count": click_count,
        "backend": "atspi",
    }


def perform_mouse_click(
    x: int, y: int, *, button: str = "left", click_count: int = 1, coordinate_space: str = "logical"
) -> JsonDict:
    if not (1 <= click_count <= 3):
        msg = f"click_count must be 1, 2, or 3 (got {click_count})"
        raise ValueError(msg)
    actual_x, actual_y = x, y
    if coordinate_space == "pixel":
        scale = get_display_scale_factor()
        if scale > 1:
            actual_x = x // scale
            actual_y = y // scale

    try:
        return _REMOTE_INPUT.click_at(actual_x, actual_y, button=button, click_count=click_count)
    except Exception as exc:
        result = _perform_mouse_click_atspi(
            actual_x, actual_y, button=button, click_count=click_count
        )
        result["fallback_error"] = str(exc)
        return result


def _perform_scroll_atspi(
    direction: str,
    clicks: int = 3,
    x: int | None = None,
    y: int | None = None,
) -> JsonDict:
    direction_lower = direction.lower()
    event_name = SCROLL_BUTTON_MAP.get(direction_lower)
    if event_name is None:
        msg = "direction must be up, down, left, or right"
        raise ValueError(msg)

    if x is not None and y is not None:
        Atspi.generate_mouse_event(x, y, "abs")
        time.sleep(0.05)

    for _ in range(clicks):
        Atspi.generate_mouse_event(0, 0, event_name)
        time.sleep(0.03)

    return {
        "success": True,
        "direction": direction_lower,
        "clicks": clicks,
        "x": x,
        "y": y,
        "backend": "atspi",
    }


ATSPI_BUTTON_PRESS = {"left": "b1p", "middle": "b2p", "right": "b3p"}
ATSPI_BUTTON_RELEASE = {"left": "b1r", "middle": "b2r", "right": "b3r"}


def _perform_drag_atspi(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    *,
    button: str = "left",
    steps: int = 10,
    duration_ms: int = 300,
) -> JsonDict:
    btn = button.lower()
    press_event = ATSPI_BUTTON_PRESS.get(btn)
    release_event = ATSPI_BUTTON_RELEASE.get(btn)
    if press_event is None or release_event is None:
        msg = "button must be left, middle, or right"
        raise ValueError(msg)

    Atspi.generate_mouse_event(start_x, start_y, "abs")
    time.sleep(0.05)
    Atspi.generate_mouse_event(start_x, start_y, press_event)
    try:
        actual_steps = max(0, steps)
        start_time = time.monotonic()
        for i in range(1, actual_steps + 1):
            frac = i / actual_steps if actual_steps else 1.0
            ix = int(start_x + frac * (end_x - start_x))
            iy = int(start_y + frac * (end_y - start_y))
            Atspi.generate_mouse_event(ix, iy, "abs")
            if duration_ms > 0 and actual_steps > 0:
                target = start_time + (duration_ms / 1000) * i / actual_steps
                remaining = target - time.monotonic()
                if remaining > 0:
                    time.sleep(remaining)

        if actual_steps == 0:
            Atspi.generate_mouse_event(end_x, end_y, "abs")
    finally:
        Atspi.generate_mouse_event(end_x, end_y, release_event)

    return {
        "success": True,
        "start_x": start_x,
        "start_y": start_y,
        "end_x": end_x,
        "end_y": end_y,
        "button": btn,
        "steps": steps,
        "duration_ms": duration_ms,
        "backend": "atspi",
    }


def perform_scroll(
    direction: str,
    clicks: int = 3,
    x: int | None = None,
    y: int | None = None,
) -> JsonDict:
    if clicks <= 0:
        return {"success": True, "direction": direction.lower(), "clicks": 0, "noop": True}

    if (x is None) != (y is None):
        msg = "Both x and y must be provided together, or neither"
        raise ValueError(msg)

    try:
        return _REMOTE_INPUT.scroll(direction, clicks, x, y)
    except Exception as exc:
        result = _perform_scroll_atspi(direction, clicks, x, y)
        result["fallback_error"] = str(exc)
        return result


def perform_drag(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    *,
    button: str = "left",
    steps: int = 10,
    duration_ms: int = 300,
) -> JsonDict:
    try:
        return _REMOTE_INPUT.drag_to(
            start_x,
            start_y,
            end_x,
            end_y,
            button=button,
            steps=steps,
            duration_ms=duration_ms,
        )
    except Exception as exc:
        result = _perform_drag_atspi(
            start_x,
            start_y,
            end_x,
            end_y,
            button=button,
            steps=steps,
            duration_ms=duration_ms,
        )
        result["fallback_error"] = str(exc)
        return result


def _perform_mouse_move_atspi(x: int, y: int) -> JsonDict:
    Atspi.generate_mouse_event(x, y, "abs")
    return {"success": True, "x": x, "y": y, "backend": "atspi"}


def perform_mouse_move(x: int, y: int) -> JsonDict:
    try:
        return _REMOTE_INPUT.move_to(x, y)
    except Exception as exc:
        result = _perform_mouse_move_atspi(x, y)
        result["fallback_error"] = str(exc)
        return result


def _perform_mouse_move_smooth_atspi(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    *,
    duration_ms: int = 300,
    steps: int = 20,
) -> JsonDict:
    actual_steps = max(1, steps)
    start_time = time.monotonic()
    Atspi.generate_mouse_event(start_x, start_y, "abs")
    for i in range(1, actual_steps + 1):
        frac = i / actual_steps
        ix = int(start_x + frac * (end_x - start_x))
        iy = int(start_y + frac * (end_y - start_y))
        Atspi.generate_mouse_event(ix, iy, "abs")
        if duration_ms > 0:
            target = start_time + (duration_ms / 1000) * i / actual_steps
            remaining = target - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)
    return {
        "success": True,
        "start_x": start_x,
        "start_y": start_y,
        "end_x": end_x,
        "end_y": end_y,
        "duration_ms": duration_ms,
        "steps": actual_steps,
        "backend": "atspi",
    }


def mouse_move_smooth(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration_ms: int = 300,
) -> JsonDict:
    try:
        return _REMOTE_INPUT.move_to_smooth(start_x, start_y, end_x, end_y, duration_ms=duration_ms)
    except Exception as exc:
        result = _perform_mouse_move_smooth_atspi(
            start_x, start_y, end_x, end_y, duration_ms=duration_ms
        )
        result["fallback_error"] = str(exc)
        return result


def _perform_key_press_atspi(key_name: str) -> JsonDict:
    try:
        keyval = _key_name_to_keyval(key_name)
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

    success = Atspi.generate_keyboard_event(
        keyval,
        key_name,
        Atspi.KeySynthType.PRESSRELEASE,
    )

    return {
        "success": bool(success),
        "key_name": key_name,
        "keyval": int(keyval),
        "backend": "atspi",
    }


def press_key(key_name: str) -> JsonDict:
    try:
        return _REMOTE_INPUT.press_key(key_name)
    except Exception as exc:
        result = _perform_key_press_atspi(key_name)
        result["fallback_error"] = str(exc)
        return result


def _validate_modifiers(names: list[str]) -> list[int]:
    keyvals: list[int] = []
    seen: set[int] = set()
    for name in names:
        kv = MODIFIER_KEYVALS.get(name.strip().lower())
        if kv is None:
            valid = ", ".join(sorted({k for k in MODIFIER_KEYVALS if k != "control"}))
            msg = f"Unknown modifier {name!r}. Valid modifiers: {valid}"
            raise ValueError(msg)
        if kv not in seen:
            keyvals.append(kv)
            seen.add(kv)
    return keyvals


def _parse_key_combo(combo: str) -> tuple[list[int], int | None]:
    if not combo or not combo.strip():
        msg = "Key combination string must not be empty"
        raise ValueError(msg)

    tokens = [t.strip() for t in combo.split("+") if t.strip()]
    if not tokens:
        msg = "Key combination string must contain at least one key"
        raise ValueError(msg)

    modifier_keyvals: list[int] = []
    seen: set[int] = set()
    principal_keyval: int | None = None

    for i, token in enumerate(tokens):
        kv = MODIFIER_KEYVALS.get(token.lower())
        if kv is not None:
            if kv not in seen:
                modifier_keyvals.append(kv)
                seen.add(kv)
        else:
            if i != len(tokens) - 1:
                msg = f"Non-modifier key {token!r} must be the last token in the combination"
                raise ValueError(msg)
            principal_keyval = _key_name_to_keyval(token)

    return modifier_keyvals, principal_keyval


def _perform_key_combo_atspi(
    modifier_keyvals: list[int],
    principal_keyval: int | None,
) -> JsonDict:
    try:
        for mkv in modifier_keyvals:
            Atspi.generate_keyboard_event(mkv, "", Atspi.KeySynthType.PRESS)

        if principal_keyval is not None:
            time.sleep(0.01)
            Atspi.generate_keyboard_event(principal_keyval, "", Atspi.KeySynthType.PRESS)
            Atspi.generate_keyboard_event(principal_keyval, "", Atspi.KeySynthType.RELEASE)
        else:
            time.sleep(0.05)

        for mkv in reversed(modifier_keyvals):
            Atspi.generate_keyboard_event(mkv, "", Atspi.KeySynthType.RELEASE)
    except Exception as exc:
        return {"success": False, "error": str(exc), "backend": "atspi"}

    return {
        "success": True,
        "modifier_keyvals": modifier_keyvals,
        "principal_keyval": principal_keyval,
        "backend": "atspi",
    }


def key_combo(combo: str) -> JsonDict:
    modifier_keyvals, principal_keyval = _parse_key_combo(combo)
    try:
        return _REMOTE_INPUT.press_key_combo(modifier_keyvals, principal_keyval)
    except Exception as exc:
        result = _perform_key_combo_atspi(modifier_keyvals, principal_keyval)
        result["fallback_error"] = str(exc)
        return result


def _perform_type_text_atspi(text: str) -> JsonDict:
    success = Atspi.generate_keyboard_event(0, text, Atspi.KeySynthType.STRING)
    return {"success": bool(success), "text_length": len(text), "backend": "atspi"}


def type_text(text: str) -> JsonDict:
    if text == "":
        return {"success": True, "text_length": 0, "backend": "mutter-remote-desktop"}

    try:
        return _REMOTE_INPUT.type_text(text)
    except Exception as exc:
        result = _perform_type_text_atspi(text)
        result["fallback_error"] = str(exc)
        return result


def remote_input_info() -> JsonDict:
    return _REMOTE_INPUT.info()


_screenshot_lock = threading.Lock()


def _acquire_screenshot_bus() -> Gio.DBusConnection:
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    acquire_result = bus.call_sync(
        "org.freedesktop.DBus",
        "/org/freedesktop/DBus",
        "org.freedesktop.DBus",
        "RequestName",
        GLib.Variant("(su)", (GNOME_SCREENSHOT_WELL_KNOWN_NAME, 0x4)),
        GLib.VariantType("(u)"),
        Gio.DBusCallFlags.NONE,
        -1,
        None,
    )
    reply_code = acquire_result.unpack()[0]
    if reply_code not in (1, 4):
        msg = f"Could not acquire {GNOME_SCREENSHOT_WELL_KNOWN_NAME} bus name (code={reply_code})"
        raise RuntimeError(msg)
    return bus


def _release_screenshot_bus(bus: Gio.DBusConnection) -> None:
    try:
        bus.call_sync(
            "org.freedesktop.DBus",
            "/org/freedesktop/DBus",
            "org.freedesktop.DBus",
            "ReleaseName",
            GLib.Variant("(s)", (GNOME_SCREENSHOT_WELL_KNOWN_NAME,)),
            GLib.VariantType("(u)"),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )
    except Exception:
        pass


def _screenshot_proxy() -> Gio.DBusProxy:
    return Gio.DBusProxy.new_for_bus_sync(
        Gio.BusType.SESSION,
        Gio.DBusProxyFlags.DO_NOT_AUTO_START,
        None,
        GNOME_SHELL_SCREENSHOT_BUS,
        GNOME_SHELL_SCREENSHOT_PATH,
        GNOME_SHELL_SCREENSHOT_IFACE,
        None,
    )


def _screenshot_dbus(output_path: str) -> tuple[bool, str]:
    with _screenshot_lock:
        bus = _acquire_screenshot_bus()
        try:
            proxy = _screenshot_proxy()
            result = proxy.call_sync(
                "Screenshot",
                GLib.Variant("(bbs)", (False, False, output_path)),
                Gio.DBusCallFlags.NONE,
                5000,
                None,
            )
            success, filename_used = result.unpack()
            return success, filename_used
        finally:
            _release_screenshot_bus(bus)


def _screenshot_area_dbus(
    x: int, y: int, width: int, height: int, output_path: str
) -> tuple[bool, str]:
    with _screenshot_lock:
        bus = _acquire_screenshot_bus()
        try:
            proxy = _screenshot_proxy()
            result = proxy.call_sync(
                "ScreenshotArea",
                GLib.Variant("(iiiibs)", (x, y, width, height, False, output_path)),
                Gio.DBusCallFlags.NONE,
                5000,
                None,
            )
            success, filename_used = result.unpack()
            return success, filename_used
        finally:
            _release_screenshot_bus(bus)


def _screenshot_window_dbus(
    include_frame: bool, include_cursor: bool, output_path: str
) -> tuple[bool, str]:
    with _screenshot_lock:
        bus = _acquire_screenshot_bus()
        try:
            proxy = _screenshot_proxy()
            result = proxy.call_sync(
                "ScreenshotWindow",
                GLib.Variant("(bbbs)", (include_frame, include_cursor, False, output_path)),
                Gio.DBusCallFlags.NONE,
                5000,
                None,
            )
            success, filename_used = result.unpack()
            return success, filename_used
        finally:
            _release_screenshot_bus(bus)


def _validate_screenshot_path(filename: str | None) -> Path:
    """Validate a screenshot filename is within CACHE_DIR (path traversal protection).

    Raises ValueError if the path is outside CACHE_DIR.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if filename:
        output = Path(filename).expanduser().resolve()
        try:
            output.relative_to(CACHE_DIR.resolve())
        except ValueError as exc:
            msg = f"Path must be within {CACHE_DIR}"
            raise ValueError(msg) from exc
    else:
        output = CACHE_DIR / f"screenshot-{int(time.time() * 1000)}.png"

    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def screenshot_info() -> JsonDict:
    try:
        Gio.DBusProxy.new_for_bus_sync(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.DO_NOT_AUTO_START,
            None,
            GNOME_SHELL_SCREENSHOT_BUS,
            GNOME_SHELL_SCREENSHOT_PATH,
            GNOME_SHELL_SCREENSHOT_IFACE,
            None,
        )
        return {
            "available": True,
            "backend": "dbus",
            "interface": GNOME_SHELL_SCREENSHOT_IFACE,
        }
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def screenshot(
    filename: str | None = None,
    output_format: str | None = None,
    quality: int = 85,
    max_width: int | None = None,
    scale_to_logical: bool = False,
) -> JsonDict:
    try:
        output = _validate_screenshot_path(filename)
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

    try:
        success, filename_used = _screenshot_dbus(str(output))
    except (GLib.Error, RuntimeError) as exc:
        return {"success": False, "error": str(exc)}

    if not success:
        return {"success": False, "error": "Shell screenshot returned failure"}

    scale_factor = get_display_scale_factor()

    # If resizing is requested but PIL is not available, return error
    if (scale_to_logical or max_width) and Image is None:
        return {
            "success": False,
            "error": (
                "Pillow is required for image resizing. "
                "Install with: pip install 'gnome-ui-mcp[hidpi]'"
            ),
        }

    needs_save = False
    final_path = filename_used

    # Open image and get dimensions
    if Image is not None:
        img = Image.open(filename_used)
        pixel_w, pixel_h = img.size
    else:
        # Without PIL, we can't open the image to get dimensions
        # Return basic info without pixel dimensions
        return {
            "success": True,
            "path": final_path,
            "scale_factor": scale_factor,
        }

    logical_w = pixel_w // scale_factor
    logical_h = pixel_h // scale_factor

    if scale_to_logical and scale_factor > 1:
        img = img.resize((logical_w, logical_h), Image.Resampling.LANCZOS)
        needs_save = True

    if max_width and img.size[0] > max_width:
        ratio = max_width / img.size[0]
        new_h = int(img.size[1] * ratio)
        img = img.resize((max_width, new_h), Image.Resampling.LANCZOS)
        needs_save = True

    if output_format and output_format.lower() in ("jpeg", "jpg"):
        final_path = str(Path(filename_used).with_suffix(".jpg"))
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.save(final_path, format="JPEG", quality=quality)
        needs_save = False
    elif needs_save:
        img.save(filename_used)

    return {
        "success": True,
        "path": final_path,
        "scale_factor": scale_factor,
        "pixel_size": [pixel_w, pixel_h],
        "logical_size": [logical_w, logical_h],
    }


def screenshot_area(
    x: int, y: int, width: int, height: int, filename: str | None = None
) -> JsonDict:
    if width <= 0 or height <= 0:
        return {"success": False, "error": "Width and height must be positive"}

    if filename:
        try:
            output = _validate_screenshot_path(filename)
        except ValueError as exc:
            return {"success": False, "error": str(exc)}
    else:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        output = CACHE_DIR / f"screenshot-area-{int(time.time() * 1000)}.png"
        output.parent.mkdir(parents=True, exist_ok=True)

    try:
        success, filename_used = _screenshot_area_dbus(x, y, width, height, str(output))
    except (GLib.Error, RuntimeError) as exc:
        return {"success": False, "error": str(exc)}

    if not success:
        return {"success": False, "error": "Shell ScreenshotArea returned failure"}

    return {
        "success": True,
        "path": filename_used,
        "mode": "area",
        "x": x,
        "y": y,
        "width": width,
        "height": height,
    }


def screenshot_window(
    include_frame: bool = True,
    include_cursor: bool = False,
    filename: str | None = None,
) -> JsonDict:
    if filename:
        try:
            output = _validate_screenshot_path(filename)
        except ValueError as exc:
            return {"success": False, "error": str(exc)}
    else:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        output = CACHE_DIR / f"screenshot-window-{int(time.time() * 1000)}.png"
        output.parent.mkdir(parents=True, exist_ok=True)

    try:
        success, filename_used = _screenshot_window_dbus(include_frame, include_cursor, str(output))
    except (GLib.Error, RuntimeError) as exc:
        return {"success": False, "error": str(exc)}

    if not success:
        return {"success": False, "error": "Shell ScreenshotWindow returned failure"}

    return {
        "success": True,
        "path": filename_used,
        "mode": "window",
        "include_frame": include_frame,
    }


def _child_process_env() -> dict[str, str]:
    env: dict[str, str] = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(Path.home()),
    }
    for key in ("DBUS_SESSION_BUS_ADDRESS", "WAYLAND_DISPLAY", "XDG_RUNTIME_DIR"):
        value = os.environ.get(key)
        if value:
            env[key] = value
    return env


_VALID_SELECTIONS = ("clipboard", "primary")


def clipboard_read(selection: str = "clipboard") -> JsonDict:
    if selection not in _VALID_SELECTIONS:
        msg = f"selection must be 'clipboard' or 'primary' (got {selection!r})"
        raise ValueError(msg)

    if not shutil.which("wl-paste"):
        return {"success": False, "error": "wl-paste not found (install wl-clipboard)"}

    cmd = ["wl-paste", "--no-newline", "--type", "text/plain"]
    if selection == "primary":
        cmd.append("--primary")

    result = subprocess.run(
        cmd, capture_output=True, text=True, check=False, env=_child_process_env(), timeout=5
    )
    if result.returncode != 0:
        return {"success": True, "text": None, "selection": selection}

    return {"success": True, "text": result.stdout, "selection": selection}


def clipboard_write(text: str, selection: str = "clipboard") -> JsonDict:
    if selection not in _VALID_SELECTIONS:
        msg = f"selection must be 'clipboard' or 'primary' (got {selection!r})"
        raise ValueError(msg)

    if not shutil.which("wl-copy"):
        return {"success": False, "error": "wl-copy not found (install wl-clipboard)"}

    cmd = ["wl-copy", "--"]
    if selection == "primary":
        cmd.insert(1, "--primary")

    result = subprocess.run(
        cmd,
        input=text,
        capture_output=True,
        text=True,
        check=False,
        env=_child_process_env(),
        timeout=5,
    )
    if result.returncode != 0:
        return {
            "success": False,
            "error": result.stderr.strip() or "wl-copy failed",
            "selection": selection,
        }

    return {"success": True, "text_length": len(text), "selection": selection}
