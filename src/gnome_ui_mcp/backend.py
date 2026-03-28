from __future__ import annotations

from .desktop import accessibility, input, interaction

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
) -> JsonDict:
    return accessibility.accessibility_tree(
        app_name=app_name,
        max_depth=max_depth,
        include_actions=include_actions,
        include_text=include_text,
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


def click_element(element_id: str, action_name: str | None = None) -> JsonDict:
    return interaction.click_element(element_id=element_id, action_name=action_name)


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


def click_at(x: int, y: int, button: str = "left") -> JsonDict:
    return interaction.click_at(x=x, y=y, button=button)


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
