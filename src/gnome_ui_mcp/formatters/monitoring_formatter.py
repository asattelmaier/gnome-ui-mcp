"""Formatters for monitoring data: events, notifications, popups."""

from __future__ import annotations

from ..adapters.monitoring import NotificationList, PollResult
from ..mcp_response import JsonValue


class PollResultFormatter:
    def __init__(self, result: PollResult) -> None:
        self._result = result

    def to_string(self) -> str:
        return f"Polled {self._result.count} events."

    def to_json(self) -> list[dict[str, JsonValue]]:
        return self._result.events


class NotificationListFormatter:
    def __init__(self, result: NotificationList) -> None:
        self._result = result

    def to_string(self) -> str:
        return f"Read {self._result.count} notifications."

    def to_json(self) -> list[dict[str, JsonValue]]:
        return self._result.notifications


class PopupListFormatter:
    def __init__(self, popups: list[dict]) -> None:
        self._popups = popups

    def to_string(self) -> str:
        return f"Found {len(self._popups)} visible shell popups."

    def to_json(self) -> list[dict[str, JsonValue]]:
        return self._popups
