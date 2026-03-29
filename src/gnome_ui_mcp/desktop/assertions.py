"""Element and text assertions (Item 11)."""

from __future__ import annotations

import re
import time
from typing import Any

from . import accessibility

JsonDict = dict[str, Any]


def assert_element(
    query: str,
    app_name: str | None = None,
    role: str | None = None,
    expected_states: list[str] | None = None,
    unexpected_states: list[str] | None = None,
    timeout_ms: int = 3_000,
    poll_interval_ms: int = 250,
) -> JsonDict:
    """Assert that an element matching *query* exists and satisfies state checks."""
    deadline = time.monotonic() + timeout_ms / 1000
    element: JsonDict | None = None

    while True:
        result = accessibility.find_elements(
            query=query,
            app_name=app_name,
            role=role,
            showing_only=True,
            max_results=1,
        )
        matches = result.get("matches", [])
        if matches:
            element = matches[0]
            break

        if time.monotonic() >= deadline:
            return {
                "passed": False,
                "checks": [{"check": "element_exists", "passed": False, "actual": None}],
                "element": None,
            }

        time.sleep(max(0.02, poll_interval_ms / 1000))

    # Run state checks
    checks: list[JsonDict] = [{"check": "element_exists", "passed": True, "actual": element["id"]}]
    actual_states: list[str] = list(element.get("states", []))
    all_passed = True

    for state in expected_states or []:
        present = state in actual_states
        checks.append(
            {"check": f"expected_state:{state}", "passed": present, "actual": actual_states}
        )
        if not present:
            all_passed = False

    for state in unexpected_states or []:
        absent = state not in actual_states
        checks.append(
            {"check": f"unexpected_state:{state}", "passed": absent, "actual": actual_states}
        )
        if not absent:
            all_passed = False

    return {"passed": all_passed, "checks": checks, "element": element}


def assert_text(
    element_id: str,
    expected: str,
    match: str = "contains",
) -> JsonDict:
    """Assert that an element's text matches *expected*.

    *match* can be ``"exact"``, ``"contains"``, ``"startswith"``, or ``"regex"``.
    """
    try:
        accessible = accessibility._resolve_element(element_id)
    except (ValueError, RuntimeError) as exc:
        return {
            "passed": False,
            "error": str(exc),
            "actual": None,
            "expected": expected,
            "match": match,
        }

    actual = accessibility._element_text_preview(accessible)
    if actual is None:
        return {
            "passed": False,
            "actual": None,
            "expected": expected,
            "match": match,
        }

    passed = _compare(actual, expected, match)
    return {
        "passed": passed,
        "actual": actual,
        "expected": expected,
        "match": match,
    }


def _compare(actual: str, expected: str, mode: str) -> bool:
    if mode == "exact":
        return actual == expected
    if mode == "contains":
        return expected in actual
    if mode == "startswith":
        return actual.startswith(expected)
    if mode == "regex":
        return re.search(expected, actual) is not None
    return False
