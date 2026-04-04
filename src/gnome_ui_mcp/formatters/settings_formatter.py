"""Formatters for settings, keyboard, monitor, and wayland data."""

from __future__ import annotations

from dataclasses import asdict

from ..adapters.keyboard import KeyboardLayout
from ..adapters.monitor import MonitorInfo
from ..mcp_response import JsonValue


class KeyboardLayoutFormatter:
    def __init__(self, layout: KeyboardLayout) -> None:
        self._layout = layout

    def to_string(self) -> str:
        variant = f" ({self._layout.variant})" if self._layout.variant else ""
        return f"Keyboard layout: {self._layout.layout}{variant} [{self._layout.source_type}]"

    def to_json(self) -> dict[str, JsonValue]:
        return asdict(self._layout)


class KeyListFormatter:
    def __init__(self, category: str, keys: list[str]) -> None:
        self._category = category
        self._keys = keys

    def to_string(self) -> str:
        return f"Category '{self._category}': {len(self._keys)} keys."

    def to_json(self) -> dict[str, JsonValue]:
        return {"category": self._category, "keys": self._keys}


class MonitorFormatter:
    def __init__(self, monitor: MonitorInfo) -> None:
        self._monitor = monitor

    def to_string(self) -> str:
        g = self._monitor.geometry
        return (
            f"Monitor {self._monitor.index} ({self._monitor.model}): "
            f"{g.width}x{g.height} at ({g.x}, {g.y})"
        )

    def to_json(self) -> dict[str, JsonValue]:
        return asdict(self._monitor)


class ProtocolListFormatter:
    def __init__(self, protocols: list[str]) -> None:
        self._protocols = protocols

    def to_string(self) -> str:
        return f"Found {len(self._protocols)} Wayland protocols."

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "protocols": self._protocols,
            "protocol_count": len(self._protocols),
        }
