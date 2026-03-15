from __future__ import annotations

from typing import Any

from . import accessibility, input

JsonDict = dict[str, Any]


def _effect_context(element_id: str | None = None) -> JsonDict:
    context: JsonDict = {"shell_popups": accessibility._shell_popup_signature()}
    if element_id is None:
        return context

    try:
        snapshot = accessibility._element_snapshot(element_id)
    except Exception:
        context["element"] = {"id": element_id, "exists": False}
    else:
        snapshot["exists"] = True
        context["element"] = snapshot
    return context


def _verify_effect(before: JsonDict, after: JsonDict) -> tuple[bool | None, JsonDict]:
    before_popups = before.get("shell_popups", [])
    after_popups = after.get("shell_popups", [])
    if before_popups != after_popups:
        return True, {
            "reason": "shell_popups_changed",
            "before": before_popups,
            "after": after_popups,
        }

    before_element = before.get("element")
    after_element = after.get("element")
    if before_element and before_element.get("exists") and not after_element.get("exists", False):
        return True, {"reason": "target_disappeared"}

    if (
        before_element
        and after_element
        and before_element.get("exists")
        and after_element.get("exists")
    ):
        for field_name in ("text", "bounds", "name"):
            if before_element.get(field_name) != after_element.get(field_name):
                return True, {"reason": f"target_{field_name}_changed"}

        before_states = list(before_element.get("states", []))
        after_states = list(after_element.get("states", []))
        if before_states != after_states:
            changed_states = sorted(set(before_states) ^ set(after_states))
            application = str(before_element.get("application", ""))
            if not (application == "gnome-shell" and changed_states == ["focused"]):
                return True, {"reason": "target_states_changed", "changed_states": changed_states}

        role_name = str(before_element.get("role", ""))
        application = str(before_element.get("application", ""))
        if application == "gnome-shell":
            return False, {"reason": "no_observable_change_in_gnome_shell"}
        if accessibility._is_menu_like_role(role_name):
            return False, {"reason": "no_observable_change_for_menu_target"}

    return None, {"reason": "no_observable_change"}


def _apply_interaction_result(
    result: JsonDict,
    *,
    input_injected: bool,
    effect_verified: bool | None,
    verification: JsonDict,
) -> JsonDict:
    result["input_injected"] = bool(input_injected)
    result["effect_verified"] = effect_verified
    result["verification"] = verification
    result["success"] = bool(input_injected and effect_verified is not False)
    return result


def _activation_keys_for_role(role_name: str) -> list[str]:
    normalized = role_name.casefold()
    if "menu" in normalized:
        return ["space", "Return"]
    return ["Return", "space"]


def resolve_click_target(element_id: str) -> JsonDict:
    try:
        target = accessibility._resolve_click_target_metadata(element_id)
    except Exception as exc:
        return {"success": False, "error": str(exc), "element_id": element_id}

    return {
        "success": True,
        "element_id": element_id,
        "click_target": target,
    }


def click_element(element_id: str, action_name: str | None = None) -> JsonDict:
    target = accessibility._resolve_click_target_metadata(element_id)
    target_id = str(target["target_id"])
    accessible = accessibility._resolve_element(target_id)
    if not accessibility._is_showing(accessible):
        return {
            "success": False,
            "error": "Element is not currently showing on screen",
            "element_id": element_id,
        }

    before = _effect_context(target_id)
    action_index = accessibility._find_action_index(accessible, action_name)
    if action_index is not None:
        performed = accessible.do_action(action_index)
        result = {
            "method": "action",
            "element_id": element_id,
            "target_element_id": target_id,
            "click_target": target,
            "action_index": action_index,
            "action_name": accessibility._safe_call(
                lambda: accessible.get_action_name(action_index),
                "",
            ),
        }
        after = _effect_context(target_id)
        verified, verification = _verify_effect(before, after)
        return _apply_interaction_result(
            result,
            input_injected=bool(performed),
            effect_verified=verified,
            verification=verification,
        )

    bounds = accessibility._element_bounds(accessible)
    center = accessibility._center(bounds)
    if center is None:
        return {
            "success": False,
            "error": "Element is neither actionable nor clickable by bounds",
        }

    result = input.perform_mouse_click(center[0], center[1])
    after = _effect_context(target_id)
    verified, verification = _verify_effect(before, after)
    result["element_id"] = element_id
    result["target_element_id"] = target_id
    result["click_target"] = target
    result["method"] = "mouse"
    return _apply_interaction_result(
        result,
        input_injected=bool(result.get("success")),
        effect_verified=verified,
        verification=verification,
    )


def activate_element(element_id: str, action_name: str | None = None) -> JsonDict:
    target = accessibility._resolve_click_target_metadata(element_id)
    target_id = str(target["target_id"])
    accessible = accessibility._resolve_element(target_id)
    if not accessibility._is_showing(accessible):
        return {
            "success": False,
            "error": "Element is not currently showing on screen",
            "element_id": element_id,
            "target_element_id": target_id,
        }

    attempts: list[JsonDict] = []
    current_before = _effect_context(target_id)

    action_index = accessibility._find_action_index(accessible, action_name)
    if action_index is not None:
        performed = accessible.do_action(action_index)
        current_after = _effect_context(target_id)
        verified, verification = _verify_effect(current_before, current_after)
        attempt = _apply_interaction_result(
            {
                "method": "action",
                "action_index": action_index,
                "action_name": accessibility._safe_call(
                    lambda: accessible.get_action_name(action_index),
                    "",
                ),
            },
            input_injected=bool(performed),
            effect_verified=verified,
            verification=verification,
        )
        attempts.append(attempt)
        if attempt["success"]:
            return {
                "success": True,
                "element_id": element_id,
                "target_element_id": target_id,
                "click_target": target,
                "activation_method": attempt["method"],
                "attempts": attempts,
            }
        current_before = current_after

    focus_result = accessibility.focus_element(target_id)
    if focus_result.get("success"):
        for key_name in _activation_keys_for_role(str(target["target_role"])):
            key_result = input.press_key(key_name)
            current_after = _effect_context(target_id)
            verified, verification = _verify_effect(current_before, current_after)
            attempt = _apply_interaction_result(
                {
                    "method": "focus+key",
                    "key_name": key_name,
                    "focus_element_id": target_id,
                    "backend": key_result.get("backend"),
                },
                input_injected=bool(key_result.get("success")),
                effect_verified=verified,
                verification=verification,
            )
            if key_result.get("fallback_error"):
                attempt["fallback_error"] = key_result["fallback_error"]
            attempts.append(attempt)
            if attempt["success"]:
                return {
                    "success": True,
                    "element_id": element_id,
                    "target_element_id": target_id,
                    "click_target": target,
                    "activation_method": attempt["method"],
                    "attempts": attempts,
                }
            current_before = current_after

    center = accessibility._center(accessibility._element_bounds(accessible))
    if center is not None:
        mouse_result = input.perform_mouse_click(center[0], center[1])
        current_after = _effect_context(target_id)
        verified, verification = _verify_effect(current_before, current_after)
        attempt = _apply_interaction_result(
            {
                "method": "mouse",
                "x": center[0],
                "y": center[1],
                "button": mouse_result.get("button", "left"),
                "backend": mouse_result.get("backend"),
            },
            input_injected=bool(mouse_result.get("success")),
            effect_verified=verified,
            verification=verification,
        )
        if mouse_result.get("stream_path"):
            attempt["stream_path"] = mouse_result["stream_path"]
        if mouse_result.get("fallback_error"):
            attempt["fallback_error"] = mouse_result["fallback_error"]
        attempts.append(attempt)
        if attempt["success"]:
            return {
                "success": True,
                "element_id": element_id,
                "target_element_id": target_id,
                "click_target": target,
                "activation_method": attempt["method"],
                "attempts": attempts,
            }

    return {
        "success": False,
        "error": "No activation strategy produced an observable effect",
        "element_id": element_id,
        "target_element_id": target_id,
        "click_target": target,
        "attempts": attempts,
    }


def click_at(x: int, y: int, button: str = "left") -> JsonDict:
    point_match = accessibility.element_at_point(x=x, y=y, include_click_target=True)
    target_id = accessibility._safe_call(lambda: point_match["match"]["click_target"]["target_id"])
    before = _effect_context(target_id) if target_id else _effect_context()
    result = input.perform_mouse_click(x, y, button=button)
    after = _effect_context(target_id) if target_id else _effect_context()
    verified, verification = _verify_effect(before, after)
    result["point_target"] = point_match.get("match")
    return _apply_interaction_result(
        result,
        input_injected=bool(result.get("success")),
        effect_verified=verified,
        verification=verification,
    )
