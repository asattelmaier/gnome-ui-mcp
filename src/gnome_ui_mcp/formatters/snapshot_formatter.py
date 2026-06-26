"""Formatter for element snapshots.

Renders a :class:`~gnome_ui_mcp.desktop.snapshot.Snapshot` into the compact,
indented, LLM-readable text the agent uses to pick a uid, plus the structured
JSON payload. Output line shape:

    uid=7_2 push button "Back" [disabled]

Indentation encodes tree depth. Only a small set of meaningful states is shown
inline to stay token-light (token-optimised design principle).
"""

from __future__ import annotations

from ..desktop.snapshot import Snapshot

type JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]

_INLINE_FLAGS = ("focused", "selected", "checked", "expanded", "disabled", "editable")


def _flags(states: list[str]) -> list[str]:
    return [state for state in _INLINE_FLAGS if state in states]


class SnapshotFormatter:
    """Dual-channel renderer for a captured snapshot."""

    def __init__(self, snapshot: Snapshot) -> None:
        self._snapshot = snapshot

    def to_string(self) -> str:
        snap = self._snapshot
        header = f"Snapshot #{snap.id} ({snap.scope}) -- {len(snap.nodes)} elements"
        if not snap.nodes:
            return (
                f"{header}\nNo elements found in scope. The window may be empty, "
                f"not showing, or accessibility data is unavailable."
            )

        lines = [header, "Reference elements by uid in click/fill/hover/fill_form."]
        for node in snap.nodes:
            indent = "  " * node.depth
            parts = [f"uid={node.uid}", node.role or "node"]
            if node.name:
                parts.append(f'"{node.name}"')
            flags = _flags(node.states)
            if flags:
                parts.append(f"[{', '.join(flags)}]")
            lines.append(indent + " ".join(parts))
        return "\n".join(lines)

    def to_json(self) -> list[dict[str, JsonValue]]:
        return [
            {
                "uid": node.uid,
                "role": node.role,
                "name": node.name,
                "depth": node.depth,
                "states": _flags(node.states),
                "actions": node.actions,
                "has_bounds": node.bounds is not None,
            }
            for node in self._snapshot.nodes
        ]
