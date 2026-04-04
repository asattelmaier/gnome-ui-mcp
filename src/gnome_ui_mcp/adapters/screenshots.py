"""Screenshot operations: area and window.

Wraps desktop input and accessibility modules. Returns typed data and raises
exceptions on failure.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from ..desktop import accessibility as _desktop_accessibility
from ..desktop import input as _desktop_input


def _require(result: dict) -> dict:
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Operation failed")))
    return result


@dataclass
class AreaScreenshotResult:
    path: str


@dataclass
class WindowScreenshotResult:
    path: str
    window_element_id: str


def screenshot_area(
    x: int,
    y: int,
    width: int,
    height: int,
    filename: str | None = None,
) -> AreaScreenshotResult:
    """Capture a rectangular region. Raises on failure."""
    result = _require(
        _desktop_input.screenshot_area(
            x=x,
            y=y,
            width=width,
            height=height,
            filename=filename,
        )
    )
    return AreaScreenshotResult(path=str(result.get("path", "")))


def screenshot_window(
    window_element_id: str,
    include_frame: bool = True,
    include_cursor: bool = False,
    filename: str | None = None,
) -> WindowScreenshotResult:
    """Capture a window to PNG. Focuses the window first. Raises on failure."""
    focus_result = _desktop_accessibility.focus_element(element_id=window_element_id)
    if focus_result.get("success") is False:
        msg = f"Could not focus window: {focus_result.get('error', 'unknown')}"
        raise ValueError(msg)
    time.sleep(0.15)
    result = _require(
        _desktop_input.screenshot_window(
            include_frame=include_frame,
            include_cursor=include_cursor,
            filename=filename,
        )
    )
    return WindowScreenshotResult(
        path=str(result.get("path", "")),
        window_element_id=window_element_id,
    )
