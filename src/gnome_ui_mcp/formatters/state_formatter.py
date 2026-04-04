"""Formatters for state data: snapshots, OCR, visual analysis."""

from __future__ import annotations

from dataclasses import asdict

from ..adapters.state import (
    ActionHistoryResult,
    OcrResult,
    VisualDiffResult,
)
from ..mcp_response import JsonValue


class OcrResultFormatter:
    def __init__(self, result: OcrResult) -> None:
        self._result = result

    def to_string(self) -> str:
        return f"OCR result: {len(self._result.text)} characters extracted."

    def to_json(self) -> dict[str, JsonValue]:
        return asdict(self._result)


class VisualDiffFormatter:
    def __init__(self, result: VisualDiffResult) -> None:
        self._result = result

    def to_string(self) -> str:
        return f"Visual diff: {self._result.region_count} changed regions."

    def to_json(self) -> dict[str, JsonValue]:
        return asdict(self._result)


class ActionHistoryFormatter:
    def __init__(self, result: ActionHistoryResult) -> None:
        self._result = result

    def to_string(self) -> str:
        return f"Retrieved {len(self._result.actions)} recent actions."

    def to_json(self) -> list[dict[str, JsonValue]]:
        return self._result.actions
