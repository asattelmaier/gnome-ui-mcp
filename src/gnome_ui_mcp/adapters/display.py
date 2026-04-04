"""Display/monitor listing.

Wraps desktop display module. Returns typed data and raises exceptions
on failure.
"""

from __future__ import annotations

from ..desktop import display as _desktop_display


def _require(result: dict) -> dict:
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Operation failed")))
    return result


def list_monitors() -> list[dict]:
    """List all connected monitors. Raises on failure."""
    result = _require(_desktop_display.list_monitors())
    return result.get("monitors", [])
