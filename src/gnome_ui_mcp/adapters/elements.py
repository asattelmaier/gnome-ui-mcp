"""Element interaction and query wrappers.

Wraps desktop accessibility and interaction modules. Returns dataclasses/dicts
and raises exceptions on failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..desktop import accessibility as _desktop_accessibility
from ..desktop import highlight as _desktop_highlight
from ..desktop import interaction as _desktop_interaction
from ..desktop import scroll as _desktop_scroll
from ..desktop.types import ElementFilter


def _require(result: dict) -> dict:
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Operation failed")))
    return result


# -- dataclasses --


@dataclass
class ClickResult:
    element_id: str
    method: str
    input_injected: bool
    effect_verified: bool | None


@dataclass
class ActivateResult:
    element_id: str
    resolved_element_id: str
    target_element_id: str
    activation_method: str
    attempts: list[dict]


@dataclass
class FindAndActivateResult:
    element_id: str
    resolved_element_id: str
    target_element_id: str
    activation_method: str
    match: dict


@dataclass
class ResolveClickTargetResult:
    element_id: str
    resolved_element_id: str
    click_target: dict


@dataclass
class ScrollToElementResult:
    scrolls_performed: int
    now_showing: bool
    element_bounds: dict | None


@dataclass
class HighlightResult:
    path: str
    element_id: str
    bounds: dict


@dataclass
class NavigateMenuResult:
    menu_path: list[str]
    activated_items: list[dict]
    final_item: dict | None


# -- public API --


def focus_element(element_id: str) -> None:
    """Focus an element via AT-SPI. Raises on failure."""
    _require(_desktop_accessibility.focus_element(element_id=element_id))


def click_element(
    element_id: str,
    action_name: str | None = None,
    click_count: int = 1,
    button: str = "left",
) -> ClickResult:
    """Click an element. Raises on failure."""
    result = _require(
        _desktop_interaction.click_element(
            element_id=element_id,
            action_name=action_name,
            click_count=click_count,
            button=button,
        )
    )
    return ClickResult(
        element_id=element_id,
        method=result.get("method", ""),
        input_injected=result.get("input_injected", False),
        effect_verified=result.get("effect_verified"),
    )


def activate_element(
    element_id: str,
    action_name: str | None = None,
) -> ActivateResult:
    """Activate an element with multi-strategy fallback. Raises on failure."""
    result = _require(
        _desktop_interaction.activate_element(
            element_id=element_id,
            action_name=action_name,
        )
    )
    return ActivateResult(
        element_id=element_id,
        resolved_element_id=result.get("resolved_element_id", element_id),
        target_element_id=result.get("target_element_id", element_id),
        activation_method=result.get("activation_method", ""),
        attempts=result.get("attempts", []),
    )


def find_and_activate(
    filt: ElementFilter,
    max_depth: int = 8,
    action_name: str | None = None,
) -> FindAndActivateResult:
    """Find and activate an element matching a filter. Raises on failure."""
    result = _require(
        _desktop_interaction.find_and_activate(
            filt,
            max_depth=max_depth,
            action_name=action_name,
        )
    )
    return FindAndActivateResult(
        element_id=result.get("element_id", ""),
        resolved_element_id=result.get("resolved_element_id", ""),
        target_element_id=result.get("target_element_id", ""),
        activation_method=result.get("activation_method", ""),
        match=result.get("match", {}),
    )


def hover_element(element_id: str) -> None:
    """Move cursor to an element's center. Raises on failure."""
    _require(_desktop_interaction.hover_element(element_id=element_id))


def resolve_click_target(element_id: str) -> ResolveClickTargetResult:
    """Resolve the nearest actionable ancestor. Raises on failure."""
    result = _require(_desktop_interaction.resolve_click_target(element_id=element_id))
    return ResolveClickTargetResult(
        element_id=element_id,
        resolved_element_id=result.get("resolved_element_id", element_id),
        click_target=result.get("click_target", {}),
    )


def set_element_text(element_id: str, text: str) -> None:
    """Replace text in an editable element. Raises on failure."""
    _require(_desktop_accessibility.set_element_text(element_id=element_id, text=text))


def select_element_text(
    element_id: str,
    start_offset: int | None = None,
    end_offset: int | None = None,
) -> None:
    """Select text within an element. Raises on failure."""
    _require(
        _desktop_accessibility.select_element_text(
            element_id=element_id,
            start_offset=start_offset,
            end_offset=end_offset,
        )
    )


def set_element_value(element_id: str, value: float) -> None:
    """Set the numeric value of a value element. Raises on failure."""
    _require(_desktop_accessibility.set_element_value(element_id=element_id, value=value))


def expand_node(element_id: str) -> None:
    """Expand a tree/expander node. Raises on failure."""
    _require(_desktop_accessibility.expand_node(element_id=element_id))


def collapse_node(element_id: str) -> None:
    """Collapse a tree/expander node. Raises on failure."""
    _require(_desktop_accessibility.collapse_node(element_id=element_id))


def select_option(element_id: str, child_index: int) -> None:
    """Select a child item via AT-SPI Selection. Raises on failure."""
    _require(
        _desktop_accessibility.select_option(
            element_id=element_id,
            child_index=child_index,
        )
    )


def set_toggle_state(element_id: str, desired_state: bool) -> None:
    """Set a toggle to on/off. Raises on failure."""
    _require(
        _desktop_accessibility.set_toggle_state(
            element_id=element_id,
            desired_state=desired_state,
        )
    )


def navigate_menu(
    menu_path: list[str],
    app_name: str | None = None,
) -> NavigateMenuResult:
    """Navigate a menu hierarchy. Raises on failure."""
    result = _require(_desktop_interaction.navigate_menu(menu_path=menu_path, app_name=app_name))
    return NavigateMenuResult(
        menu_path=result.get("menu_path", menu_path),
        activated_items=result.get("activated_items", []),
        final_item=result.get("final_item"),
    )


def get_focused_element() -> dict:
    """Return metadata about the focused element. Raises on failure."""
    result = _require(_desktop_accessibility.get_focused_element())
    return result


def get_element_properties(element_id: str) -> dict:
    """Return extended AT-SPI properties. Raises on failure."""
    return _require(_desktop_accessibility.get_element_properties(element_id=element_id))


def get_element_text(element_id: str) -> dict:
    """Return detailed text information. Raises on failure."""
    return _require(_desktop_accessibility.get_element_text(element_id=element_id))


def get_table_info(element_id: str) -> dict:
    """Return table dimensions and headers. Raises on failure."""
    return _require(_desktop_accessibility.get_table_info(element_id=element_id))


def get_table_cell(element_id: str, row: int, col: int) -> dict:
    """Return info about a specific table cell. Raises on failure."""
    return _require(_desktop_accessibility.get_table_cell(element_id=element_id, row=row, col=col))


def get_element_path(element_id: str) -> dict:
    """Return ancestry chain. Raises on failure."""
    return _require(_desktop_accessibility.get_element_path(element_id=element_id))


def get_elements_by_ids(element_ids: list[str]) -> dict:
    """Resolve multiple element IDs. Raises on failure."""
    return _require(_desktop_accessibility.get_elements_by_ids(element_ids=element_ids))


def get_tooltip_text(element_id: str) -> str:
    """Return tooltip text. Raises on failure."""
    result = _require(_desktop_accessibility.get_tooltip_text(element_id=element_id))
    return result.get("tooltip_text", "")


def element_at_point(
    x: int,
    y: int,
    app_name: str | None = None,
    max_depth: int = 10,
    include_click_target: bool = True,
) -> dict:
    """Return deepest element at screen coordinates. Raises on failure."""
    return _require(
        _desktop_accessibility.element_at_point(
            x=x,
            y=y,
            app_name=app_name,
            max_depth=max_depth,
            include_click_target=include_click_target,
        )
    )


def scroll_to_element(
    element_id: str,
    max_scrolls: int = 20,
    scroll_clicks: int = 3,
) -> ScrollToElementResult:
    """Scroll an element into view. Raises on failure."""
    result = _require(
        _desktop_scroll.scroll_to_element(
            element_id=element_id,
            max_scrolls=max_scrolls,
            scroll_clicks=scroll_clicks,
        )
    )
    return ScrollToElementResult(
        scrolls_performed=result.get("scrolls_performed", 0),
        now_showing=result.get("now_showing", False),
        element_bounds=result.get("element_bounds"),
    )


def highlight_element(
    element_id: str,
    color: str = "red",
    label: str | None = None,
) -> HighlightResult:
    """Take a screenshot with element highlight. Raises on failure."""
    result = _require(
        _desktop_highlight.highlight_element(
            element_id=element_id,
            color=color,
            label=label,
        )
    )
    return HighlightResult(
        path=result.get("path", ""),
        element_id=element_id,
        bounds=result.get("bounds", {}),
    )
