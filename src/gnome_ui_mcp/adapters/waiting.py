"""Waiting and assertion operations.

Wraps desktop accessibility, app_wait, assertions, and wait_act modules.
Returns typed data and raises exceptions on failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..desktop import accessibility as _desktop_accessibility
from ..desktop import app_wait as _desktop_app_wait
from ..desktop import assertions as _desktop_assertions
from ..desktop import wait_act as _desktop_wait_act
from ..desktop.types import ElementFilter


def _require(result: dict) -> dict:
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Operation failed")))
    return result


# -- dataclasses --


@dataclass
class WaitForElementResult:
    element: dict


@dataclass
class WaitForAppResult:
    app_id: str
    waited_ms: int
    windows: list[dict]


@dataclass
class WaitForWindowResult:
    window: dict
    waited_ms: int


@dataclass
class WaitForPopupCountResult:
    count: int
    popups: list[dict]


@dataclass
class ShellSettledResult:
    settled: bool
    popup_count: int


@dataclass
class WaitAndActResult:
    waited_ms: int
    wait_match: dict
    action_result: dict


@dataclass
class AssertElementResult:
    passed: bool
    checks: list[dict]
    element: dict | None


@dataclass
class AssertTextResult:
    passed: bool
    actual: str | None
    expected: str
    match: str


# -- public API --


def wait_for_element(
    filt: ElementFilter,
    timeout_ms: int = 5000,
    poll_interval_ms: int = 250,
) -> WaitForElementResult:
    """Wait for an element to appear. Raises on failure/timeout."""
    result = _require(
        _desktop_accessibility.wait_for_element(
            filt,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
        )
    )
    return WaitForElementResult(element=result.get("element", result))


def wait_for_element_gone(
    filt: ElementFilter,
    timeout_ms: int = 5000,
    poll_interval_ms: int = 250,
) -> None:
    """Wait for an element to disappear. Raises on failure/timeout."""
    _require(
        _desktop_accessibility.wait_for_element_gone(
            filt,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
        )
    )


def wait_for_app(
    app_name: str,
    timeout_ms: int = 10000,
    poll_interval_ms: int = 250,
    require_window: bool = True,
) -> WaitForAppResult:
    """Wait for an application to appear. Raises on failure/timeout."""
    result = _require(
        _desktop_app_wait.wait_for_app(
            app_name=app_name,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
            require_window=require_window,
        )
    )
    return WaitForAppResult(
        app_id=result.get("app_id", ""),
        waited_ms=result.get("waited_ms", 0),
        windows=result.get("windows", []),
    )


def wait_for_window(
    query: str,
    app_name: str | None = None,
    role: str | None = None,
    timeout_ms: int = 10000,
    poll_interval_ms: int = 250,
) -> WaitForWindowResult:
    """Wait for a window to appear. Raises on failure/timeout."""
    result = _require(
        _desktop_app_wait.wait_for_window(
            query=query,
            app_name=app_name,
            role=role,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
        )
    )
    return WaitForWindowResult(
        window=result.get("window", {}),
        waited_ms=result.get("waited_ms", 0),
    )


def wait_for_popup_count(
    count: int,
    timeout_ms: int = 5000,
    poll_interval_ms: int = 100,
    max_depth: int = 10,
) -> WaitForPopupCountResult:
    """Wait for popup count to match. Raises on failure/timeout."""
    result = _require(
        _desktop_accessibility.wait_for_popup_count(
            count=count,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
            max_depth=max_depth,
        )
    )
    return WaitForPopupCountResult(
        count=count,
        popups=result.get("popups", []),
    )


def wait_for_shell_settled(
    timeout_ms: int = 1500,
    stable_for_ms: int = 250,
    poll_interval_ms: int = 50,
    max_depth: int = 10,
) -> ShellSettledResult:
    """Wait for GNOME Shell to settle. Raises on failure."""
    result = _require(
        _desktop_accessibility.wait_for_shell_settled(
            timeout_ms=timeout_ms,
            stable_for_ms=stable_for_ms,
            poll_interval_ms=poll_interval_ms,
            max_depth=max_depth,
        )
    )
    return ShellSettledResult(
        settled=result.get("success", True),
        popup_count=result.get("popup_count", 0),
    )


def wait_and_act(
    wait_query: str,
    wait_role: str | None = None,
    wait_app_name: str | None = None,
    then_action: str = "activate",
    then_query: str | None = None,
    then_role: str | None = None,
    then_text: str | None = None,
    timeout_ms: int = 5000,
    poll_interval_ms: int = 250,
) -> WaitAndActResult:
    """Wait for element, then act. Raises on failure."""
    result = _require(
        _desktop_wait_act.wait_and_act(
            wait_query=wait_query,
            wait_role=wait_role,
            wait_app_name=wait_app_name,
            then_action=then_action,
            then_query=then_query,
            then_role=then_role,
            then_text=then_text,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
        )
    )
    return WaitAndActResult(
        waited_ms=result.get("waited_ms", 0),
        wait_match=result.get("wait_match", {}),
        action_result=result.get("action_result", {}),
    )


def assert_element(
    query: str,
    app_name: str | None = None,
    role: str | None = None,
    expected_states: list[str] | None = None,
    unexpected_states: list[str] | None = None,
    timeout_ms: int = 3000,
) -> AssertElementResult:
    """Assert element exists with states. Raises on v1 failure."""
    result = _require(
        _desktop_assertions.assert_element(
            query=query,
            app_name=app_name,
            role=role,
            expected_states=expected_states,
            unexpected_states=unexpected_states,
            timeout_ms=timeout_ms,
        )
    )
    return AssertElementResult(
        passed=result.get("passed", False),
        checks=result.get("checks", []),
        element=result.get("element"),
    )


def assert_text(
    element_id: str,
    expected: str,
    match: str = "contains",
) -> AssertTextResult:
    """Assert element text matches expected. Raises on v1 failure."""
    result = _require(
        _desktop_assertions.assert_text(
            element_id=element_id,
            expected=expected,
            match=match,
        )
    )
    return AssertTextResult(
        passed=result.get("passed", False),
        actual=result.get("actual"),
        expected=expected,
        match=match,
    )
