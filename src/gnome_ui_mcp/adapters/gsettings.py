"""GSettings operations.

Wraps desktop gsettings module. Returns typed data and raises exceptions
on failure.
"""

from __future__ import annotations

from typing import Any

from ..desktop import gsettings as _desktop_gsettings


def _require(result: dict) -> dict:
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Operation failed")))
    return result


def gsettings_get(schema: str, key: str) -> Any:
    """Read a GSettings key value. Raises on failure."""
    result = _require(_desktop_gsettings.gsettings_get(schema=schema, key=key))
    return result.get("value")


def gsettings_set(
    schema: str,
    key: str,
    value: str | int | float | bool,
) -> None:
    """Write a GSettings key value. Raises on failure."""
    _require(_desktop_gsettings.gsettings_set(schema=schema, key=key, value=value))


def gsettings_list_keys(schema: str) -> list[str]:
    """List all keys in a GSettings schema. Raises on failure."""
    result = _require(_desktop_gsettings.gsettings_list_keys(schema=schema))
    return result.get("keys", [])


def gsettings_reset(schema: str, key: str) -> None:
    """Reset a GSettings key to default. Raises on failure."""
    _require(_desktop_gsettings.gsettings_reset(schema=schema, key=key))
