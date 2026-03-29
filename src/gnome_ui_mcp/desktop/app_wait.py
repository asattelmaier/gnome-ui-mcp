"""Wait for applications and windows to appear (Item 8)."""

from __future__ import annotations

import time
from typing import Any

from . import accessibility

JsonDict = dict[str, Any]


def wait_for_app(
    app_name: str,
    timeout_ms: int = 10_000,
    poll_interval_ms: int = 250,
    require_window: bool = True,
) -> JsonDict:
    """Poll until *app_name* appears in the AT-SPI application list.

    If *require_window* is ``True`` (default), also wait until the
    application has at least one showing window.
    """
    start = time.monotonic()
    deadline = start + timeout_ms / 1000

    while True:
        apps = accessibility._select_applications(app_name)
        if apps:
            app, path = apps[0]
            app_id = accessibility._path_to_id(path)

            if not require_window:
                return {
                    "success": True,
                    "waited_ms": _elapsed_ms(start),
                    "app_id": app_id,
                    "windows": [],
                }

            win_result = accessibility.list_windows(app_name)
            windows = win_result.get("windows", [])
            showing = [w for w in windows if "showing" in w.get("states", [])]
            if showing:
                return {
                    "success": True,
                    "waited_ms": _elapsed_ms(start),
                    "app_id": app_id,
                    "windows": showing,
                }

        if time.monotonic() >= deadline:
            return {
                "success": False,
                "error": f"Timeout waiting for application {app_name!r}",
                "waited_ms": _elapsed_ms(start),
            }

        time.sleep(max(0.02, poll_interval_ms / 1000))


def wait_for_window(
    query: str,
    app_name: str | None = None,
    role: str | None = None,
    timeout_ms: int = 10_000,
    poll_interval_ms: int = 250,
) -> JsonDict:
    """Poll until a window matching *query* appears."""
    start = time.monotonic()
    deadline = start + timeout_ms / 1000

    while True:
        result = accessibility.find_elements(
            query=query,
            app_name=app_name,
            role=role,
            showing_only=True,
            max_results=1,
        )
        matches = result.get("matches", [])
        if matches:
            return {
                "success": True,
                "waited_ms": _elapsed_ms(start),
                "window": matches[0],
            }

        if time.monotonic() >= deadline:
            return {
                "success": False,
                "error": f"Timeout waiting for window matching {query!r}",
                "waited_ms": _elapsed_ms(start),
            }

        time.sleep(max(0.02, poll_interval_ms / 1000))


def _elapsed_ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)
