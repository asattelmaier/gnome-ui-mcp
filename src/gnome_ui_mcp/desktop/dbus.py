from __future__ import annotations

from typing import Any

from ..runtime.gi_env import Gio, GLib

JsonDict = dict[str, Any]


def _build_variant(signature: str | None, args: list | None) -> GLib.Variant | None:
    if not signature or not args:
        return None
    try:
        return GLib.Variant(signature, tuple(args))
    except Exception as exc:
        msg = f"Failed to build GLib.Variant with signature {signature!r}: {exc}"
        raise ValueError(msg) from exc


def _variant_to_json(variant: GLib.Variant) -> Any:
    val = variant.unpack()
    return _deep_unpack(val)


def _deep_unpack(val: Any) -> Any:
    if isinstance(val, GLib.Variant):
        return _deep_unpack(val.unpack())
    if isinstance(val, dict):
        return {k: _deep_unpack(v) for k, v in val.items()}
    if isinstance(val, list | tuple):
        unpacked = [_deep_unpack(item) for item in val]
        return tuple(unpacked) if isinstance(val, tuple) else unpacked
    return val


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

    unpacked = _variant_to_json(result) if result is not None else None

    return {
        "success": True,
        "bus_name": bus_name,
        "object_path": object_path,
        "interface": interface,
        "method": method,
        "result": unpacked,
    }
