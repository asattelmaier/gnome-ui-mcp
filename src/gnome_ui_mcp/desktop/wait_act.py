"""Wait-then-act composite helper (Item 9)."""

from __future__ import annotations

import time
from typing import Any

from . import accessibility, interaction

JsonDict = dict[str, Any]


def wait_and_act(
    wait_query: str,
    wait_role: str | None = None,
    wait_app_name: str | None = None,
    then_action: str = "activate",
    then_query: str | None = None,
    then_role: str | None = None,
    then_text: str | None = None,
    timeout_ms: int = 5_000,
    poll_interval_ms: int = 250,
) -> JsonDict:
    """Poll for an element and then perform an action on it (or a sibling).

    Supported *then_action* values:
    - ``"activate"`` -- call :func:`interaction.activate_element`
    - ``"click"``    -- call :func:`interaction.click_element`
    - ``"focus"``    -- call :func:`accessibility.focus_element`
    - ``"set_text"`` -- call :func:`accessibility.set_element_text` with *then_text*
    """
    start = time.monotonic()
    deadline = start + timeout_ms / 1000

    # --- wait phase ---
    wait_match: JsonDict | None = None
    while True:
        result = accessibility.find_elements(
            query=wait_query,
            app_name=wait_app_name,
            role=wait_role,
            showing_only=True,
            max_results=1,
        )
        matches = result.get("matches", [])
        if matches:
            wait_match = matches[0]
            break

        if time.monotonic() >= deadline:
            return {
                "success": False,
                "error": f"Timeout waiting for element matching {wait_query!r}",
                "waited_ms": _elapsed_ms(start),
            }

        time.sleep(max(0.02, poll_interval_ms / 1000))

    waited_ms = _elapsed_ms(start)

    # --- resolve action target ---
    target_id: str = str(wait_match["id"])
    if then_query is not None:
        then_result = accessibility.find_elements(
            query=then_query,
            app_name=wait_app_name,
            role=then_role,
            showing_only=True,
            max_results=1,
        )
        then_matches = then_result.get("matches", [])
        if then_matches:
            target_id = str(then_matches[0]["id"])
        else:
            return {
                "success": False,
                "error": f"Found wait element but then_query {then_query!r} matched nothing",
                "waited_ms": waited_ms,
                "wait_match": wait_match,
            }

    # --- act phase ---
    action_result = _dispatch_action(then_action, target_id, then_text)

    return {
        "success": action_result.get("success", False),
        "waited_ms": waited_ms,
        "wait_match": wait_match,
        "action_result": action_result,
    }


def _dispatch_action(action: str, element_id: str, text: str | None) -> JsonDict:
    if action == "activate":
        return interaction.activate_element(element_id)
    if action == "click":
        return interaction.click_element(element_id)
    if action == "focus":
        return accessibility.focus_element(element_id)
    if action == "set_text":
        return accessibility.set_element_text(element_id, text or "")
    return {"success": False, "error": f"Unknown action: {action!r}"}


def _elapsed_ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)
