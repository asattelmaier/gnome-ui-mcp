"""Accessibility tree access via AT-SPI.

Direct AT-SPI integration. Functions return plain Python types and
raise exceptions on failure.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import TypeVar

from ..desktop import accessibility as _desktop_accessibility
from ..desktop.types import ElementFilter, TreeOptions
from ..runtime.gi_env import Atspi

_T = TypeVar("_T")
_log = logging.getLogger(__name__)

WINDOW_ROLES = {"alert", "dialog", "file chooser", "frame", "window"}


# -- low-level helpers --


def _init() -> None:
    if not Atspi.is_initialized():
        Atspi.init()


def _desktop() -> Atspi.Accessible:
    _init()
    desktop = Atspi.get_desktop(0)
    if desktop is None:
        msg = "AT-SPI desktop is not available"
        raise RuntimeError(msg)
    return desktop


def _safe_call(func: Callable[[], _T], default: _T | None = None) -> _T | None:
    try:
        return func()
    except Exception:
        _log.debug("_safe_call failed: %s", func, exc_info=True)
        return default


def _path_to_id(path: tuple[int, ...]) -> str:
    return "/".join(str(p) for p in path)


def _iter_applications() -> Iterator[tuple[Atspi.Accessible, tuple[int, ...]]]:
    desktop = _desktop()
    count = _safe_call(desktop.get_child_count, 0) or 0
    for i in range(count):
        child = _safe_call(lambda idx=i: desktop.get_child_at_index(idx))
        if child is not None:
            yield child, (i,)


# -- data types --


@dataclass
class AppInfo:
    id: str
    name: str
    role: str
    children: int


@dataclass
class WindowInfo:
    id: str
    name: str
    role: str
    application: str


# -- public API --


def desktop_count() -> int:
    _init()
    return Atspi.get_desktop_count()


def _get_app_name_for_element(element_id: str) -> str:
    """Return the application name for the given element ID."""
    try:
        parts = element_id.split("/")
        if not parts:
            return ""
        app_index = int(parts[0])
        desktop = _desktop()
        app = _safe_call(lambda: desktop.get_child_at_index(app_index))
        if app is None:
            return ""
        return _safe_call(app.get_name, "") or ""
    except Exception:
        return ""


def list_applications() -> list[AppInfo]:
    """Return all applications visible in the AT-SPI tree."""
    return [
        AppInfo(
            id=_path_to_id(path),
            name=_safe_call(app.get_name, "") or "",
            role=_safe_call(app.get_role_name, "") or "",
            children=_safe_call(app.get_child_count, 0) or 0,
        )
        for app, path in _iter_applications()
    ]


def list_windows(app_name: str | None = None) -> list[WindowInfo]:
    """Return top-level windows, optionally filtered by application name."""
    windows: list[WindowInfo] = []
    for app, app_path in _iter_applications():
        name = _safe_call(app.get_name, "") or ""
        if app_name and app_name.casefold() not in name.casefold():
            continue

        child_count = _safe_call(app.get_child_count, 0) or 0
        for index in range(child_count):
            child = _safe_call(
                lambda current=app, idx=index: current.get_child_at_index(idx),
            )
            if child is None:
                continue

            role_name = _safe_call(child.get_role_name, "") or ""
            if role_name not in WINDOW_ROLES:
                continue

            windows.append(
                WindowInfo(
                    id=_path_to_id(app_path + (index,)),
                    name=_safe_call(child.get_name, "") or "",
                    role=role_name,
                    application=name,
                )
            )

    return windows


def accessibility_tree(
    app_name: str | None = None,
    opts: TreeOptions | None = None,
) -> list[dict]:
    """Return serialized accessibility trees for the desktop or one application."""
    result = _desktop_accessibility.accessibility_tree(app_name=app_name, opts=opts)
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "No applications found")))
    return list(result.get("trees", []))


def find_elements(
    filt: ElementFilter,
    max_depth: int = 8,
    max_results: int = 20,
) -> list[dict]:
    """Return matching elements for the given filter."""
    result = _desktop_accessibility.find_elements(
        filt,
        max_depth=max_depth,
        max_results=max_results,
    )
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Element search failed")))
    return list(result.get("matches", []))
