from __future__ import annotations

from typing import Any

from ..runtime.gi_env import Gio, GLib
from .types import JsonDict, unpack_variant


def _json_to_variant(value: Any, current_variant: GLib.Variant) -> GLib.Variant:
    type_string = current_variant.get_type_string()
    if type_string == "s":
        return GLib.Variant("s", str(value))
    if type_string == "i":
        return GLib.Variant("i", int(value))
    if type_string == "u":
        return GLib.Variant("u", int(value))
    if type_string == "b":
        return GLib.Variant("b", bool(value))
    if type_string == "d":
        return GLib.Variant("d", float(value))
    if type_string == "as":
        return GLib.Variant("as", [str(v) for v in value])
    return GLib.Variant(type_string, value)


def gsettings_get(schema: str, key: str) -> JsonDict:
    try:
        settings = Gio.Settings(schema_id=schema)
        variant = settings.get_value(key)
        value = unpack_variant(variant)
    except Exception as exc:
        return {"success": False, "error": str(exc), "schema": schema, "key": key}

    return {"success": True, "schema": schema, "key": key, "value": value}


def gsettings_set(schema: str, key: str, value: Any) -> JsonDict:
    try:
        settings = Gio.Settings(schema_id=schema)
        current = settings.get_value(key)
        new_variant = _json_to_variant(value, current)
        settings.set_value(key, new_variant)
        Gio.Settings.sync()
    except Exception as exc:
        return {"success": False, "error": str(exc), "schema": schema, "key": key}

    return {"success": True, "schema": schema, "key": key, "value": value}


def gsettings_list_keys(schema: str) -> JsonDict:
    try:
        source = Gio.SettingsSchemaSource.get_default()
        schema_obj = source.lookup(schema, True)
        if schema_obj is None:
            return {"success": False, "error": f"Schema {schema!r} not found"}
        keys = list(schema_obj.list_keys())
    except Exception as exc:
        return {"success": False, "error": str(exc), "schema": schema}

    return {"success": True, "schema": schema, "keys": keys, "key_count": len(keys)}


def gsettings_reset(schema: str, key: str) -> JsonDict:
    try:
        settings = Gio.Settings(schema_id=schema)
        settings.reset(key)
        Gio.Settings.sync()
    except Exception as exc:
        return {"success": False, "error": str(exc), "schema": schema, "key": key}

    return {"success": True, "schema": schema, "key": key, "reset": True}
