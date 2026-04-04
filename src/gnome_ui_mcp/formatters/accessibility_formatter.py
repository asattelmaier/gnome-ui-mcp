"""Formatters for accessibility data.

Each formatter provides dual output: to_string() for LLM text,
to_json() for structured data.
"""

from __future__ import annotations

from dataclasses import asdict

from ..adapters.accessibility import AppInfo, WindowInfo
from ..mcp_response import JsonValue


class ApplicationListFormatter:
    """Formats a list of applications for response output."""

    def __init__(self, apps: list[AppInfo]) -> None:
        self._apps = apps

    def to_string(self) -> str:
        if not self._apps:
            return "No applications found."
        lines = [f"Found {len(self._apps)} applications:"]
        for app in self._apps:
            lines.append(f"  [{app.id}] {app.name} ({app.role}, {app.children} children)")
        return "\n".join(lines)

    def to_json(self) -> list[dict[str, JsonValue]]:
        return [asdict(a) for a in self._apps]


class WindowListFormatter:
    """Formats a list of windows for response output."""

    def __init__(self, windows: list[WindowInfo]) -> None:
        self._windows = windows

    def to_string(self) -> str:
        if not self._windows:
            return "No windows found."
        lines = [f"Found {len(self._windows)} windows:"]
        for w in self._windows:
            lines.append(f"  [{w.id}] {w.name} ({w.role}) - {w.application}")
        return "\n".join(lines)

    def to_json(self) -> list[dict[str, JsonValue]]:
        return [asdict(w) for w in self._windows]
