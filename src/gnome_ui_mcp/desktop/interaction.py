from __future__ import annotations

import time
from typing import Any

from . import accessibility, input
from .locators import locator_for_element_id, relocate_from_locator

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
        for field_name in ("text", "bounds", "name", "subtree_fingerprint"):
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


def _settled_effect_context(
    element_id: str | None = None,
    *,
    settle_timeout_ms: int = 1_500,
    stable_for_ms: int = 250,
    poll_interval_ms: int = 50,
) -> tuple[JsonDict, JsonDict]:
    settled = accessibility.wait_for_shell_settled(
        timeout_ms=settle_timeout_ms,
        stable_for_ms=stable_for_ms,
        poll_interval_ms=poll_interval_ms,
    )
    return _effect_context(element_id), settled


def _verified_result_after_settle(
    result: JsonDict,
    *,
    before: JsonDict,
    element_id: str | None = None,
    input_injected: bool,
    settle_timeout_ms: int = 1_500,
    stable_for_ms: int = 250,
    poll_interval_ms: int = 50,
) -> JsonDict:
    after, settled = _settled_effect_context(
        element_id,
        settle_timeout_ms=settle_timeout_ms,
        stable_for_ms=stable_for_ms,
        poll_interval_ms=poll_interval_ms,
    )
    verified, verification = _verify_effect(before, after)
    verification["shell_settled"] = settled
    if not settled.get("success") and verified is not True:
        verified = False
        verification["reason"] = "shell_not_settled"

    return _apply_interaction_result(
        result,
        input_injected=input_injected,
        effect_verified=verified,
        verification=verification,
    )


def _activation_keys_for_role(role_name: str) -> list[str]:
    normalized = role_name.casefold()
    if "menu" in normalized:
        return ["space", "Return"]
    return ["Return", "space"]


def _focus_debug_summary(focus: JsonDict | None) -> JsonDict | None:
    if focus is None:
        return None

    return {
        "id": focus.get("id"),
        "name": focus.get("name"),
        "role": focus.get("role"),
        "application": focus.get("application"),
        "editable": bool(focus.get("editable")),
        "states": list(focus.get("states", [])),
    }


def _focus_verification_details(
    focus: JsonDict | None,
    *,
    target_id: str,
    target_app: str,
) -> JsonDict:
    if focus is None:
        return {
            "focus_verified": False,
            "focus_match": "none",
            "reason": "no_focused_element",
        }

    focused_id = str(focus.get("id", ""))
    focused_app = str(focus.get("application", ""))
    editable = bool(focus.get("editable"))

    if focused_id == target_id:
        return {
            "focus_verified": True,
            "focus_match": "element",
            "reason": "target_element_focused",
        }

    if target_app and focused_app == target_app and not editable:
        return {
            "focus_verified": True,
            "focus_match": "application",
            "reason": "target_application_focused",
        }

    if editable:
        reason = "focused_element_is_editable"
    elif target_app and focused_app and focused_app != target_app:
        reason = "focused_application_mismatch"
    else:
        reason = "target_not_focused"

    return {
        "focus_verified": False,
        "focus_match": "none",
        "reason": reason,
    }


def _wait_for_focus_verification(
    target_id: str,
    *,
    timeout_ms: int = 400,
    poll_interval_ms: int = 50,
) -> JsonDict:
    target_app = accessibility._application_name_for_element_id(target_id)
    deadline = time.monotonic() + timeout_ms / 1000
    last_focus = accessibility.current_focus_metadata()
    last_verification = _focus_verification_details(
        last_focus,
        target_id=target_id,
        target_app=target_app,
    )

    while True:
        focus = accessibility.current_focus_metadata()
        verification = _focus_verification_details(
            focus,
            target_id=target_id,
            target_app=target_app,
        )
        last_focus = focus
        last_verification = verification
        if verification["focus_verified"]:
            return {
                "success": True,
                "target_app": target_app,
                "current_focus": _focus_debug_summary(focus),
                **verification,
            }

        if time.monotonic() >= deadline:
            return {
                "success": False,
                "target_app": target_app,
                "current_focus": _focus_debug_summary(last_focus),
                **last_verification,
            }

        time.sleep(max(0.02, poll_interval_ms / 1000))


def _resolve_target_with_recovery(element_id: str) -> tuple[str, JsonDict, JsonDict | None]:
    last_error = ""

    try:
        target = accessibility._resolve_click_target_metadata(element_id)
        target_id = str(target["target_id"])
        accessible = accessibility._resolve_element(target_id)
        if accessibility._is_showing(accessible):
            return element_id, target, None
        last_error = "Element is not currently showing on screen"
    except Exception as exc:
        last_error = str(exc)

    locator = locator_for_element_id(element_id)
    if locator is None:
        raise ValueError(last_error or f"Element not found: {element_id}")

    relocated = relocate_from_locator(locator, max_results=1)
    if not relocated.get("success"):
        error = str(relocated.get("error", "Failed to relocate element"))
        if last_error:
            error = f"{last_error}; {error}"
        raise ValueError(error)

    match = relocated["match"]
    recovered_element_id = str(match["id"])
    target = match.get("click_target")
    if target is None:
        target = accessibility._resolve_click_target_metadata(recovered_element_id)

    target_id = str(target["target_id"])
    accessible = accessibility._resolve_element(target_id)
    if not accessibility._is_showing(accessible):
        raise ValueError("Recovered element is not currently showing on screen")

    return (
        recovered_element_id,
        target,
        {
            "used": True,
            "requested_element_id": element_id,
            "recovered_element_id": recovered_element_id,
            "locator": locator,
            "match": match,
        },
    )


def resolve_click_target(element_id: str) -> JsonDict:
    try:
        resolved_element_id, target, recovery = _resolve_target_with_recovery(element_id)
    except Exception as exc:
        return {"success": False, "error": str(exc), "element_id": element_id}

    result = {
        "success": True,
        "element_id": element_id,
        "resolved_element_id": resolved_element_id,
        "click_target": target,
    }
    if recovery is not None:
        result["recovery"] = recovery
    return result


def click_element(
    element_id: str, action_name: str | None = None, click_count: int = 1
) -> JsonDict:
    resolved_element_id, target, recovery = _resolve_target_with_recovery(element_id)
    target_id = str(target["target_id"])
    accessible = accessibility._resolve_element(target_id)

    before = _effect_context(target_id)
    action_index = (
        accessibility._find_action_index(accessible, action_name) if click_count == 1 else None
    )
    if action_index is not None:
        performed = accessible.do_action(action_index)
        result = {
            "method": "action",
            "element_id": element_id,
            "resolved_element_id": resolved_element_id,
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
        response = _apply_interaction_result(
            result,
            input_injected=bool(performed),
            effect_verified=verified,
            verification=verification,
        )
        if recovery is not None:
            response["recovery"] = recovery
        return response

    bounds = accessibility._element_bounds(accessible)
    center = accessibility._center(bounds)
    if center is None:
        return {
            "success": False,
            "error": "Element is neither actionable nor clickable by bounds",
        }

    result = input.perform_mouse_click(center[0], center[1], click_count=click_count)
    after = _effect_context(target_id)
    verified, verification = _verify_effect(before, after)
    result["element_id"] = element_id
    result["resolved_element_id"] = resolved_element_id
    result["target_element_id"] = target_id
    result["click_target"] = target
    result["method"] = "mouse"
    response = _apply_interaction_result(
        result,
        input_injected=bool(result.get("success")),
        effect_verified=verified,
        verification=verification,
    )
    if recovery is not None:
        response["recovery"] = recovery
    return response


def activate_element(element_id: str, action_name: str | None = None) -> JsonDict:
    try:
        resolved_element_id, target, recovery = _resolve_target_with_recovery(element_id)
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "element_id": element_id,
        }

    target_id = str(target["target_id"])
    accessible = accessibility._resolve_element(target_id)

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
                "resolved_element_id": resolved_element_id,
                "target_element_id": target_id,
                "click_target": target,
                "activation_method": attempt["method"],
                "attempts": attempts,
                "recovery": recovery,
            }
        current_before = current_after

    previous_focus = _focus_debug_summary(accessibility.current_focus_metadata())
    focus_checks: list[JsonDict] = []
    for _attempt_index in range(2):
        focus_result = accessibility.focus_element(target_id)
        focus_check = _wait_for_focus_verification(target_id)
        focus_checks.append(
            {
                "focus_requested": bool(focus_result.get("success")),
                "focus_verified": bool(focus_check.get("focus_verified")),
                "focus_match": focus_check.get("focus_match"),
                "reason": focus_check.get("reason"),
                "target_app": focus_check.get("target_app"),
                "current_focus": focus_check.get("current_focus"),
            }
        )
        if focus_result.get("success") and focus_check.get("focus_verified"):
            break
    else:
        focus_result = {"success": False}
        focus_check = focus_checks[-1] if focus_checks else {"focus_verified": False}

    if focus_result.get("success") and focus_check.get("focus_verified"):
        for key_name in _activation_keys_for_role(str(target["target_role"])):
            key_result = input.press_key(key_name)
            attempt = _verified_result_after_settle(
                {
                    "method": "focus+key",
                    "key_name": key_name,
                    "focus_element_id": target_id,
                    "backend": key_result.get("backend"),
                },
                input_injected=bool(key_result.get("success")),
                before=current_before,
                element_id=target_id,
            )
            attempt["focus_verified"] = bool(focus_check.get("focus_verified"))
            attempt["focus_match"] = focus_check.get("focus_match")
            attempt["previous_focus"] = previous_focus
            attempt["current_focus"] = focus_check.get("current_focus")
            attempt["focus_checks"] = list(focus_checks)
            if key_result.get("fallback_error"):
                attempt["fallback_error"] = key_result["fallback_error"]
            attempts.append(attempt)
            if attempt["success"]:
                return {
                    "success": True,
                    "element_id": element_id,
                    "resolved_element_id": resolved_element_id,
                    "target_element_id": target_id,
                    "click_target": target,
                    "activation_method": attempt["method"],
                    "attempts": attempts,
                    "recovery": recovery,
                }
            current_before = _effect_context(target_id)
    elif focus_checks:
        attempts.append(
            {
                "method": "focus+key",
                "key_name": None,
                "focus_element_id": target_id,
                "focus_verified": False,
                "focus_match": focus_checks[-1].get("focus_match"),
                "previous_focus": previous_focus,
                "current_focus": focus_checks[-1].get("current_focus"),
                "focus_checks": list(focus_checks),
                "input_injected": False,
                "effect_verified": False,
                "verification": {
                    "reason": "focus_not_verified",
                    "focus_checks": list(focus_checks),
                },
                "success": False,
            }
        )

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
                "resolved_element_id": resolved_element_id,
                "target_element_id": target_id,
                "click_target": target,
                "activation_method": attempt["method"],
                "attempts": attempts,
                "recovery": recovery,
            }

    return {
        "success": False,
        "error": "No activation strategy produced an observable effect",
        "element_id": element_id,
        "resolved_element_id": resolved_element_id,
        "target_element_id": target_id,
        "click_target": target,
        "attempts": attempts,
        "recovery": recovery,
    }


def find_and_activate(
    query: str,
    *,
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
    result = accessibility.find_elements(
        query=query,
        app_name=app_name,
        role=role,
        max_depth=max_depth,
        max_results=1,
        showing_only=showing_only,
        clickable_only=clickable_only,
        bounds_only=bounds_only,
        within_element_id=within_element_id,
        within_popup=within_popup,
    )
    matches = result.get("matches", [])
    if not matches:
        return {
            "success": False,
            "error": "No element matched query",
            "query": query,
            "app_name": app_name,
            "role": role,
            "within_element_id": within_element_id,
            "within_popup": within_popup,
        }

    match = matches[0]
    activation = activate_element(str(match["id"]), action_name=action_name)
    activation["match"] = match
    activation["locator"] = match.get("locator")
    return activation


def press_key(
    key_name: str,
    *,
    element_id: str | None = None,
    settle_timeout_ms: int = 1_500,
    stable_for_ms: int = 250,
    poll_interval_ms: int = 50,
) -> JsonDict:
    before = _effect_context(element_id)
    key_result = input.press_key(key_name)
    result = _verified_result_after_settle(
        {
            "method": "key",
            "key_name": key_name,
            "element_id": element_id,
            "backend": key_result.get("backend"),
        },
        before=before,
        element_id=element_id,
        input_injected=bool(key_result.get("success")),
        settle_timeout_ms=settle_timeout_ms,
        stable_for_ms=stable_for_ms,
        poll_interval_ms=poll_interval_ms,
    )
    if key_result.get("fallback_error"):
        result["fallback_error"] = key_result["fallback_error"]
    if "keyval" in key_result:
        result["keyval"] = key_result["keyval"]
    return result


def key_combo(
    combo: str,
    *,
    element_id: str | None = None,
    settle_timeout_ms: int = 1_500,
    stable_for_ms: int = 250,
    poll_interval_ms: int = 50,
) -> JsonDict:
    before = _effect_context(element_id)
    combo_result = input.key_combo(combo)
    result = _verified_result_after_settle(
        {
            "method": "key_combo",
            "combo": combo,
            "element_id": element_id,
            "backend": combo_result.get("backend"),
        },
        before=before,
        element_id=element_id,
        input_injected=bool(combo_result.get("success")),
        settle_timeout_ms=settle_timeout_ms,
        stable_for_ms=stable_for_ms,
        poll_interval_ms=poll_interval_ms,
    )
    if combo_result.get("fallback_error"):
        result["fallback_error"] = combo_result["fallback_error"]
    return result


def hover_element(element_id: str) -> JsonDict:
    try:
        accessible = accessibility._resolve_element(element_id)
    except Exception as exc:
        return {"success": False, "error": str(exc), "element_id": element_id}

    bounds = accessibility._element_bounds(accessible)
    center = accessibility._center(bounds)
    if center is None:
        return {
            "success": False,
            "error": "Element has no computable bounds for hover",
            "element_id": element_id,
        }

    move_result = input.perform_mouse_move(center[0], center[1])
    move_result["element_id"] = element_id
    move_result["x"] = center[0]
    move_result["y"] = center[1]
    move_result["bounds"] = bounds
    move_result["effect_verified"] = None
    return move_result


def click_at(x: int, y: int, button: str = "left", click_count: int = 1) -> JsonDict:
    point_match = accessibility.element_at_point(x=x, y=y, include_click_target=True)
    target_id = accessibility._safe_call(lambda: point_match["match"]["click_target"]["target_id"])
    before = _effect_context(target_id) if target_id else _effect_context()
    result = input.perform_mouse_click(x, y, button=button, click_count=click_count)
    after = _effect_context(target_id) if target_id else _effect_context()
    verified, verification = _verify_effect(before, after)
    result["point_target"] = point_match.get("match")
    return _apply_interaction_result(
        result,
        input_injected=bool(result.get("success")),
        effect_verified=verified,
        verification=verification,
    )
