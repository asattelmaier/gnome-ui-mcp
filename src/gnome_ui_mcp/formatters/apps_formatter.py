"""Formatters for application data."""

from __future__ import annotations

from dataclasses import asdict

from ..adapters.apps import DesktopAppList
from ..mcp_response import JsonValue


class DesktopAppListFormatter:
    def __init__(self, app_list: DesktopAppList) -> None:
        self._app_list = app_list

    def to_string(self) -> str:
        if not self._app_list.apps:
            return "No desktop applications found."
        return f"Found {self._app_list.count} desktop applications."

    def to_json(self) -> list[dict[str, JsonValue]]:
        return [asdict(a) for a in self._app_list.apps]
