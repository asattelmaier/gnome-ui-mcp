from __future__ import annotations

from ..runtime.gi_env import Gio, GLib
from .types import JsonDict, unpack_variant


def _build_variant(signature: str | None, args: list | None) -> GLib.Variant | None:
    if not signature or not args:
        return None
    try:
        return GLib.Variant(signature, tuple(args))
    except Exception as exc:
        msg = f"Failed to build GLib.Variant with signature {signature!r}: {exc}"
        raise ValueError(msg) from exc


def dbus_call(
    bus_name: str,
    object_path: str,
    interface: str,
    method: str,
    signature: str | None = None,
    args: list | None = None,
    timeout_ms: int = 5000,
) -> JsonDict:
    try:
        params = _build_variant(signature, args)
    except ValueError as exc:
        return {"success": False, "error": str(exc), "bus_name": bus_name, "method": method}

    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        result = bus.call_sync(
            bus_name,
            object_path,
            interface,
            method,
            params,
            None,
            Gio.DBusCallFlags.NONE,
            timeout_ms,
            None,
        )
    except Exception as exc:
        return {"success": False, "error": str(exc), "bus_name": bus_name, "method": method}

    unpacked = unpack_variant(result) if result is not None else None

    return {
        "success": True,
        "bus_name": bus_name,
        "object_path": object_path,
        "interface": interface,
        "method": method,
        "result": unpacked,
    }
