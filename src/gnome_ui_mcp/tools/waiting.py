"""Waiting and assertion tools."""

from __future__ import annotations

from ..adapters import waiting
from ..desktop.types import ElementFilter
from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory
from .tool_definition import ToolRequest, define_tool

# -- wait_for_element --


def _wait_for_element(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    query = request.params.get("query", "")
    app_name = request.params.get("app_name", None)
    role = request.params.get("role", None)
    timeout_ms = request.params.get("timeout_ms", 5000)
    poll_interval_ms = request.params.get("poll_interval_ms", 250)
    showing_only = request.params.get("showing_only", True)
    clickable_only = request.params.get("clickable_only", False)
    bounds_only = request.params.get("bounds_only", False)
    within_element_id = request.params.get("within_element_id", None)
    within_popup = request.params.get("within_popup", False)
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
    result = waiting.wait_for_element(
        filt, timeout_ms=timeout_ms, poll_interval_ms=poll_interval_ms
    )
    response.set_data("element", result.element)
    response.append_text(f"Element matching '{query}' appeared.")


wait_for_element = define_tool(
    name="wait_for_element",
    description=(
        "Poll the accessibility tree until a matching element appears or "
        "the timeout expires, optionally scoped to a subtree or visible popup."
    ),
    handler=_wait_for_element,
    category=ToolCategory.WAITING,
    parameters={
        "query": {"type": "string", "description": "Text to search for in element names."},
        "app_name": {
            "type": "string",
            "default": None,
            "description": "Restrict search to this application.",
        },
        "role": {
            "type": "string",
            "default": None,
            "description": "Only match elements with this role.",
        },
        "timeout_ms": {
            "type": "integer",
            "default": 5000,
            "description": "Maximum time to wait in milliseconds.",
        },
        "poll_interval_ms": {
            "type": "integer",
            "default": 250,
            "description": "Polling interval in milliseconds.",
        },
        "showing_only": {
            "type": "boolean",
            "default": True,
            "description": "Only match elements that are currently showing.",
        },
        "clickable_only": {
            "type": "boolean",
            "default": False,
            "description": "Only match elements that are directly clickable.",
        },
        "bounds_only": {
            "type": "boolean",
            "default": False,
            "description": "Only match elements that have screen bounds.",
        },
        "within_element_id": {
            "type": "string",
            "default": None,
            "description": "Scope search to children of this element.",
        },
        "within_popup": {
            "type": "boolean",
            "default": False,
            "description": "Scope search to the currently visible popup.",
        },
    },
)


# -- wait_for_element_gone --


def _wait_for_element_gone(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    query = request.params.get("query", "")
    app_name = request.params.get("app_name", None)
    role = request.params.get("role", None)
    timeout_ms = request.params.get("timeout_ms", 5000)
    poll_interval_ms = request.params.get("poll_interval_ms", 250)
    showing_only = request.params.get("showing_only", True)
    clickable_only = request.params.get("clickable_only", False)
    bounds_only = request.params.get("bounds_only", False)
    within_element_id = request.params.get("within_element_id", None)
    within_popup = request.params.get("within_popup", False)
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
    waiting.wait_for_element_gone(filt, timeout_ms=timeout_ms, poll_interval_ms=poll_interval_ms)
    response.append_text(f"Element matching '{query}' disappeared.")


wait_for_element_gone = define_tool(
    name="wait_for_element_gone",
    description=(
        "Poll the accessibility tree until a matching element disappears or "
        "the timeout expires, optionally scoped to a subtree or visible popup."
    ),
    handler=_wait_for_element_gone,
    category=ToolCategory.WAITING,
    parameters={
        "query": {"type": "string", "description": "Text to search for in element names."},
        "app_name": {
            "type": "string",
            "default": None,
            "description": "Restrict search to this application.",
        },
        "role": {
            "type": "string",
            "default": None,
            "description": "Only match elements with this role.",
        },
        "timeout_ms": {
            "type": "integer",
            "default": 5000,
            "description": "Maximum time to wait in milliseconds.",
        },
        "poll_interval_ms": {
            "type": "integer",
            "default": 250,
            "description": "Polling interval in milliseconds.",
        },
        "showing_only": {
            "type": "boolean",
            "default": True,
            "description": "Only match elements that are currently showing.",
        },
        "clickable_only": {
            "type": "boolean",
            "default": False,
            "description": "Only match elements that are directly clickable.",
        },
        "bounds_only": {
            "type": "boolean",
            "default": False,
            "description": "Only match elements that have screen bounds.",
        },
        "within_element_id": {
            "type": "string",
            "default": None,
            "description": "Scope search to children of this element.",
        },
        "within_popup": {
            "type": "boolean",
            "default": False,
            "description": "Scope search to the currently visible popup.",
        },
    },
)


# -- wait_for_app --


def _wait_for_app(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    app_name = request.params.get("app_name", "")
    timeout_ms = request.params.get("timeout_ms", 10000)
    poll_interval_ms = request.params.get("poll_interval_ms", 250)
    require_window = request.params.get("require_window", True)
    result = waiting.wait_for_app(
        app_name=app_name,
        timeout_ms=timeout_ms,
        poll_interval_ms=poll_interval_ms,
        require_window=require_window,
    )
    response.set_data("app_id", result.app_id)
    response.set_data("waited_ms", result.waited_ms)
    response.set_data("windows", result.windows)
    response.append_text(f"Application '{app_name}' appeared.")


wait_for_app = define_tool(
    name="wait_for_app",
    description="Wait for an application to appear in the AT-SPI tree.",
    handler=_wait_for_app,
    category=ToolCategory.WAITING,
    parameters={
        "app_name": {"type": "string", "description": "Application name to wait for."},
        "timeout_ms": {
            "type": "integer",
            "default": 10000,
            "description": "Maximum time to wait in milliseconds.",
        },
        "poll_interval_ms": {
            "type": "integer",
            "default": 250,
            "description": "Polling interval in milliseconds.",
        },
        "require_window": {
            "type": "boolean",
            "default": True,
            "description": "Require at least one window to be open.",
        },
    },
)


# -- wait_for_window --


def _wait_for_window(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    query = request.params.get("query", "")
    app_name = request.params.get("app_name", None)
    role = request.params.get("role", None)
    timeout_ms = request.params.get("timeout_ms", 10000)
    poll_interval_ms = request.params.get("poll_interval_ms", 250)
    result = waiting.wait_for_window(
        query=query,
        app_name=app_name,
        role=role,
        timeout_ms=timeout_ms,
        poll_interval_ms=poll_interval_ms,
    )
    response.set_data("window", result.window)
    response.set_data("waited_ms", result.waited_ms)
    response.append_text(f"Window matching '{query}' appeared.")


wait_for_window = define_tool(
    name="wait_for_window",
    description="Wait for a window to appear.",
    handler=_wait_for_window,
    category=ToolCategory.WAITING,
    parameters={
        "query": {"type": "string", "description": "Window title text to match."},
        "app_name": {
            "type": "string",
            "default": None,
            "description": "Restrict search to this application.",
        },
        "role": {
            "type": "string",
            "default": None,
            "description": "Only match windows with this role.",
        },
        "timeout_ms": {
            "type": "integer",
            "default": 10000,
            "description": "Maximum time to wait in milliseconds.",
        },
        "poll_interval_ms": {
            "type": "integer",
            "default": 250,
            "description": "Polling interval in milliseconds.",
        },
    },
)


# -- wait_for_popup_count --


def _wait_for_popup_count(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    count = request.params.get("count", 0)
    timeout_ms = request.params.get("timeout_ms", 5000)
    poll_interval_ms = request.params.get("poll_interval_ms", 100)
    max_depth = request.params.get("max_depth", 10)
    result = waiting.wait_for_popup_count(
        count=count,
        timeout_ms=timeout_ms,
        poll_interval_ms=poll_interval_ms,
        max_depth=max_depth,
    )
    response.set_data("count", result.count)
    response.set_data("popups", result.popups)
    response.append_text(f"Popup count reached {count}.")


wait_for_popup_count = define_tool(
    name="wait_for_popup_count",
    description=("Poll the GNOME Shell until the number of visible popups matches a count."),
    handler=_wait_for_popup_count,
    category=ToolCategory.WAITING,
    parameters={
        "count": {"type": "integer", "description": "Expected number of popups."},
        "timeout_ms": {
            "type": "integer",
            "default": 5000,
            "description": "Maximum time to wait in milliseconds.",
        },
        "poll_interval_ms": {
            "type": "integer",
            "default": 100,
            "description": "Polling interval in milliseconds.",
        },
        "max_depth": {
            "type": "integer",
            "default": 10,
            "description": "Maximum tree depth to search for popups.",
        },
    },
)


# -- wait_for_shell_settled --


def _wait_for_shell_settled(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    timeout_ms = request.params.get("timeout_ms", 1500)
    stable_for_ms = request.params.get("stable_for_ms", 250)
    poll_interval_ms = request.params.get("poll_interval_ms", 50)
    max_depth = request.params.get("max_depth", 10)
    result = waiting.wait_for_shell_settled(
        timeout_ms=timeout_ms,
        stable_for_ms=stable_for_ms,
        poll_interval_ms=poll_interval_ms,
        max_depth=max_depth,
    )
    response.set_data("settled", result.settled)
    response.set_data("popup_count", result.popup_count)
    response.append_text("GNOME Shell has settled.")


wait_for_shell_settled = define_tool(
    name="wait_for_shell_settled",
    description=("Poll until GNOME Shell popup state has stayed unchanged for a short time."),
    handler=_wait_for_shell_settled,
    category=ToolCategory.WAITING,
    parameters={
        "timeout_ms": {
            "type": "integer",
            "default": 1500,
            "description": "Maximum time to wait in milliseconds.",
        },
        "stable_for_ms": {
            "type": "integer",
            "default": 250,
            "description": "How long shell must be stable.",
        },
        "poll_interval_ms": {
            "type": "integer",
            "default": 50,
            "description": "Polling interval in milliseconds.",
        },
        "max_depth": {
            "type": "integer",
            "default": 10,
            "description": "Maximum tree depth for popup detection.",
        },
    },
)


# -- wait_and_act --


def _wait_and_act(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    wait_query = request.params.get("wait_query", "")
    wait_role = request.params.get("wait_role", None)
    wait_app_name = request.params.get("wait_app_name", None)
    then_action = request.params.get("then_action", "activate")
    then_query = request.params.get("then_query", None)
    then_role = request.params.get("then_role", None)
    then_text = request.params.get("then_text", None)
    timeout_ms = request.params.get("timeout_ms", 5000)
    poll_interval_ms = request.params.get("poll_interval_ms", 250)
    result = waiting.wait_and_act(
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
    response.set_data("waited_ms", result.waited_ms)
    response.set_data("wait_match", result.wait_match)
    response.set_data("action_result", result.action_result)
    response.append_text(f"Waited for '{wait_query}' then performed '{then_action}'.")


wait_and_act = define_tool(
    name="wait_and_act",
    description=("Wait for an element to appear, then act on it. Atomic wait+act in one MCP call."),
    handler=_wait_and_act,
    category=ToolCategory.WAITING,
    read_only=False,
    parameters={
        "wait_query": {
            "type": "string",
            "description": "Text to wait for in element names.",
        },
        "wait_role": {
            "type": "string",
            "default": None,
            "description": "Role filter for the wait phase.",
        },
        "wait_app_name": {
            "type": "string",
            "default": None,
            "description": "Application filter for the wait phase.",
        },
        "then_action": {
            "type": "string",
            "default": "activate",
            "description": "Action to perform: activate, click, focus, or set_text.",
        },
        "then_query": {
            "type": "string",
            "default": None,
            "description": "Override query for the action target.",
        },
        "then_role": {
            "type": "string",
            "default": None,
            "description": "Override role for the action target.",
        },
        "then_text": {
            "type": "string",
            "default": None,
            "description": "Text to set (for set_text action).",
        },
        "timeout_ms": {
            "type": "integer",
            "default": 5000,
            "description": "Maximum time to wait in milliseconds.",
        },
        "poll_interval_ms": {
            "type": "integer",
            "default": 250,
            "description": "Polling interval in milliseconds.",
        },
    },
)


# -- assert_element --


def _assert_element(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    query = request.params.get("query", "")
    app_name = request.params.get("app_name", None)
    role = request.params.get("role", None)
    expected_states = request.params.get("expected_states", None)
    unexpected_states = request.params.get("unexpected_states", None)
    timeout_ms = request.params.get("timeout_ms", 3000)
    result = waiting.assert_element(
        query=query,
        app_name=app_name,
        role=role,
        expected_states=expected_states,
        unexpected_states=unexpected_states,
        timeout_ms=timeout_ms,
    )
    response.set_data("passed", result.passed)
    response.set_data("checks", result.checks)
    response.set_data("element", result.element)
    response.append_text(f"Assertion {'passed' if result.passed else 'failed'} for '{query}'.")


assert_element = define_tool(
    name="assert_element",
    description=(
        "Assert that an element exists with expected states. "
        "Returns pass/fail with structured checks."
    ),
    handler=_assert_element,
    category=ToolCategory.WAITING,
    parameters={
        "query": {"type": "string", "description": "Text to search for."},
        "app_name": {
            "type": "string",
            "default": None,
            "description": "Restrict search to this application.",
        },
        "role": {
            "type": "string",
            "default": None,
            "description": "Expected element role.",
        },
        "expected_states": {
            "type": "array",
            "items_type": "string",
            "default": None,
            "description": "States the element should have.",
        },
        "unexpected_states": {
            "type": "array",
            "items_type": "string",
            "default": None,
            "description": "States the element should not have.",
        },
        "timeout_ms": {
            "type": "integer",
            "default": 3000,
            "description": "Maximum time to wait for element to appear.",
        },
    },
)


# -- assert_text --


def _assert_text(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    expected = request.params.get("expected", "")
    match = request.params.get("match", "contains")
    result = waiting.assert_text(
        element_id=element_id,
        expected=expected,
        match=match,
    )
    response.set_data("passed", result.passed)
    response.set_data("actual", result.actual)
    response.set_data("expected", result.expected)
    response.set_data("match", result.match)
    status = "passed" if result.passed else "failed"
    response.append_text(f"Text assertion {status} for {element_id}.")


assert_text = define_tool(
    name="assert_text",
    description="Assert that an element's text matches expected value.",
    handler=_assert_text,
    category=ToolCategory.WAITING,
    parameters={
        "element_id": {
            "type": "string",
            "description": "Element ID to check text of.",
        },
        "expected": {
            "type": "string",
            "description": "Expected text value.",
        },
        "match": {
            "type": "string",
            "default": "contains",
            "description": "Match mode: exact, contains, startswith, or regex.",
        },
    },
)
