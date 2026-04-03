from __future__ import annotations

import time

from .desktop import (
    accessibility,
    app_lifecycle,
    app_log,
    app_wait,
    apps,
    assertions,
    boundaries,
    dbus,
    display,
    events,
    file_dialog,
    gsettings,
    highlight,
    history,
    input,
    interaction,
    keyboard_info,
    monitor_point,
    notifications,
    ocr,
    screencast,
    session,
    snapshots,
    visual,
    vlm,
    wait_act,
    wayland_info,
    window_management,
    workspaces,
)
from .desktop import (
    scroll as scroll_mod,
)
from .desktop.types import ElementFilter, JsonDict, SettleOptions, TreeOptions


def _check_boundary(element_id: str) -> JsonDict | None:
    """Return an error dict if element_id violates the active boundary, else None."""
    result = boundaries.check_boundary(element_id)
    if not result.get("allowed", True):
        return {"success": False, **result}
    return None


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
    opts = TreeOptions(
        max_depth=max_depth,
        include_actions=include_actions,
        include_text=include_text,
        filter_roles=filter_roles,
        filter_states=filter_states,
        showing_only=showing_only,
    )
    return accessibility.accessibility_tree(app_name=app_name, opts=opts)


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
    filt = ElementFilter(
        query=query,
        role=role,
        app_name=app_name,
        showing_only=showing_only,
        clickable_only=clickable_only,
        bounds_only=bounds_only,
        within_element_id=within_element_id,
        within_popup=within_popup,
    )
    return accessibility.find_elements(filt, max_depth=max_depth, max_results=max_results)


def focus_element(element_id: str) -> JsonDict:
    if err := _check_boundary(element_id):
        return err
    return accessibility.focus_element(element_id=element_id)


def resolve_click_target(element_id: str) -> JsonDict:
    return interaction.resolve_click_target(element_id=element_id)


def click_element(
    element_id: str,
    action_name: str | None = None,
    click_count: int = 1,
    button: str = "left",
) -> JsonDict:
    if err := _check_boundary(element_id):
        return err
    result = interaction.click_element(
        element_id=element_id,
        action_name=action_name,
        click_count=click_count,
        button=button,
    )
    if result.get("success"):
        history.record_action(
            "click_element",
            {
                "element_id": element_id,
                "action_name": action_name,
                "click_count": click_count,
                "button": button,
            },
        )
    return result


def activate_element(element_id: str, action_name: str | None = None) -> JsonDict:
    if err := _check_boundary(element_id):
        return err
    result = interaction.activate_element(element_id=element_id, action_name=action_name)
    if result.get("success"):
        history.record_action(
            "activate_element",
            {"element_id": element_id, "action_name": action_name},
        )
    return result


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
    filt = ElementFilter(
        query=query,
        role=role,
        app_name=app_name,
        showing_only=showing_only,
        clickable_only=clickable_only,
        bounds_only=bounds_only,
        within_element_id=within_element_id,
        within_popup=within_popup,
    )
    return interaction.find_and_activate(filt, max_depth=max_depth, action_name=action_name)


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


def scroll_smooth(
    x: int,
    y: int,
    dx: float = 0.0,
    dy: float = 0.0,
) -> JsonDict:
    return input.scroll_smooth(x=x, y=y, dx=dx, dy=dy)


def drag(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    button: str = "left",
    steps: int = 10,
    duration_ms: int = 300,
) -> JsonDict:
    return input.perform_drag(
        start_x=start_x,
        start_y=start_y,
        end_x=end_x,
        end_y=end_y,
        button=button,
        steps=steps,
        duration_ms=duration_ms,
    )


def touch_rotate(
    center_x: int,
    center_y: int,
    start_angle: float,
    end_angle: float,
    radius: float,
    duration_ms: int = 400,
) -> JsonDict:
    return input.touch_rotate(
        center_x=center_x,
        center_y=center_y,
        start_angle=start_angle,
        end_angle=end_angle,
        radius=radius,
        duration_ms=duration_ms,
    )


def clipboard_read(
    selection: str = "clipboard",
    mime_type: str = "text/plain",
) -> JsonDict:
    return input.clipboard_read(selection=selection, mime_type=mime_type)


def clipboard_write(
    text: str,
    selection: str = "clipboard",
    mime_type: str = "text/plain",
) -> JsonDict:
    return input.clipboard_write(text=text, selection=selection, mime_type=mime_type)


def mouse_move(x: int, y: int) -> JsonDict:
    return input.perform_mouse_move(x=x, y=y)


def mouse_move_relative(dx: float, dy: float) -> JsonDict:
    return input.mouse_move_relative(dx=dx, dy=dy)


def mouse_move_smooth(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration_ms: int = 300,
) -> JsonDict:
    return input.mouse_move_smooth(
        start_x=start_x,
        start_y=start_y,
        end_x=end_x,
        end_y=end_y,
        duration_ms=duration_ms,
    )


def hover_element(element_id: str) -> JsonDict:
    if err := _check_boundary(element_id):
        return err
    return interaction.hover_element(element_id=element_id)


def set_element_text(element_id: str, text: str) -> JsonDict:
    if err := _check_boundary(element_id):
        return err
    result = accessibility.set_element_text(element_id=element_id, text=text)
    if result.get("success"):
        history.record_action(
            "set_element_text",
            {"element_id": element_id, "text": text},
        )
    return result


def select_element_text(
    element_id: str,
    start_offset: int | None = None,
    end_offset: int | None = None,
) -> JsonDict:
    return accessibility.select_element_text(
        element_id=element_id, start_offset=start_offset, end_offset=end_offset
    )


def type_text(text: str) -> JsonDict:
    result = input.type_text(text=text)
    if result.get("success"):
        history.record_action("type_text", {"text": text})
    return result


def press_key(
    key_name: str,
    element_id: str | None = None,
    settle_timeout_ms: int = 1_500,
    stable_for_ms: int = 250,
    poll_interval_ms: int = 50,
) -> JsonDict:
    opts = SettleOptions(
        settle_timeout_ms=settle_timeout_ms,
        stable_for_ms=stable_for_ms,
        poll_interval_ms=poll_interval_ms,
    )
    result = interaction.press_key(key_name=key_name, element_id=element_id, opts=opts)
    if result.get("success"):
        history.record_action(
            "press_key",
            {"key_name": key_name, "element_id": element_id},
        )
    return result


def key_combo(
    combo: str,
    element_id: str | None = None,
    settle_timeout_ms: int = 1_500,
    stable_for_ms: int = 250,
    poll_interval_ms: int = 50,
) -> JsonDict:
    opts = SettleOptions(
        settle_timeout_ms=settle_timeout_ms,
        stable_for_ms=stable_for_ms,
        poll_interval_ms=poll_interval_ms,
    )
    result = interaction.key_combo(combo=combo, element_id=element_id, opts=opts)
    if result.get("success"):
        history.record_action(
            "key_combo",
            {"combo": combo, "element_id": element_id},
        )
    return result


def screenshot(
    filename: str | None = None,
    output_format: str | None = None,
    quality: int = 85,
    max_width: int | None = None,
    scale_to_logical: bool = False,
    return_base64: bool = False,
) -> JsonDict:
    return input.screenshot(
        filename=filename,
        output_format=output_format,
        quality=quality,
        max_width=max_width,
        scale_to_logical=scale_to_logical,
        return_base64=return_base64,
    )


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
    filt = ElementFilter(
        query=query,
        role=role,
        app_name=app_name,
        showing_only=showing_only,
        clickable_only=clickable_only,
        bounds_only=bounds_only,
        within_element_id=within_element_id,
        within_popup=within_popup,
    )
    return accessibility.wait_for_element(
        filt, timeout_ms=timeout_ms, poll_interval_ms=poll_interval_ms
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
    filt = ElementFilter(
        query=query,
        role=role,
        app_name=app_name,
        showing_only=showing_only,
        clickable_only=clickable_only,
        bounds_only=bounds_only,
        within_element_id=within_element_id,
        within_popup=within_popup,
    )
    return accessibility.wait_for_element_gone(
        filt, timeout_ms=timeout_ms, poll_interval_ms=poll_interval_ms
    )


def ocr_screen(
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> JsonDict:
    return ocr.ocr_screen(x=x, y=y, width=width, height=height)


def find_text_ocr(
    target: str,
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> JsonDict:
    return ocr.find_text_ocr(target=target, x=x, y=y, width=width, height=height)


def click_text_ocr(target: str, button: str = "left") -> JsonDict:
    return ocr.click_text_ocr(target=target, button=button)


def gsettings_get(schema: str, key: str) -> JsonDict:
    return gsettings.gsettings_get(schema=schema, key=key)


def gsettings_set(schema: str, key: str, value: object) -> JsonDict:
    return gsettings.gsettings_set(schema=schema, key=key, value=value)


def gsettings_list_keys(schema: str) -> JsonDict:
    return gsettings.gsettings_list_keys(schema=schema)


def gsettings_reset(schema: str, key: str) -> JsonDict:
    return gsettings.gsettings_reset(schema=schema, key=key)


def get_pixel_color(x: int, y: int) -> JsonDict:
    return visual.get_pixel_color(x=x, y=y)


def get_region_color(x: int, y: int, width: int, height: int) -> JsonDict:
    return visual.get_region_color(x=x, y=y, width=width, height=height)


def visual_diff(image_path_1: str, image_path_2: str, threshold: int = 30) -> JsonDict:
    return visual.visual_diff(
        image_path_1=image_path_1, image_path_2=image_path_2, threshold=threshold
    )


def list_desktop_apps(
    query: str = "",
    include_hidden: bool = False,
    max_results: int = 50,
) -> JsonDict:
    return apps.list_desktop_apps(
        query=query, include_hidden=include_hidden, max_results=max_results
    )


def launch_app(desktop_id: str) -> JsonDict:
    return apps.launch_app(desktop_id=desktop_id)


def dbus_call(
    bus_name: str,
    object_path: str,
    interface: str,
    method: str,
    signature: str | None = None,
    args: list | None = None,
    timeout_ms: int = 5000,
) -> JsonDict:
    return dbus.dbus_call(
        bus_name=bus_name,
        object_path=object_path,
        interface=interface,
        method=method,
        signature=signature,
        args=args,
        timeout_ms=timeout_ms,
    )


def list_monitors() -> JsonDict:
    return display.list_monitors()


def switch_workspace(direction: str) -> JsonDict:
    return workspaces.switch_workspace(direction=direction)


def move_window_to_workspace(direction: str) -> JsonDict:
    return workspaces.move_window_to_workspace(direction=direction)


def list_workspaces() -> JsonDict:
    return workspaces.list_workspaces()


def toggle_overview(active: bool | None = None) -> JsonDict:
    return workspaces.toggle_overview(active=active)


def notification_monitor_start() -> JsonDict:
    return notifications.notification_monitor_start()


def notification_monitor_read(clear: bool = True) -> JsonDict:
    return notifications.notification_monitor_read(clear=clear)


def notification_monitor_stop() -> JsonDict:
    return notifications.notification_monitor_stop()


def screen_record_start(
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
    framerate: int = 30,
    draw_cursor: bool = True,
) -> JsonDict:
    return screencast.screen_record_start(
        x=x, y=y, width=width, height=height, framerate=framerate, draw_cursor=draw_cursor
    )


def screen_record_stop(to_gif: bool = False, gif_fps: int = 10, gif_width: int = 640) -> JsonDict:
    return screencast.screen_record_stop(to_gif=to_gif, gif_fps=gif_fps, gif_width=gif_width)


def wayland_protocols(filter_protocol: str | None = None) -> JsonDict:
    return wayland_info.wayland_info(filter_protocol=filter_protocol)


def launch_with_logging(command: str) -> JsonDict:
    return app_log.launch_with_logging(command=command)


def read_app_log(pid: int, last_n_lines: int = 0) -> JsonDict:
    return app_log.read_app_log(pid=pid, last_n_lines=last_n_lines)


def close_window() -> JsonDict:
    return window_management.close_window()


def move_window(dx: int, dy: int) -> JsonDict:
    return window_management.move_window(dx=dx, dy=dy)


def resize_window(dw: int, dh: int) -> JsonDict:
    return window_management.resize_window(dw=dw, dh=dh)


def snap_window(position: str) -> JsonDict:
    return window_management.snap_window(position=position)


def toggle_window_state(state: str) -> JsonDict:
    return window_management.toggle_window_state(state=state)


def type_into(label: str, text: str, submit: bool = False) -> JsonDict:
    return ocr.type_into(label=label, text=text, submit=submit)


def analyze_screenshot(
    prompt: str,
    provider: str = "openrouter",
    model: str | None = None,
) -> JsonDict:
    return vlm.analyze_screenshot(prompt=prompt, provider=provider, model=model)


def compare_screenshots(
    path1: str,
    path2: str,
    prompt: str | None = None,
    provider: str = "openrouter",
    model: str | None = None,
) -> JsonDict:
    return vlm.compare_screenshots(
        path1=path1, path2=path2, prompt=prompt, provider=provider, model=model
    )


# Phase 7a: Deep AT-SPI query tools


def select_option(element_id: str, child_index: int) -> JsonDict:
    if err := _check_boundary(element_id):
        return err
    return accessibility.select_option(element_id=element_id, child_index=child_index)


def set_toggle_state(element_id: str, desired_state: bool) -> JsonDict:
    if err := _check_boundary(element_id):
        return err
    return accessibility.set_toggle_state(element_id=element_id, desired_state=desired_state)


def expand_node(element_id: str) -> JsonDict:
    if err := _check_boundary(element_id):
        return err
    return accessibility.expand_node(element_id=element_id)


def collapse_node(element_id: str) -> JsonDict:
    if err := _check_boundary(element_id):
        return err
    return accessibility.collapse_node(element_id=element_id)


def navigate_menu(
    menu_path: list[str],
    app_name: str | None = None,
) -> JsonDict:
    return interaction.navigate_menu(menu_path=menu_path, app_name=app_name)


def file_dialog_set_path(path: str) -> JsonDict:
    return file_dialog.file_dialog_set_path(path=path)


def dismiss_notification(notification_id: int) -> JsonDict:
    return notifications.dismiss_notification(notification_id=notification_id)


def click_notification_action(notification_id: int, action_key: str) -> JsonDict:
    return notifications.click_notification_action(
        notification_id=notification_id, action_key=action_key
    )


def get_focused_element() -> JsonDict:
    return accessibility.get_focused_element()


def set_element_value(element_id: str, value: float) -> JsonDict:
    if err := _check_boundary(element_id):
        return err
    return accessibility.set_element_value(element_id=element_id, value=value)


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


def get_tooltip_text(element_id: str) -> JsonDict:
    return accessibility.get_tooltip_text(element_id=element_id)


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


# Session isolation


def session_start(width: int = 1920, height: int = 1080) -> JsonDict:
    return session.session_start(width=width, height=height)


def session_stop() -> JsonDict:
    return session.session_stop()


def session_info() -> JsonDict:
    return session.session_info()


# App lifecycle


def close_app(app_name: str) -> JsonDict:
    return app_lifecycle.close_app(app_name=app_name)


def kill_app(app_name: str) -> JsonDict:
    return app_lifecycle.kill_app(app_name=app_name)
