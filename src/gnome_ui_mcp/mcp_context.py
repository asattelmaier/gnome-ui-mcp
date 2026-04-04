"""Session and state management for the MCP server.

Central orchestrator for mutable desktop state such as the AT-SPI
connection, boundaries, action history, and locator cache.

Lazy initialization keeps startup cheap and mirrors the single shared
context model used by the server runtime.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field

from .runtime.gi_env import Atspi

_log = logging.getLogger(__name__)


@dataclass
class ScreenshotBackend:
    available: bool
    backend: str | None = None
    interface: str | None = None
    error: str | None = None


@dataclass
class RemoteDesktopBackend:
    available: bool
    version: int | None = None
    supported_device_types: int | None = None
    error: str | None = None


@dataclass
class ActionRecord:
    tool: str
    params: dict[str, object]
    element_id: str | None = None
    app_name: str | None = None
    timestamp: float = field(default_factory=time.time)
    undo_hint: str | None = None


_UNDO_HINTS: dict[str, str | None] = {
    "type_text": "ctrl+z",
    "set_element_text": "ctrl+z",
    "click_element": "Escape",
    "activate_element": "Escape",
    "press_key": None,
    "key_combo": None,
}


class McpContext:
    """Central session state, created lazily on first tool call."""

    def __init__(self) -> None:
        self._initialized: bool = False
        self._desktop: Atspi.Accessible | None = None

        self._boundary_app: str | None = None
        self._boundary_allow_keys: list[str] = []

        self._history: deque[ActionRecord] = deque(maxlen=100)
        self._locators: dict[str, object] = {}
        self._event_subscriptions: dict[str, object] = {}
        self._recording_path: str | None = None
        self._processes: dict[int, object] = {}

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        if not Atspi.is_initialized():
            Atspi.init()
        desktop = Atspi.get_desktop(0)
        if desktop is None:
            msg = "AT-SPI desktop is not available"
            raise RuntimeError(msg)
        self._desktop = desktop
        self._initialized = True
        _log.info("AT-SPI initialized.")

    @property
    def desktop(self) -> Atspi.Accessible:
        self._ensure_initialized()
        return self._desktop

    def desktop_count(self) -> int:
        self._ensure_initialized()
        return Atspi.get_desktop_count()

    def screenshot_backend(self) -> ScreenshotBackend:
        from .desktop import input as desktop_input

        result = desktop_input.screenshot_info()
        return ScreenshotBackend(
            available=bool(result.get("available", False)),
            backend=result.get("backend"),
            interface=result.get("interface"),
            error=result.get("error"),
        )

    def remote_desktop_backend(self) -> RemoteDesktopBackend:
        from .desktop import input as desktop_input

        result = desktop_input.remote_input_info()
        return RemoteDesktopBackend(
            available=bool(result.get("available", False)),
            version=result.get("version"),
            supported_device_types=result.get("supported_device_types"),
            error=result.get("error"),
        )

    def set_boundary(
        self,
        app_name: str | None,
        allow_keys: list[str] | None = None,
    ) -> None:
        self._boundary_app = app_name
        self._boundary_allow_keys = list(allow_keys or [])

    def clear_boundary(self) -> None:
        self._boundary_app = None
        self._boundary_allow_keys = []

    @property
    def boundary_app(self) -> str | None:
        return self._boundary_app

    @property
    def boundary_allow_keys(self) -> list[str]:
        return list(self._boundary_allow_keys)

    def check_boundary(self, element_id: str) -> None:
        """Raise ValueError if an element violates the active boundary."""
        if self._boundary_app is None:
            return
        from .adapters.accessibility import _get_app_name_for_element

        actual_app = _get_app_name_for_element(element_id)
        if actual_app and self._boundary_app.casefold() in actual_app.casefold():
            return
        msg = (
            f"Boundary violation: element belongs to {actual_app!r}, "
            f"but boundary restricts to {self._boundary_app!r}"
        )
        raise ValueError(msg)

    def record_action(
        self,
        tool: str,
        params: dict[str, object],
        element_id: str | None = None,
        app_name: str | None = None,
    ) -> None:
        self._history.append(
            ActionRecord(
                tool=tool,
                params=dict(params),
                element_id=element_id,
                app_name=app_name,
                undo_hint=_UNDO_HINTS.get(tool),
            ),
        )

    def get_history(self, last_n: int = 10) -> list[ActionRecord]:
        items = list(self._history)
        items.reverse()
        return items[:last_n]

    @property
    def history_count(self) -> int:
        return len(self._history)

    def remember_locator(self, element_id: str, locator: object) -> None:
        self._locators[element_id] = locator

    def get_locator(self, element_id: str) -> object | None:
        return self._locators.get(element_id)

    def dispose(self) -> None:
        self._desktop = None
        self._initialized = False
        self._history.clear()
        self._locators.clear()
        self._event_subscriptions.clear()
        self._processes.clear()
        self._recording_path = None
        self._boundary_app = None
        self._boundary_allow_keys = []
        _log.info("McpContext disposed.")
