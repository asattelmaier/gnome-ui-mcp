"""Action history recording and retrieval (Item 15)."""

from __future__ import annotations

import time
from collections import deque
from typing import Any

JsonDict = dict[str, Any]

_UNDO_HINTS: dict[str, str | None] = {
    "type_text": "ctrl+z",
    "set_element_text": "ctrl+z",
    "click_element": "Escape",
    "activate_element": "Escape",
    "press_key": None,
    "key_combo": None,
}

# Module-level action log (most recent at the end)
_history: deque[JsonDict] = deque(maxlen=100)


def record_action(
    tool: str,
    params: JsonDict,
    element_id: str | None = None,
    app_name: str | None = None,
) -> None:
    """Append an action record to the history buffer."""
    _history.append(
        {
            "tool": tool,
            "params": dict(params),
            "element_id": element_id,
            "app_name": app_name,
            "timestamp": time.time(),
            "undo_hint": _UNDO_HINTS.get(tool),
        }
    )


def get_action_history(last_n: int = 10) -> list[JsonDict]:
    """Return the most recent *last_n* actions (newest first)."""
    items = list(_history)
    items.reverse()
    return items[:last_n]
