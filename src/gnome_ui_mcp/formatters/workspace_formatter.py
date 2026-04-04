"""Formatters for workspace data."""

from __future__ import annotations

from dataclasses import asdict

from ..adapters.workspaces import Workspace
from ..mcp_response import JsonValue


class WorkspaceListFormatter:
    def __init__(self, workspaces: list[Workspace]) -> None:
        self._workspaces = workspaces

    def to_string(self) -> str:
        if not self._workspaces:
            return "No workspaces found."
        lines = [f"Found {len(self._workspaces)} workspaces:"]
        for ws in self._workspaces:
            lines.append(f"  Workspace {ws.index}: {len(ws.windows)} windows")
        return "\n".join(lines)

    def to_json(self) -> list[dict[str, JsonValue]]:
        return [asdict(ws) for ws in self._workspaces]
