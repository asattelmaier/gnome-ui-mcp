from __future__ import annotations

import time

from .desktop import (
    accessibility,
    app_wait,
    assertions,
    boundaries,
    events,
    highlight,
    history,
    input,
    interaction,
    keyboard_info,
    monitor_point,
    snapshots,
    wait_act,
)
from .desktop import (
    scroll as scroll_mod,
)

JsonDict = dict[str, object]


def ping() -> JsonDict:
    applications = accessibility.list_applications()["applications"]

    return {
        "success": True,
        "desktop_count": accessibility.desktop_count(),
        "application_count": len(applications),
        "screenshot": input.screenshot_info(),
        "mutter_remote_desktop": input.remote_input_info(),
    }


def list_applications() -> JsonDict:
    return accessibility.list_applications()


def list_windows(app_name: str | None = None) -> JsonDict:
    return accessibility.list_windows(app_name=app_name)


def accessibility_tree(
    app_name: str | None = None,
    max_depth: int = 4,
    include_actions: bool = False,
    include_text: bool = False,
    filter_roles: list[str] | None = None,
    filter_states: list[str] | None = None,
    showing_only: bool = False,
) -> JsonDict:
    return accessibility.accessibility_tree(
        app_name=app_name,
        max_depth=max_depth,
        include_actions=include_actions,
        include_text=include_text,
        filter_roles=filter_roles,
        filter_states=filter_states,
        showing_only=showing_only,
    )


def find_elements(
    query: str = "",
    app_name: str | None = None,
    role: str | None = None,
    max_depth: int = 8,
    max_results: int = 20,
    showing_only: bool = True,
    clickable_only: bool = False,
    bounds_only: bool = False,
    within_element_id: str | None = None,
    within_popup: bool = False,
) -> JsonDict:
    return accessibility.find_elements(
        query=query,
        app_name=app_name,
        role=role,
        max_depth=max_depth,
        max_results=max_results,
        showing_only=showing_only,
        clickable_only=clickable_only,
        bounds_only=bounds_only,
        within_element_id=within_element_id,
        within_popup=within_popup,
    )


def focus_element(element_id: str) -> JsonDict:
    return accessibility.focus_element(element_id=element_id)


def resolve_click_target(element_id: str) -> JsonDict:
    return interaction.resolve_click_target(element_id=element_id)


def click_element(
    element_id: str, action_name: str | None = None, click_count: int = 1
) -> JsonDict:
    return interaction.click_element(
        element_id=element_id, action_name=action_name, click_count=click_count
    )


def activate_element(element_id: str, action_name: str | None = None) -> JsonDict:
    return interaction.activate_element(element_id=element_id, action_name=action_name)


def find_and_activate(
    query: str,
    app_name: str | None = None,
    role: str | None = None,
    max_depth: int = 8,
    showing_only: bool = True,
    clickable_only: bool = False,
    bounds_only: bool = False,
    within_element_id: str | None = None,
    within_popup: bool = False,
    action_name: str | None = None,
) -> JsonDict:
    return interaction.find_and_activate(
        query=query,
        app_name=app_name,
        role=role,
        max_depth=max_depth,
        showing_only=showing_only,
        clickable_only=clickable_only,
        bounds_only=bounds_only,
        within_element_id=within_element_id,
        within_popup=within_popup,
        action_name=action_name,
    )


def click_at(x: int, y: int, button: str = "left", click_count: int = 1) -> JsonDict:
    return interaction.click_at(x=x, y=y, button=button, click_count=click_count)


def scroll(
    direction: str = "down",
    clicks: int = 3,
    x: int | None = None,
    y: int | None = None,
) -> JsonDict:
    return input.perform_scroll(
        direction=direction,
        clicks=clicks,
        x=x,
        y=y,
    )


def mouse_move(x: int, y: int) -> JsonDict:
    return input.perform_mouse_move(x=x, y=y)


def set_element_text(element_id: str, text: str) -> JsonDict:
    return accessibility.set_element_text(element_id=element_id, text=text)


def select_element_text(
    element_id: str,
    start_offset: int | None = None,
    end_offset: int | None = None,
) -> JsonDict:
    return accessibility.select_element_text(
        element_id=element_id, start_offset=start_offset, end_offset=end_offset
    )


def type_text(text: str) -> JsonDict:
    return input.type_text(text=text)


def press_key(
    key_name: str,
    element_id: str | None = None,
    settle_timeout_ms: int = 1_500,
    stable_for_ms: int = 250,
    poll_interval_ms: int = 50,
) -> JsonDict:
    return interaction.press_key(
        key_name=key_name,
        element_id=element_id,
        settle_timeout_ms=settle_timeout_ms,
        stable_for_ms=stable_for_ms,
        poll_interval_ms=poll_interval_ms,
    )


def key_combo(
    combo: str,
    element_id: str | None = None,
    settle_timeout_ms: int = 1_500,
    stable_for_ms: int = 250,
    poll_interval_ms: int = 50,
) -> JsonDict:
    return interaction.key_combo(
        combo=combo,
        element_id=element_id,
        settle_timeout_ms=settle_timeout_ms,
        stable_for_ms=stable_for_ms,
        poll_interval_ms=poll_interval_ms,
    )


def screenshot(filename: str | None = None) -> JsonDict:
    return input.screenshot(filename=filename)


def screenshot_area(
    x: int,
    y: int,
    width: int,
    height: int,
    filename: str | None = None,
) -> JsonDict:
    return input.screenshot_area(x=x, y=y, width=width, height=height, filename=filename)


def screenshot_window(
    window_element_id: str,
    include_frame: bool = True,
    include_cursor: bool = False,
    filename: str | None = None,
) -> JsonDict:
    focus_result = accessibility.focus_element(element_id=window_element_id)
    if not focus_result.get("success"):
        return {
            "success": False,
            "error": f"Could not focus window: {focus_result.get('error', 'unknown')}",
            "window_element_id": window_element_id,
        }
    time.sleep(0.15)
    result = input.screenshot_window(
        include_frame=include_frame, include_cursor=include_cursor, filename=filename
    )
    result["window_element_id"] = window_element_id
    return result


def element_at_point(
    x: int,
    y: int,
    app_name: str | None = None,
    max_depth: int = 10,
    include_click_target: bool = True,
) -> JsonDict:
    return accessibility.element_at_point(
        x=x,
        y=y,
        app_name=app_name,
        max_depth=max_depth,
        include_click_target=include_click_target,
    )


def visible_shell_popups() -> JsonDict:
    return accessibility.visible_shell_popups()


def wait_for_popup_count(
    count: int,
    timeout_ms: int = 5_000,
    poll_interval_ms: int = 100,
    max_depth: int = 10,
) -> JsonDict:
    return accessibility.wait_for_popup_count(
        count=count,
        timeout_ms=timeout_ms,
        poll_interval_ms=poll_interval_ms,
        max_depth=max_depth,
    )


def wait_for_shell_settled(
    timeout_ms: int = 1_500,
    stable_for_ms: int = 250,
    poll_interval_ms: int = 50,
    max_depth: int = 10,
) -> JsonDict:
    return accessibility.wait_for_shell_settled(
        timeout_ms=timeout_ms,
        stable_for_ms=stable_for_ms,
        poll_interval_ms=poll_interval_ms,
        max_depth=max_depth,
    )


def wait_for_element(
    query: str,
    app_name: str | None = None,
    role: str | None = None,
    timeout_ms: int = 5_000,
    poll_interval_ms: int = 250,
    showing_only: bool = True,
    clickable_only: bool = False,
    bounds_only: bool = False,
    within_element_id: str | None = None,
    within_popup: bool = False,
) -> JsonDict:
    return accessibility.wait_for_element(
        query=query,
        app_name=app_name,
        role=role,
        timeout_ms=timeout_ms,
        poll_interval_ms=poll_interval_ms,
        showing_only=showing_only,
        clickable_only=clickable_only,
        bounds_only=bounds_only,
        within_element_id=within_element_id,
        within_popup=within_popup,
    )


def wait_for_element_gone(
    query: str,
    app_name: str | None = None,
    role: str | None = None,
    timeout_ms: int = 5_000,
    poll_interval_ms: int = 250,
    showing_only: bool = True,
    clickable_only: bool = False,
    bounds_only: bool = False,
    within_element_id: str | None = None,
    within_popup: bool = False,
) -> JsonDict:
    return accessibility.wait_for_element_gone(
        query=query,
        app_name=app_name,
        role=role,
        timeout_ms=timeout_ms,
        poll_interval_ms=poll_interval_ms,
        showing_only=showing_only,
        clickable_only=clickable_only,
        bounds_only=bounds_only,
        within_element_id=within_element_id,
        within_popup=within_popup,
    )


def get_focused_element() -> JsonDict:
    return accessibility.get_focused_element()


def get_element_properties(element_id: str) -> JsonDict:
    return accessibility.get_element_properties(element_id=element_id)


def get_element_text(element_id: str) -> JsonDict:
    return accessibility.get_element_text(element_id=element_id)


def get_table_info(element_id: str) -> JsonDict:
    return accessibility.get_table_info(element_id=element_id)


def get_table_cell(element_id: str, row: int, col: int) -> JsonDict:
    return accessibility.get_table_cell(element_id=element_id, row=row, col=col)


def get_element_path(element_id: str) -> JsonDict:
    return accessibility.get_element_path(element_id=element_id)


def get_elements_by_ids(element_ids: list[str]) -> JsonDict:
    return accessibility.get_elements_by_ids(element_ids=element_ids)


# Phase 7b: Wait/action patterns


def wait_for_app(
    app_name: str, timeout_ms: int = 10000, poll_interval_ms: int = 250, require_window: bool = True
) -> JsonDict:
    return app_wait.wait_for_app(
        app_name=app_name,
        timeout_ms=timeout_ms,
        poll_interval_ms=poll_interval_ms,
        require_window=require_window,
    )


def wait_for_window(
    query: str,
    app_name: str | None = None,
    role: str | None = None,
    timeout_ms: int = 10000,
    poll_interval_ms: int = 250,
) -> JsonDict:
    return app_wait.wait_for_window(
        query=query,
        app_name=app_name,
        role=role,
        timeout_ms=timeout_ms,
        poll_interval_ms=poll_interval_ms,
    )


def wait_and_act(**kwargs: object) -> JsonDict:
    return wait_act.wait_and_act(**kwargs)


def scroll_to_element(element_id: str, max_scrolls: int = 20, scroll_clicks: int = 3) -> JsonDict:
    return scroll_mod.scroll_to_element(
        element_id=element_id, max_scrolls=max_scrolls, scroll_clicks=scroll_clicks
    )


# Phase 7c: Assertions, events, snapshots, boundaries, history


def assert_element(**kwargs: object) -> JsonDict:
    return assertions.assert_element(**kwargs)


def assert_text(**kwargs: object) -> JsonDict:
    return assertions.assert_text(**kwargs)


def subscribe_events(event_types: list[str], app_name: str | None = None) -> JsonDict:
    return events.subscribe_events(event_types=event_types, app_name=app_name)


def poll_events(subscription_id: str, timeout_ms: int = 5000, max_events: int = 100) -> JsonDict:
    return events.poll_events(
        subscription_id=subscription_id, timeout_ms=timeout_ms, max_events=max_events
    )


def unsubscribe_events(subscription_id: str) -> JsonDict:
    return events.unsubscribe_events(subscription_id=subscription_id)


def snapshot_state() -> JsonDict:
    return snapshots.snapshot_state()


def compare_state(before_id: str, after_id: str) -> JsonDict:
    return snapshots.compare_state(before_id=before_id, after_id=after_id)


def set_boundaries(
    app_name: str | None = None, allow_global_keys: list[str] | None = None
) -> JsonDict:
    return boundaries.set_boundaries(app_name=app_name, allow_global_keys=allow_global_keys)


def clear_boundaries() -> JsonDict:
    return boundaries.clear_boundaries()


def get_action_history(last_n: int = 10) -> JsonDict:
    return history.get_action_history(last_n=last_n)


# Phase 7d: Utilities


def highlight_element(element_id: str, color: str = "red", label: str | None = None) -> JsonDict:
    return highlight.highlight_element(element_id=element_id, color=color, label=label)


def get_keyboard_layout() -> JsonDict:
    return keyboard_info.get_keyboard_layout()


def list_key_names(category: str = "all") -> JsonDict:
    return keyboard_info.list_key_names(category=category)


def get_monitor_for_point(x: int, y: int) -> JsonDict:
    return monitor_point.get_monitor_for_point(x=x, y=y)
