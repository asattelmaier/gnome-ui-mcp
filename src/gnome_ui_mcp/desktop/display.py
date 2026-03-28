from __future__ import annotations

from typing import Any

from ..runtime.gi_env import Gio, GLib

JsonDict = dict[str, Any]

MUTTER_DISPLAY_CONFIG_BUS = "org.gnome.Mutter.DisplayConfig"
MUTTER_DISPLAY_CONFIG_PATH = "/org/gnome/Mutter/DisplayConfig"
MUTTER_DISPLAY_CONFIG_IFACE = "org.gnome.Mutter.DisplayConfig"


def _unpack_variant(val: Any) -> Any:
    if isinstance(val, GLib.Variant):
        return _unpack_variant(val.unpack())
    if isinstance(val, dict):
        return {k: _unpack_variant(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_unpack_variant(item) for item in val]
    return val


def list_monitors() -> JsonDict:
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        result = bus.call_sync(
            MUTTER_DISPLAY_CONFIG_BUS,
            MUTTER_DISPLAY_CONFIG_PATH,
            MUTTER_DISPLAY_CONFIG_IFACE,
            "GetCurrentState",
            None,
            None,
            Gio.DBusCallFlags.NONE,
            5000,
            None,
        )
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    unpacked = _unpack_variant(result)
    _serial, raw_monitors, raw_logical, _properties = unpacked

    # Build logical monitor lookup: connector -> (x, y, scale, is_primary)
    logical_lookup: dict[str, JsonDict] = {}
    for logical in raw_logical:
        lx, ly, scale, _transform, is_primary, connectors, _props = logical
        for conn_info in connectors:
            connector = conn_info[0]
            logical_lookup[connector] = {
                "x": int(lx),
                "y": int(ly),
                "scale": float(scale),
                "is_primary": bool(is_primary),
            }

    monitors: list[JsonDict] = []
    for monitor in raw_monitors:
        connector_info, modes, properties = monitor
        connector, manufacturer, model, serial = connector_info

        # Find current mode (first mode is typically current)
        width = 0
        height = 0
        refresh_rate = 0.0
        if modes:
            first_mode = modes[0]
            _mode_id, width, height, refresh_rate = first_mode[0], first_mode[1], first_mode[2], first_mode[3]

        display_name = properties.get("display-name", "")
        is_builtin = properties.get("is-builtin", False)

        logical = logical_lookup.get(connector, {})

        monitors.append({
            "connector": connector,
            "manufacturer": manufacturer,
            "model": model,
            "serial": serial,
            "display_name": display_name,
            "resolution": f"{width}x{height}",
            "refresh_rate_hz": round(float(refresh_rate), 1),
            "scale": logical.get("scale", 1.0),
            "position": {"x": logical.get("x", 0), "y": logical.get("y", 0)},
            "is_primary": logical.get("is_primary", False),
            "is_builtin": bool(is_builtin),
        })

    return {"success": True, "monitors": monitors, "monitor_count": len(monitors)}
