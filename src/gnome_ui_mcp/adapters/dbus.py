"""D-Bus call wrapper.

Wraps desktop dbus module. Returns typed data and raises exceptions
on failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..desktop import dbus as _desktop_dbus


def _require(result: dict) -> dict:
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Operation failed")))
    return result


@dataclass
class DbusCallResult:
    bus_name: str
    object_path: str
    interface: str
    method: str
    value: Any


def dbus_call(
    bus_name: str,
    object_path: str,
    interface: str,
    method: str,
    args: list | None = None,
    signature: str | None = None,
    timeout_ms: int = 5000,
) -> DbusCallResult:
    """Call any D-Bus method. Raises on failure."""
    result = _require(
        _desktop_dbus.dbus_call(
            bus_name=bus_name,
            object_path=object_path,
            interface=interface,
            method=method,
            args=args,
            signature=signature,
            timeout_ms=timeout_ms,
        )
    )
    return DbusCallResult(
        bus_name=bus_name,
        object_path=object_path,
        interface=interface,
        method=method,
        value=result.get("result"),
    )
