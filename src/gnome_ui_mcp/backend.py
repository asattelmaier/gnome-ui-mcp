from __future__ import annotations

import shutil

from .desktop import accessibility, input, interaction

JsonDict = dict[str, object]


def ping() -> JsonDict:
    applications = accessibility.list_applications()["applications"]
    screenshot_path = shutil.which("gnome-screenshot") or ""

    return {
        "success": True,
        "desktop_count": accessibility.desktop_count(),
        "application_count": len(applications),
        "gnome_screenshot": screenshot_path,
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
    )


def focus_element(element_id: str) -> JsonDict:
    return accessibility.focus_element(element_id=element_id)


def resolve_click_target(element_id: str) -> JsonDict:
    return interaction.resolve_click_target(element_id=element_id)


def click_element(element_id: str, action_name: str | None = None) -> JsonDict:
    return interaction.click_element(element_id=element_id, action_name=action_name)


def activate_element(element_id: str, action_name: str | None = None) -> JsonDict:
    return interaction.activate_element(element_id=element_id, action_name=action_name)


def click_at(x: int, y: int, button: str = "left") -> JsonDict:
    return interaction.click_at(x=x, y=y, button=button)


def set_element_text(element_id: str, text: str) -> JsonDict:
    return accessibility.set_element_text(element_id=element_id, text=text)


def type_text(text: str) -> JsonDict:
    return input.type_text(text=text)


def press_key(key_name: str) -> JsonDict:
    return input.press_key(key_name=key_name)


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


def wait_for_element(
    query: str,
    app_name: str | None = None,
    role: str | None = None,
    timeout_ms: int = 5_000,
    poll_interval_ms: int = 250,
    showing_only: bool = True,
    clickable_only: bool = False,
    bounds_only: bool = False,
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
    )
