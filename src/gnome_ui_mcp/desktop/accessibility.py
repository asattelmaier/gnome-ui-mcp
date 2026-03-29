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
    state_set = _safe_call(accessible.get_state_set)
    if state_set is None:
        return False
    return bool(_safe_call(lambda: state_set.contains(Atspi.StateType.SHOWING), False))


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
    filter_roles: list[str] | None = None,
    filter_states: list[str] | None = None,
    showing_only: bool = False,
) -> JsonDict | None:
    # Check filters before building the node
    role_name = _safe_call(accessible.get_role_name, "")
    states = _element_states(accessible)

    if showing_only and "showing" not in states:
        return None
    if filter_roles and role_name not in filter_roles:
        # Still recurse into children in case they match
        pass
    if filter_states:
        if not all(s in states for s in filter_states):
            # Still recurse, but mark this node as filtered
            pass

    # Determine if this node itself passes filters
    passes_role = not filter_roles or role_name in filter_roles
    passes_states = not filter_states or all(s in states for s in filter_states)
    passes_showing = not showing_only or "showing" in states
    node_passes = passes_role and passes_states and passes_showing

    # Recurse into children
    children: list[JsonDict] = []
    if depth < max_depth:
        child_count = _safe_call(accessible.get_child_count, 0) or 0
        for index in range(child_count):
            child = _safe_call(lambda idx=index: accessible.get_child_at_index(idx))
            if child is None:
                continue
            child_node = _serialize_tree(
                child,
                path + (index,),
                depth=depth + 1,
                max_depth=max_depth,
                include_actions=include_actions,
                include_text=include_text,
                filter_roles=filter_roles,
                filter_states=filter_states,
                showing_only=showing_only,
            )
            if child_node is not None:
                children.append(child_node)

    # If this node doesn't pass but has matching descendants, include it as a
    # structural ancestor; if it has no matching descendants, prune it entirely.
    if not node_passes and not children:
        return None

    node = _element_summary(
        accessible,
        path,
        include_actions=include_actions,
        include_text=include_text,
    )
    node["children"] = children
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


def _has_active_or_focused_window(app: Atspi.Accessible) -> bool:
    """Check if an application has at least one ACTIVE or FOCUSED top-level window."""
    child_count = _safe_call(app.get_child_count, 0) or 0
    for index in range(child_count):
        win = _safe_call(lambda idx=index: app.get_child_at_index(idx))
        if win is None:
            continue
        state_set = _safe_call(win.get_state_set)
        if state_set is None:
            continue
        if _safe_call(lambda ss=state_set: ss.contains(Atspi.StateType.ACTIVE), False):
            return True
        if _safe_call(lambda ss=state_set: ss.contains(Atspi.StateType.FOCUSED), False):
            return True
    return False


def _is_focused(accessible: Atspi.Accessible) -> bool:
    """O(1) check for the FOCUSED state via state_set.contains()."""
    state_set = _safe_call(accessible.get_state_set)
    if state_set is None:
        return False
    return bool(_safe_call(lambda: state_set.contains(Atspi.StateType.FOCUSED), False))


def current_focus_metadata(*, max_depth: int = 16) -> JsonDict | None:
    best_match: JsonDict | None = None
    best_depth = -1
    shell_match: JsonDict | None = None
    shell_depth = -1

    for app, app_path in _iter_applications():
        app_label = _safe_call(app.get_name, "")
        if not _has_active_or_focused_window(app):
            continue

        is_shell = app_label == "gnome-shell"

        for element, path, depth in _walk_tree(app, app_path, depth=0, max_depth=max_depth):
            if not _is_focused(element):
                continue
            if is_shell:
                if depth > shell_depth:
                    states = _element_states(element)
                    shell_match = _element_summary(
                        element, path, include_actions=False, include_text=True
                    )
                    shell_match["application"] = app_label
                    shell_match["editable"] = _is_editable_element(element, states=states)
                    shell_depth = depth
            else:
                if depth > best_depth:
                    states = _element_states(element)
                    best_match = _element_summary(
                        element, path, include_actions=False, include_text=True
                    )
                    best_match["application"] = app_label
                    best_match["editable"] = _is_editable_element(element, states=states)
                    best_depth = depth

    return best_match if best_match is not None else shell_match


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
    filter_roles: list[str] | None = None,
    filter_states: list[str] | None = None,
    showing_only: bool = False,
) -> JsonDict:
    roots = _select_applications(app_name)
    if not roots:
        error = f"No application matched {app_name!r}" if app_name else "No applications found"
        return {"success": False, "error": error}

    trees: list[JsonDict] = []
    for app, path in roots:
        tree = _serialize_tree(
            app,
            path,
            depth=0,
            max_depth=max_depth,
            include_actions=include_actions,
            include_text=include_text,
            filter_roles=filter_roles,
            filter_states=filter_states,
            showing_only=showing_only,
        )
        if tree is not None:
            trees.append(tree)

    return {"success": True, "trees": trees}


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


def select_element_text(
    element_id: str,
    start_offset: int | None = None,
    end_offset: int | None = None,
) -> JsonDict:
    accessible = _resolve_element(element_id)
    text_iface = _safe_call(accessible.get_text_iface)
    if text_iface is None:
        return {"success": False, "error": "Element does not support the Text interface"}

    states = _element_states(accessible)
    if "selectable-text" not in states:
        return {
            "success": False,
            "error": "Element does not support text selection (missing selectable-text state)",
        }

    char_count = _safe_call(text_iface.get_character_count, 0) or 0
    if char_count <= 0:
        return {"success": False, "error": "Element has no text content to select"}

    if (start_offset is None) != (end_offset is None):
        return {
            "success": False,
            "error": "Both start_offset and end_offset must be provided, or neither for select-all",
        }

    if start_offset is None:
        start_offset = 0
        end_offset = char_count - 1
    else:
        assert end_offset is not None
        if start_offset > end_offset:
            start_offset, end_offset = end_offset, start_offset
        start_offset = max(0, start_offset)
        end_offset = min(end_offset, char_count - 1)

    if start_offset >= end_offset:
        return {"success": False, "error": "Empty selection range after clamping"}

    # Clear existing selections
    n_existing = _safe_call(text_iface.get_n_selections, 0) or 0
    for _ in range(n_existing):
        _safe_call(lambda: text_iface.remove_selection(0))

    added = _safe_call(lambda: text_iface.add_selection(start_offset, end_offset), False)
    if not added:
        return {"success": False, "error": "AT-SPI add_selection failed"}

    selected_text = _safe_call(lambda: text_iface.get_text(start_offset, end_offset), "")
    return {
        "success": True,
        "element_id": element_id,
        "character_count": char_count,
        "selection_start": start_offset,
        "selection_end": end_offset,
        "selected_text": selected_text,
    }


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


# ---------------------------------------------------------------------------
# Item 1: get_focused_element
# ---------------------------------------------------------------------------


def get_focused_element(*, max_depth: int = 16) -> JsonDict:
    """Return the currently focused element wrapped in a success envelope."""
    element = current_focus_metadata(max_depth=max_depth)
    return {"success": True, "element": element}


# ---------------------------------------------------------------------------
# expand_node / collapse_node
# ---------------------------------------------------------------------------


def expand_node(element_id: str) -> JsonDict:
    """Expand a tree/expander node if it is currently collapsed."""
    accessible = _resolve_element(element_id)
    states = _element_states(accessible)

    if "expanded" in states:
        return {
            "success": True,
            "element_id": element_id,
            "toggled": False,
            "state": "expanded",
        }

    action_index = _find_action_index(accessible, "expand or activate")
    if action_index is None:
        action_index = _find_action_index(accessible, None)
    if action_index is None:
        return {
            "success": False,
            "error": "Element has no expand action available",
            "element_id": element_id,
        }

    accessible.do_action(action_index)
    return {
        "success": True,
        "element_id": element_id,
        "toggled": True,
        "state": "expanded",
    }


def collapse_node(element_id: str) -> JsonDict:
    """Collapse a tree/expander node if it is currently expanded."""
    accessible = _resolve_element(element_id)
    states = _element_states(accessible)

    if "expanded" not in states:
        return {
            "success": True,
            "element_id": element_id,
            "toggled": False,
            "state": "collapsed",
        }

    action_index = _find_action_index(accessible, "expand or activate")
    if action_index is None:
        action_index = _find_action_index(accessible, None)
    if action_index is None:
        return {
            "success": False,
            "error": "Element has no collapse action available",
            "element_id": element_id,
        }

    accessible.do_action(action_index)
    return {
        "success": True,
        "element_id": element_id,
        "toggled": True,
        "state": "collapsed",
    }


# ---------------------------------------------------------------------------
# Item 2: get_element_properties
# ---------------------------------------------------------------------------


def get_element_properties(element_id: str) -> JsonDict:
    """Return extended AT-SPI properties for an element."""
    accessible = _resolve_element(element_id)

    # Value interface
    value_iface = _safe_call(accessible.get_value_iface)
    value_data: JsonDict | None = None
    if value_iface is not None:
        value_data = {
            "current": _safe_call(value_iface.get_current_value, 0.0),
            "minimum": _safe_call(value_iface.get_minimum_value, 0.0),
            "maximum": _safe_call(value_iface.get_maximum_value, 0.0),
            "step": _safe_call(value_iface.get_minimum_increment, 0.0),
        }

    # Selection interface
    sel_iface = _safe_call(accessible.get_selection_iface)
    selection_data: JsonDict | None = None
    if sel_iface is not None:
        n_selected = _safe_call(sel_iface.get_n_selected_children, 0) or 0
        selected_children: list[JsonDict] = []
        for i in range(n_selected):
            child = _safe_call(lambda idx=i: sel_iface.get_selected_child(idx))
            if child is not None:
                selected_children.append(
                    {
                        "name": _safe_call(child.get_name, ""),
                        "role": _safe_call(child.get_role_name, ""),
                    }
                )
        selection_data = {
            "n_selected": n_selected,
            "selected_children": selected_children,
        }

    # Relations
    relation_set = _safe_call(accessible.get_relation_set, []) or []
    relations: list[JsonDict] = []
    for rel in relation_set:
        rel_type = _safe_call(rel.get_relation_type)
        type_name = _safe_call(lambda rt=rel_type: rt.value_nick, "") if rel_type else ""
        n_targets = _safe_call(rel.get_n_targets, 0) or 0
        targets: list[JsonDict] = []
        for j in range(n_targets):
            target = _safe_call(lambda idx=j, r=rel: r.get_target(idx))
            if target is not None:
                targets.append(
                    {
                        "name": _safe_call(target.get_name, ""),
                        "role": _safe_call(target.get_role_name, ""),
                    }
                )
        relations.append({"type": type_name, "targets": targets})

    # Attributes
    attributes = _safe_call(accessible.get_attributes, {}) or {}

    # Image interface
    img_iface = _safe_call(accessible.get_image_iface)
    image_data: JsonDict | None = None
    if img_iface is not None:
        img_size = _safe_call(img_iface.get_image_size)
        image_data = {
            "description": _safe_call(img_iface.get_image_description, ""),
            "width": int(img_size.x) if img_size else 0,
            "height": int(img_size.y) if img_size else 0,
        }

    return {
        "success": True,
        "element_id": element_id,
        "value": value_data,
        "selection": selection_data,
        "relations": relations,
        "attributes": dict(attributes),
        "image": image_data,
    }


# ---------------------------------------------------------------------------
# Item 3: get_element_text
# ---------------------------------------------------------------------------


def get_element_text(element_id: str) -> JsonDict:
    """Return detailed text information for an element."""
    accessible = _resolve_element(element_id)
    text_iface = _safe_call(accessible.get_text_iface)
    if text_iface is None:
        return {"success": False, "error": "Element does not support the Text interface"}

    char_count = _safe_call(text_iface.get_character_count, 0) or 0
    text = _safe_call(lambda: text_iface.get_text(0, char_count), "") if char_count > 0 else ""
    caret_offset = _safe_call(text_iface.get_caret_offset, 0) or 0

    # Selections
    n_selections = _safe_call(text_iface.get_n_selections, 0) or 0
    selections: list[JsonDict] = []
    for i in range(n_selections):
        sel_range = _safe_call(lambda idx=i: text_iface.get_selection(idx))
        if sel_range is not None:
            selections.append(
                {
                    "start": sel_range.start_offset,
                    "end": sel_range.end_offset,
                }
            )

    # Attributes at caret
    attr_result = _safe_call(lambda: text_iface.get_text_attributes(caret_offset))
    if attr_result is not None:
        attrs, attr_start, attr_end = attr_result
        attributes_at_caret: JsonDict = {
            "attributes": dict(attrs) if attrs else {},
            "start": attr_start,
            "end": attr_end,
        }
    else:
        attributes_at_caret = {"attributes": {}, "start": 0, "end": 0}

    return {
        "success": True,
        "element_id": element_id,
        "text": text,
        "character_count": char_count,
        "caret_offset": caret_offset,
        "n_selections": n_selections,
        "selections": selections,
        "attributes_at_caret": attributes_at_caret,
    }


# ---------------------------------------------------------------------------
# Item 4: get_table_info / get_table_cell
# ---------------------------------------------------------------------------


def get_table_info(element_id: str) -> JsonDict:
    """Return table dimensions, headers, and caption."""
    accessible = _resolve_element(element_id)
    table_iface = _safe_call(accessible.get_table_iface)
    if table_iface is None:
        return {"success": False, "error": "Element does not support the Table interface"}

    n_rows = _safe_call(table_iface.get_n_rows, 0) or 0
    n_cols = _safe_call(table_iface.get_n_columns, 0) or 0

    headers: list[str] = []
    for col in range(n_cols):
        header = _safe_call(lambda c=col: table_iface.get_column_header(c))
        headers.append(_safe_call(header.get_name, "") if header else "")

    caption_acc = _safe_call(table_iface.get_caption)
    caption = _safe_call(caption_acc.get_name, "") if caption_acc else None

    return {
        "success": True,
        "element_id": element_id,
        "n_rows": n_rows,
        "n_columns": n_cols,
        "headers": headers,
        "caption": caption,
    }


def get_table_cell(element_id: str, row: int, col: int) -> JsonDict:
    """Return info about a specific table cell."""
    accessible = _resolve_element(element_id)
    table_iface = _safe_call(accessible.get_table_iface)
    if table_iface is None:
        return {"success": False, "error": "Element does not support the Table interface"}

    n_rows = _safe_call(table_iface.get_n_rows, 0) or 0
    n_cols = _safe_call(table_iface.get_n_columns, 0) or 0

    if row < 0 or row >= n_rows or col < 0 or col >= n_cols:
        return {
            "success": False,
            "error": (
                f"Cell ({row}, {col}) is out of range for table "
                f"with {n_rows} rows and {n_cols} columns"
            ),
        }

    cell = _safe_call(lambda: table_iface.get_accessible_at(row, col))
    if cell is None:
        return {"success": False, "error": f"Could not access cell at ({row}, {col})"}

    return {
        "success": True,
        "element_id": element_id,
        "row": row,
        "col": col,
        "cell": {
            "name": _safe_call(cell.get_name, ""),
            "role": _safe_call(cell.get_role_name, ""),
        },
    }


# ---------------------------------------------------------------------------
# Item 5: get_element_path
# ---------------------------------------------------------------------------


def get_element_path(element_id: str) -> JsonDict:
    """Return the ancestry chain from root to the given element."""
    try:
        path_indices = _id_to_path(element_id)
    except ValueError:
        return {"success": False, "error": f"Invalid element_id: {element_id}"}

    ancestry: list[JsonDict] = []
    current = _desktop()

    for depth, index in enumerate(path_indices):
        current = _safe_call(lambda node=current, idx=index: node.get_child_at_index(idx))
        if current is None:
            prefix = _path_to_id(path_indices[: depth + 1])
            return {
                "success": False,
                "error": f"Element not found at path prefix: {prefix}",
            }
        prefix_id = _path_to_id(path_indices[: depth + 1])
        ancestry.append(
            {
                "id": prefix_id,
                "name": _safe_call(current.get_name, ""),
                "role": _safe_call(current.get_role_name, ""),
            }
        )

    return {"success": True, "element_id": element_id, "path": ancestry}


# ---------------------------------------------------------------------------
# Item 6: get_elements_by_ids
# ---------------------------------------------------------------------------


def get_elements_by_ids(element_ids: list[str]) -> JsonDict:
    """Resolve multiple element IDs in one call, tracking missing ones."""
    elements: list[JsonDict] = []
    missing: list[str] = []

    for eid in element_ids:
        try:
            accessible = _resolve_element(eid)
            path = tuple(_id_to_path(eid))
            summary = _element_summary(accessible, path)
            elements.append(summary)
        except Exception:
            missing.append(eid)

    return {"success": True, "elements": elements, "missing": missing}
