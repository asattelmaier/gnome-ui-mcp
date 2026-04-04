"""Session isolation and file dialog.

Wraps desktop session and file_dialog modules. Returns typed data and raises
exceptions on failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..desktop import file_dialog as _desktop_file_dialog
from ..desktop import session as _desktop_session


def _require(result: dict) -> dict:
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Operation failed")))
    return result


@dataclass
class SessionStartResult:
    pid: int
    bus_address: str | None
    width: int
    height: int
    already_running: bool


@dataclass
class SessionInfo:
    running: bool
    pid: int | None
    bus_address: str | None
    width: int | None
    height: int | None


def session_start(width: int = 1920, height: int = 1080) -> SessionStartResult:
    """Start an isolated GNOME Shell session. Raises on failure."""
    result = _require(_desktop_session.session_start(width=width, height=height))
    return SessionStartResult(
        pid=result.get("pid", 0),
        bus_address=result.get("bus_address"),
        width=result.get("width", width),
        height=result.get("height", height),
        already_running=result.get("already_running", False),
    )


def session_stop() -> None:
    """Stop the isolated session. Raises on failure."""
    _require(_desktop_session.session_stop())


def session_info() -> SessionInfo:
    """Get session information. Raises on failure."""
    result = _require(_desktop_session.session_info())
    return SessionInfo(
        running=result.get("running", False),
        pid=result.get("pid"),
        bus_address=result.get("bus_address"),
        width=result.get("width"),
        height=result.get("height"),
    )


def file_dialog_set_path(path: str) -> None:
    """Set a file path in a GTK file dialog. Raises on failure."""
    _require(_desktop_file_dialog.file_dialog_set_path(path=path))
