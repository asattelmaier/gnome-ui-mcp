"""Scroll an element into view (Item 10)."""

from __future__ import annotations

from typing import Any

from . import accessibility, input

JsonDict = dict[str, Any]

_SCROLL_ROLE_KEYWORDS = ("scroll", "viewport", "list box", "tree")


def scroll_to_element(
    element_id: str,
    max_scrolls: int = 20,
    scroll_clicks: int = 3,
) -> JsonDict:
    """Try to make *element_id* visible by scrolling.

    Strategy:
    1. Already showing? Return immediately.
    2. Try AT-SPI ``scroll_to`` API.
    3. Fallback: find nearest scroll-capable parent and inject scroll events.
    """
    try:
        accessible = accessibility._resolve_element(element_id)
    except (ValueError, RuntimeError) as exc:
        return {"success": False, "error": str(exc)}

    # 1. Already visible
    if accessibility._is_showing(accessible):
        return _result(True, 0, True, accessibility._element_bounds(accessible))

    # 2. Try AT-SPI scroll_to API
    comp = accessibility._safe_call(accessible.get_component_iface)
    if comp is not None:
        try:
            scrolled = comp.scroll_to(2)  # Atspi.ScrollType.ANYWHERE == 2
        except Exception:
            scrolled = False

        if scrolled and accessibility._is_showing(accessible):
            return _result(True, 0, True, accessibility._element_bounds(accessible))

    # 3. Fallback: scroll in parent container
    scroll_parent, parent_bounds = _find_scroll_parent(accessible)
    if scroll_parent is None or parent_bounds is None:
        return _result(False, 0, False, accessibility._element_bounds(accessible))

    center_x = int(parent_bounds["x"]) + int(parent_bounds["width"]) // 2
    center_y = int(parent_bounds["y"]) + int(parent_bounds["height"]) // 2

    for scroll_count in range(1, max_scrolls + 1):
        input.perform_scroll("down", clicks=scroll_clicks, x=center_x, y=center_y)
        if accessibility._is_showing(accessible):
            return _result(True, scroll_count, True, accessibility._element_bounds(accessible))

    return _result(False, max_scrolls, False, accessibility._element_bounds(accessible))


def _find_scroll_parent(
    accessible: object,
) -> tuple[object | None, JsonDict | None]:
    """Walk up the parent chain looking for a scroll-like container."""
    current = accessibility._safe_call(getattr(accessible, "get_parent", lambda: None))
    for _ in range(30):
        if current is None:
            return None, None
        role = accessibility._safe_call(current.get_role_name, "") or ""
        if any(kw in role.casefold() for kw in _SCROLL_ROLE_KEYWORDS):
            bounds = accessibility._element_bounds(current)
            if bounds is not None:
                return current, bounds
        current = accessibility._safe_call(current.get_parent)
    return None, None


def _result(
    success: bool,
    scrolls_performed: int,
    now_showing: bool,
    element_bounds: JsonDict | None,
) -> JsonDict:
    return {
        "success": success,
        "scrolls_performed": scrolls_performed,
        "now_showing": now_showing,
        "element_bounds": element_bounds,
    }
