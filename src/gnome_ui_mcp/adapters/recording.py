"""Screen recording.

Wraps desktop screencast module. Returns typed data and raises exceptions
on failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..desktop import screencast as _desktop_screencast


def _require(result: dict) -> dict:
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Operation failed")))
    return result


@dataclass
class RecordingStartResult:
    path: str


@dataclass
class RecordingStopResult:
    path: str
    gif_path: str | None


def screen_record_start(
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
    framerate: int = 30,
    draw_cursor: bool = True,
) -> RecordingStartResult:
    """Start screen recording. Raises on failure."""
    result = _require(
        _desktop_screencast.screen_record_start(
            x=x,
            y=y,
            width=width,
            height=height,
            framerate=framerate,
            draw_cursor=draw_cursor,
        )
    )
    return RecordingStartResult(path=result.get("path", ""))


def screen_record_stop(
    to_gif: bool = False,
    gif_fps: int = 10,
    gif_width: int = 640,
) -> RecordingStopResult:
    """Stop screen recording. Raises on failure."""
    result = _require(
        _desktop_screencast.screen_record_stop(
            to_gif=to_gif,
            gif_fps=gif_fps,
            gif_width=gif_width,
        )
    )
    return RecordingStopResult(
        path=result.get("path", ""),
        gif_path=result.get("gif_path"),
    )
