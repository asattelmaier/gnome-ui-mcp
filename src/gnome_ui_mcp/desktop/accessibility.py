from __future__ import annotations

import hashlib
import time
from collections.abc import Iterable
from typing import Any

from ..runtime.gi_env import Atspi
from .locators import build_locator, remember_locator

JsonDict = dict[str, Any]

WINDOW_ROLES = {"alert", "dialog", "file chooser", "frame", "window"}
PREFERRED_ACTIONS = ("click", "press", "activate", "jump", "open", "select", "toggle")
MENU_ROLE_KEYWORDS = ("menu", "popup", "popover")
NON_CLICKABLE_ROLES = {
    "description",
    "filler",
    "icon",
    "image",
    "label",
    "panel",
    "paragraph",
    "section",
    "static",
    "text",
}


def _init_atspi() -> None:
    if not Atspi.is_initialized():
        Atspi.init()


def _desktop() -> Atspi.Accessible:
    _init_atspi()
    desktop = Atspi.get_desktop(0)
    if desktop is None:
        msg = "AT-SPI desktop is not available"
        raise RuntimeError(msg)
    return desktop


def desktop_count() -> int:
    _init_atspi()
    return Atspi.get_desktop_count()


def _safe_call(func: Any, default: Any = None) -> Any:
    try:
        return func()
    except Exception:
        return default


def _path_to_id(path: Iterable[int]) -> str:
    return "/".join(str(part) for part in path)


def _id_to_path(element_id: str) -> list[int]:
    try:
        parts = [int(part) for part in element_id.split("/") if part != ""]
    except ValueError as exc:
        msg = f"Invalid element_id: {element_id}"
        raise ValueError(msg) from exc
    if not parts:
        msg = f"Invalid element_id: {element_id!r}"
        raise ValueError(msg)
    return parts


def _resolve_element(element_id: str) -> Atspi.Accessible:
    current = _desktop()
    for index in _id_to_path(element_id):
        current = current.get_child_at_index(index)
        if current is None:
            msg = f"Element not found: {element_id}"
            raise ValueError(msg)
    return current


def _element_states(accessible: Atspi.Accessible) -> list[str]:
    state_set = _safe_call(accessible.get_state_set)
    if state_set is None:
        return []

    states = _safe_call(state_set.get_states, [])
    return sorted(
        state.value_nick
        for state in states
        if state is not None and getattr(state, "value_nick", None)
    )


def _is_showing(accessible: Atspi.Accessible) -> bool:
    return "showing" in _element_states(accessible)


def _contains_point(bounds: JsonDict | None, x: int, y: int) -> bool:
    if bounds is None:
        return False

    return int(bounds["x"]) <= x < int(bounds["x"]) + int(bounds["width"]) and int(
        bounds["y"]
    ) <= y < int(bounds["y"]) + int(bounds["height"])


def _element_bounds(accessible: Atspi.Accessible) -> JsonDict | None:
    component_iface = _safe_call(accessible.get_component_iface)
    if component_iface is None:
        return None

    extents = _safe_call(lambda: component_iface.get_extents(Atspi.CoordType.SCREEN))
    if extents is None:
        return None

    return {
        "x": int(extents.x),
        "y": int(extents.y),
        "width": int(extents.width),
        "height": int(extents.height),
    }


def _is_editable_element(
    accessible: Atspi.Accessible,
    *,
    states: list[str] | None = None,
) -> bool:
    resolved_states = states if states is not None else _element_states(accessible)
    if "editable" in resolved_states:
        return True
    return _safe_call(accessible.get_editable_text_iface) is not None


def _element_text_preview(accessible: Atspi.Accessible, max_chars: int = 200) -> str | None:
    text_iface = _safe_call(accessible.get_text_iface)
    if text_iface is None:
        return None

    char_count = _safe_call(text_iface.get_character_count, 0) or 0
    if char_count <= 0:
        return ""

    return _safe_call(lambda: text_iface.get_text(0, min(char_count, max_chars)), "")


def _element_actions(accessible: Atspi.Accessible) -> list[JsonDict]:
    action_count = _safe_call(accessible.get_n_actions, 0) or 0
    if action_count <= 0:
        return []

    return [
        {
            "index": index,
            "name": _safe_call(lambda idx=index: accessible.get_action_name(idx), ""),
            "description": _safe_call(
                lambda idx=index: accessible.get_action_description(idx),
                "",
            ),
            "key_binding": "",
        }
        for index in range(action_count)
    ]


def _element_summary(
    accessible: Atspi.Accessible,
    path: tuple[int, ...],
    *,
    include_actions: bool = False,
    include_text: bool = False,
) -> JsonDict:
    return {
        "id": _path_to_id(path),
        "name": _safe_call(accessible.get_name, ""),
        "description": _safe_call(accessible.get_description, ""),
        "role": _safe_call(accessible.get_role_name, ""),
        "states": _element_states(accessible),
        "bounds": _element_bounds(accessible),
        "actions": _element_actions(accessible) if include_actions else [],
        "text": _element_text_preview(accessible) if include_text else None,
    }


def _walk_tree(
    accessible: Atspi.Accessible,
    path: tuple[int, ...],
    *,
    depth: int,
    max_depth: int,
) -> Iterable[tuple[Atspi.Accessible, tuple[int, ...], int]]:
    yield accessible, path, depth
    if depth >= max_depth:
        return

    child_count = _safe_call(accessible.get_child_count, 0) or 0
    for index in range(child_count):
        child = _safe_call(lambda idx=index: accessible.get_child_at_index(idx))
        if child is None:
            continue
        yield from _walk_tree(child, path + (index,), depth=depth + 1, max_depth=max_depth)


def _iter_applications() -> Iterable[tuple[Atspi.Accessible, tuple[int, ...]]]:
    desktop = _desktop()
    app_count = _safe_call(desktop.get_child_count, 0) or 0
    for index in range(app_count):
        app = _safe_call(lambda idx=index: desktop.get_child_at_index(idx))
        if app is None:
            continue
        yield app, (index,)


def _select_applications(app_name: str | None) -> list[tuple[Atspi.Accessible, tuple[int, ...]]]:
    matches: list[tuple[Atspi.Accessible, tuple[int, ...]]] = []
    for app, path in _iter_applications():
        name = _safe_call(app.get_name, "")
        if app_name and app_name.casefold() not in name.casefold():
            continue
        matches.append((app, path))
    return matches


def _serialize_tree(
    accessible: Atspi.Accessible,
    path: tuple[int, ...],
    *,
    depth: int,
    max_depth: int,
    include_actions: bool,
    include_text: bool,
) -> JsonDict:
    node = _element_summary(
        accessible,
        path,
        include_actions=include_actions,
        include_text=include_text,
    )
    node["children"] = []

    if depth >= max_depth:
        return node

    child_count = _safe_call(accessible.get_child_count, 0) or 0
    for index in range(child_count):
        child = _safe_call(lambda idx=index: accessible.get_child_at_index(idx))
        if child is None:
            continue
        node["children"].append(
            _serialize_tree(
                child,
                path + (index,),
                depth=depth + 1,
                max_depth=max_depth,
                include_actions=include_actions,
                include_text=include_text,
            )
        )

    return node


def _center(bounds: JsonDict | None) -> tuple[int, int] | None:
    if not bounds:
        return None

    return (
        int(bounds["x"]) + max(1, int(bounds["width"])) // 2,
        int(bounds["y"]) + max(1, int(bounds["height"])) // 2,
    )


def _find_action_index(accessible: Atspi.Accessible, requested_action: str | None) -> int | None:
    action_count = _safe_call(accessible.get_n_actions, 0) or 0
    if action_count <= 0:
        return None

    action_names = [
        _safe_call(lambda idx=index: accessible.get_action_name(idx), "")
        for index in range(action_count)
    ]
    normalized = [name.casefold() for name in action_names]

    if requested_action:
        requested = requested_action.casefold()
        for index, action_name in enumerate(normalized):
            if action_name == requested or requested in action_name:
                return index

    for preferred in PREFERRED_ACTIONS:
        for index, action_name in enumerate(normalized):
            if action_name == preferred or preferred in action_name:
                return index

    return 0 if action_count else None


def _application_name_for_element_id(element_id: str) -> str:
    path = _id_to_path(element_id)
    if not path:
        return ""

    try:
        return _safe_call(_resolve_element(str(path[0])).get_name, "")
    except Exception:
        return ""


def _subtree_fingerprint(
    accessible: Atspi.Accessible,
    *,
    max_depth: int = 2,
    max_nodes: int = 40,
) -> str:
    parts: list[str] = []

    def collect(node: Atspi.Accessible, depth: int) -> None:
        if len(parts) >= max_nodes:
            return

        states = [
            state
            for state in _element_states(node)
            if state in {"active", "checked", "expanded", "focused", "selected", "showing"}
        ]
        parts.append(
            "|".join(
                [
                    _safe_call(node.get_role_name, ""),
                    _safe_call(node.get_name, ""),
                    _element_text_preview(node, max_chars=80) or "",
                    ",".join(states),
                ]
            )
        )

        if depth >= max_depth:
            return

        child_count = _safe_call(node.get_child_count, 0) or 0
        for index in range(child_count):
            child = _safe_call(lambda idx=index: node.get_child_at_index(idx))
            if child is None:
                continue
            collect(child, depth + 1)
            if len(parts) >= max_nodes:
                return

    collect(accessible, 0)
    return hashlib.sha1("\n".join(parts).encode("utf-8")).hexdigest()


def _element_snapshot(element_id: str) -> JsonDict:
    accessible = _resolve_element(element_id)
    return {
        "id": element_id,
        "application": _application_name_for_element_id(element_id),
        "name": _safe_call(accessible.get_name, ""),
        "role": _safe_call(accessible.get_role_name, ""),
        "states": _element_states(accessible),
        "bounds": _element_bounds(accessible),
        "text": _element_text_preview(accessible, max_chars=200),
        "subtree_fingerprint": _subtree_fingerprint(accessible),
    }


def current_focus_metadata(*, max_depth: int = 16) -> JsonDict | None:
    best_match: JsonDict | None = None
    best_depth = -1

    for app, app_path in _iter_applications():
        app_label = _safe_call(app.get_name, "")
        for element, path, depth in _walk_tree(app, app_path, depth=0, max_depth=max_depth):
            states = _element_states(element)
            if "focused" not in states:
                continue
            if depth < best_depth:
                continue

            best_match = _element_summary(element, path, include_actions=False, include_text=True)
            best_match["application"] = app_label
            best_match["editable"] = _is_editable_element(element, states=states)
            best_depth = depth

    return best_match


def _is_menu_like_role(role_name: str) -> bool:
    normalized = role_name.casefold()
    return any(keyword in normalized for keyword in MENU_ROLE_KEYWORDS)


def _visible_shell_popup_matches(
    *,
    max_depth: int = 10,
) -> list[JsonDict]:
    popup_candidates: dict[tuple[int, ...], JsonDict] = {}
    popup_roots: list[tuple[int, ...]] = []

    for app, app_path in _select_applications("gnome-shell"):
        app_label = _safe_call(app.get_name, "")
        for element, path, _depth in _walk_tree(app, app_path, depth=0, max_depth=max_depth):
            if not _is_showing(element):
                continue

            role_name = _safe_call(element.get_role_name, "")
            bounds = _element_bounds(element)
            if bounds is None or int(bounds["width"]) <= 0 or int(bounds["height"]) <= 0:
                continue

            if _is_menu_like_role(role_name):
                item = _element_summary(element, path, include_actions=True, include_text=True)
                item["application"] = app_label
                popup_candidates[path] = item

            if "menu item" not in role_name.casefold():
                continue

            for depth in range(len(path), 0, -1):
                ancestor_path = path[:depth]
                ancestor_item = popup_candidates.get(ancestor_path)
                if ancestor_item is not None:
                    popup_roots.append(ancestor_path)
                    break

    unique_roots = list(dict.fromkeys(popup_roots))
    return [popup_candidates[path] for path in unique_roots]


def _visible_shell_popup_state(*, max_depth: int = 10) -> JsonDict:
    popups = _visible_shell_popup_matches(max_depth=max_depth)
    signature = sorted(str(item["id"]) for item in popups)
    return {
        "popups": popups,
        "popup_count": len(popups),
        "signature": signature,
    }


def _shell_popup_signature() -> list[str]:
    state = _visible_shell_popup_state()
    return list(state["signature"])


def _search_roots(
    *,
    app_name: str | None,
    within_element_id: str | None,
    within_popup: bool,
    max_depth: int,
) -> list[JsonDict]:
    if within_element_id is not None:
        return [
            {
                "accessible": _resolve_element(within_element_id),
                "path": tuple(_id_to_path(within_element_id)),
                "application": _application_name_for_element_id(within_element_id),
                "scope": {
                    "type": "element",
                    "within_element_id": within_element_id,
                },
            }
        ]

    if within_popup:
        roots: list[JsonDict] = []
        for popup in _visible_shell_popup_matches(max_depth=max_depth):
            popup_id = str(popup["id"])
            roots.append(
                {
                    "accessible": _resolve_element(popup_id),
                    "path": tuple(_id_to_path(popup_id)),
                    "application": str(popup.get("application", "")),
                    "scope": {
                        "type": "popup",
                        "within_popup": True,
                        "popup_id": popup_id,
                    },
                }
            )
        return roots

    return [
        {
            "accessible": app,
            "path": app_path,
            "application": _safe_call(app.get_name, ""),
            "scope": {
                "type": "application",
                "app_name": _safe_call(app.get_name, ""),
            },
        }
        for app, app_path in _select_applications(app_name)
    ]


def _element_interaction_metadata(element_id: str) -> JsonDict:
    accessible = _resolve_element(element_id)
    states = _element_states(accessible)
    role_name = _safe_call(accessible.get_role_name, "")
    bounds = _element_bounds(accessible)
    action_index = _find_action_index(accessible, None)

    return {
        "id": element_id,
        "name": _safe_call(accessible.get_name, ""),
        "role": role_name,
        "states": states,
        "showing": "showing" in states,
        "focusable": "focusable" in states or "focused" in states,
        "has_action": action_index is not None,
        "action_index": action_index,
        "bounds": bounds,
        "mouse_clickable": bounds is not None and role_name.casefold() not in NON_CLICKABLE_ROLES,
    }


def _resolve_click_target_metadata(element_id: str) -> JsonDict:
    ancestor_ids = []
    path = _id_to_path(element_id)
    for length in range(len(path), 0, -1):
        ancestor_ids.append(_path_to_id(path[:length]))

    candidates = [_element_interaction_metadata(candidate_id) for candidate_id in ancestor_ids]

    chosen: JsonDict | None = None
    strategy = ""
    for candidate in candidates:
        if candidate["showing"] and candidate["has_action"]:
            chosen = candidate
            strategy = "action"
            break

    if chosen is None:
        for candidate in candidates:
            if candidate["showing"] and candidate["focusable"]:
                chosen = candidate
                strategy = "focus"
                break

    if chosen is None:
        for candidate in candidates:
            if candidate["showing"] and candidate["mouse_clickable"]:
                chosen = candidate
                strategy = "mouse"
                break

    if chosen is None:
        for candidate in candidates:
            if candidate["showing"] and candidate["bounds"] is not None:
                chosen = candidate
                strategy = "mouse"
                break

    if chosen is None:
        msg = "Unable to resolve a clickable ancestor for the element"
        raise ValueError(msg)

    return {
        "element_id": element_id,
        "target_id": chosen["id"],
        "target_name": chosen["name"],
        "target_role": chosen["role"],
        "target_bounds": chosen["bounds"],
        "strategy": strategy,
        "distance": len(path) - len(_id_to_path(str(chosen["id"]))),
        "has_action": chosen["has_action"],
        "focusable": chosen["focusable"],
    }


def list_applications() -> JsonDict:
    applications = [
        {
            "id": _path_to_id(path),
            "name": _safe_call(app.get_name, ""),
            "role": _safe_call(app.get_role_name, ""),
            "children": _safe_call(app.get_child_count, 0) or 0,
        }
        for app, path in _iter_applications()
    ]
    return {"success": True, "applications": applications}


def list_windows(app_name: str | None = None) -> JsonDict:
    windows: list[JsonDict] = []
    for app, app_path in _select_applications(app_name):
        child_count = _safe_call(app.get_child_count, 0) or 0
        for index in range(child_count):
            child = _safe_call(lambda current=app, idx=index: current.get_child_at_index(idx))
            if child is None:
                continue

            role_name = _safe_call(child.get_role_name, "")
            if role_name not in WINDOW_ROLES:
                continue

            window = _element_summary(child, app_path + (index,), include_actions=True)
            window["application"] = _safe_call(app.get_name, "")
            windows.append(window)

    return {"success": True, "windows": windows}


def accessibility_tree(
    app_name: str | None = None,
    max_depth: int = 4,
    include_actions: bool = False,
    include_text: bool = False,
) -> JsonDict:
    roots = _select_applications(app_name)
    if not roots:
        error = f"No application matched {app_name!r}" if app_name else "No applications found"
        return {"success": False, "error": error}

    return {
        "success": True,
        "trees": [
            _serialize_tree(
                app,
                path,
                depth=0,
                max_depth=max_depth,
                include_actions=include_actions,
                include_text=include_text,
            )
            for app, path in roots
        ],
    }


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
    matches: list[JsonDict] = []
    role_query = role.casefold() if role else None

    for root in _search_roots(
        app_name=app_name,
        within_element_id=within_element_id,
        within_popup=within_popup,
        max_depth=max_depth,
    ):
        app = root["accessible"]
        app_path = root["path"]
        app_label = str(root["application"])
        scope = dict(root["scope"])
        for element, path, _depth in _walk_tree(app, app_path, depth=0, max_depth=max_depth):
            name = _safe_call(element.get_name, "")
            description = _safe_call(element.get_description, "")
            role_name = _safe_call(element.get_role_name, "")
            states = _element_states(element)

            if showing_only and "showing" not in states:
                continue
            if bounds_only and _element_bounds(element) is None:
                continue

            element_id = _path_to_id(path)
            try:
                click_target = _resolve_click_target_metadata(element_id)
            except Exception:
                if clickable_only:
                    continue
                click_target = None

            if (
                clickable_only
                and click_target is not None
                and click_target["target_id"] != element_id
            ):
                continue

            haystack = " ".join([app_label, name, description, role_name]).casefold()
            if query and query.casefold() not in haystack:
                continue
            if role_query and role_query not in role_name.casefold():
                continue

            item = _element_summary(element, path, include_actions=True, include_text=True)
            item["application"] = app_label
            item["scope"] = scope
            item["locator"] = build_locator(
                name=name,
                description=description,
                role_name=role_name,
                app_label=app_label,
                within_element_id=(
                    str(scope["within_element_id"])
                    if scope.get("within_element_id") is not None
                    else None
                ),
                within_popup=bool(scope.get("within_popup")),
            )
            remember_locator(item["id"], item["locator"])

            if click_target is not None:
                click_target["locator"] = build_locator(
                    name=str(click_target.get("target_name", "")) or name,
                    description=description,
                    role_name=str(click_target.get("target_role", "")),
                    app_label=app_label,
                    within_element_id=(
                        str(scope["within_element_id"])
                        if scope.get("within_element_id") is not None
                        else None
                    ),
                    within_popup=bool(scope.get("within_popup")),
                )
                remember_locator(str(click_target["target_id"]), click_target["locator"])
            item["click_target"] = click_target
            matches.append(item)

            if len(matches) >= max_results:
                return {"success": True, "matches": matches}

    return {"success": True, "matches": matches}


def focus_element(element_id: str) -> JsonDict:
    accessible = _resolve_element(element_id)
    component_iface = _safe_call(accessible.get_component_iface)
    if component_iface is None:
        return {"success": False, "error": "Element has no component interface"}

    try:
        focused = component_iface.grab_focus()
    except Exception as exc:
        return {"success": False, "error": str(exc), "element_id": element_id}
    return {"success": bool(focused), "element_id": element_id}


def set_element_text(element_id: str, text: str) -> JsonDict:
    accessible = _resolve_element(element_id)
    editable = _safe_call(accessible.get_editable_text_iface)
    if editable is None:
        return {"success": False, "error": "Element is not editable"}

    try:
        editable.set_text_contents(text)
    except Exception as exc:
        return {"success": False, "error": str(exc), "element_id": element_id}
    return {"success": True, "element_id": element_id, "text_length": len(text)}


def element_at_point(
    x: int,
    y: int,
    app_name: str | None = None,
    max_depth: int = 10,
    include_click_target: bool = True,
) -> JsonDict:
    best_match: JsonDict | None = None
    best_depth = -1
    best_area: int | None = None

    for app, app_path in _select_applications(app_name):
        app_label = _safe_call(app.get_name, "")
        for element, path, depth in _walk_tree(app, app_path, depth=0, max_depth=max_depth):
            if not _is_showing(element):
                continue

            bounds = _element_bounds(element)
            if not _contains_point(bounds, x, y):
                continue

            width = int(bounds["width"])
            height = int(bounds["height"])
            area = width * height
            if depth < best_depth:
                continue
            if depth == best_depth and best_area is not None and area >= best_area:
                continue

            item = _element_summary(element, path, include_actions=True, include_text=True)
            item["application"] = app_label
            if include_click_target:
                item["click_target"] = _resolve_click_target_metadata(item["id"])

            best_match = item
            best_depth = depth
            best_area = area

    if best_match is None:
        return {"success": False, "error": "No visible element found at point", "x": x, "y": y}

    return {"success": True, "x": x, "y": y, "match": best_match}


def visible_shell_popups() -> JsonDict:
    state = _visible_shell_popup_state()
    return {"success": True, **state}


def wait_for_popup_count(
    count: int,
    *,
    timeout_ms: int = 5_000,
    poll_interval_ms: int = 100,
    max_depth: int = 10,
) -> JsonDict:
    deadline = time.monotonic() + timeout_ms / 1000
    last_state = _visible_shell_popup_state(max_depth=max_depth)

    while time.monotonic() < deadline:
        state = _visible_shell_popup_state(max_depth=max_depth)
        last_state = state
        if int(state["popup_count"]) == count:
            return {"success": True, "count": count, **state}

        time.sleep(max(0.02, poll_interval_ms / 1000))

    return {
        "success": False,
        "error": "Timeout waiting for popup count",
        "count": count,
        **last_state,
    }


def wait_for_shell_settled(
    *,
    timeout_ms: int = 1_500,
    stable_for_ms: int = 250,
    poll_interval_ms: int = 50,
    max_depth: int = 10,
) -> JsonDict:
    deadline = time.monotonic() + timeout_ms / 1000
    stable_deadline = stable_for_ms / 1000
    last_state = _visible_shell_popup_state(max_depth=max_depth)
    last_signature = list(last_state["signature"])
    last_change_at = time.monotonic()

    while time.monotonic() < deadline:
        state = _visible_shell_popup_state(max_depth=max_depth)
        signature = list(state["signature"])

        if signature != last_signature:
            last_signature = signature
            last_change_at = time.monotonic()

        if time.monotonic() - last_change_at >= stable_deadline:
            return {
                "success": True,
                "stable_for_ms": stable_for_ms,
                **state,
            }

        last_state = state
        time.sleep(max(0.02, poll_interval_ms / 1000))

    return {
        "success": False,
        "error": "Timeout waiting for shell state to settle",
        "stable_for_ms": stable_for_ms,
        **last_state,
    }


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
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        result = find_elements(
            query=query,
            app_name=app_name,
            role=role,
            max_results=1,
            showing_only=showing_only,
            clickable_only=clickable_only,
            bounds_only=bounds_only,
            within_element_id=within_element_id,
            within_popup=within_popup,
        )
        matches = result.get("matches", [])
        if matches:
            return {"success": True, "match": matches[0]}

        time.sleep(max(0.05, poll_interval_ms / 1000))

    return {
        "success": False,
        "error": "Timeout waiting for element",
        "query": query,
    }


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
    deadline = time.monotonic() + timeout_ms / 1000
    last_match: JsonDict | None = None
    while time.monotonic() < deadline:
        result = find_elements(
            query=query,
            app_name=app_name,
            role=role,
            max_results=1,
            showing_only=showing_only,
            clickable_only=clickable_only,
            bounds_only=bounds_only,
            within_element_id=within_element_id,
            within_popup=within_popup,
        )
        matches = result.get("matches", [])
        if not matches:
            return {"success": True, "query": query, "gone": True, "last_match": last_match}

        last_match = matches[0]
        time.sleep(max(0.05, poll_interval_ms / 1000))

    return {
        "success": False,
        "error": "Timeout waiting for element to disappear",
        "query": query,
        "last_match": last_match,
    }
