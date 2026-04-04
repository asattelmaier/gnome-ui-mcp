"""Discovery tools: list applications, windows, find elements, accessibility tree."""

from __future__ import annotations

from ..adapters import accessibility
from ..formatters.accessibility_formatter import (
    ApplicationListFormatter,
    WindowListFormatter,
)
from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory
from .tool_definition import ToolRequest, define_tool

# -- list_applications --


def _list_applications(request: ToolRequest, response: McpResponse, context: McpContext) -> None:
    apps = accessibility.list_applications()
    fmt = ApplicationListFormatter(apps)
    response.set_items("applications", fmt.to_json())
    response.append_text(fmt.to_string())


list_applications = define_tool(
    name="list_applications",
    description=("List applications currently visible through the AT-SPI desktop tree."),
    handler=_list_applications,
    category=ToolCategory.ACCESSIBILITY,
)


# -- list_windows --


def _list_windows(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    app_name = request.params.get("app_name", None)
    windows = accessibility.list_windows(app_name)
    fmt = WindowListFormatter(windows)
    response.set_items("windows", fmt.to_json())
    response.append_text(fmt.to_string())


list_windows = define_tool(
    name="list_windows",
    description=("List top-level windows across the desktop or for one application."),
    handler=_list_windows,
    category=ToolCategory.ACCESSIBILITY,
    parameters={
        "app_name": {
            "type": "string",
            "default": None,
            "description": "Filter windows by application name.",
        },
    },
)


# -- accessibility_tree --


def _accessibility_tree(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    from ..desktop.types import TreeOptions

    app_name = request.params.get("app_name", None)
    max_depth = request.params.get("max_depth", 4)
    include_actions = request.params.get("include_actions", False)
    include_text = request.params.get("include_text", False)
    filter_roles = request.params.get("filter_roles", None)
    filter_states = request.params.get("filter_states", None)
    showing_only = request.params.get("showing_only", False)

    opts = TreeOptions(
        max_depth=max_depth,
        include_actions=include_actions,
        include_text=include_text,
        filter_roles=filter_roles,
        filter_states=filter_states,
        showing_only=showing_only,
    )
    trees = accessibility.accessibility_tree(app_name=app_name, opts=opts)
    response.set_trees(trees)
    response.append_text(f"Returned {len(trees)} application trees.")


accessibility_tree = define_tool(
    name="accessibility_tree",
    description=(
        "Return the accessibility tree for the whole desktop or a "
        "specific application. Optionally filter by roles, states, "
        "or showing-only."
    ),
    handler=_accessibility_tree,
    category=ToolCategory.ACCESSIBILITY,
    parameters={
        "app_name": {
            "type": "string",
            "default": None,
            "description": "Only return the tree for this application.",
        },
        "max_depth": {
            "type": "integer",
            "default": 4,
            "description": "Maximum depth to traverse.",
        },
        "include_actions": {
            "type": "boolean",
            "default": False,
            "description": "Include available actions on each node.",
        },
        "include_text": {
            "type": "boolean",
            "default": False,
            "description": "Include text content of each node.",
        },
        "filter_roles": {
            "type": "array",
            "items_type": "string",
            "default": None,
            "description": "Only include nodes with these roles.",
        },
        "filter_states": {
            "type": "array",
            "items_type": "string",
            "default": None,
            "description": "Only include nodes that have all these states.",
        },
        "showing_only": {
            "type": "boolean",
            "default": False,
            "description": "Only include nodes that are currently showing.",
        },
    },
)


# -- find_elements --


def _find_elements(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    from ..desktop.types import ElementFilter

    query = request.params.get("query", "")
    app_name = request.params.get("app_name", None)
    role = request.params.get("role", None)
    max_depth = request.params.get("max_depth", 8)
    max_results = request.params.get("max_results", 20)
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
    matches = accessibility.find_elements(
        filt,
        max_depth=max_depth,
        max_results=max_results,
    )
    response.set_matches(matches)
    response.append_text(f"Found {len(matches)} elements.")


find_elements = define_tool(
    name="find_elements",
    description=(
        "Search accessible elements by text and optional role filter, "
        "with optional clickable and bounds filters, optionally scoped "
        "to a subtree or visible popup."
    ),
    handler=_find_elements,
    category=ToolCategory.ACCESSIBILITY,
    parameters={
        "query": {
            "type": "string",
            "default": "",
            "description": "Text to search for in element names and descriptions.",
        },
        "app_name": {
            "type": "string",
            "default": None,
            "description": "Restrict search to this application.",
        },
        "role": {
            "type": "string",
            "default": None,
            "description": ("Only return elements with this role (e.g. 'push button')."),
        },
        "max_depth": {
            "type": "integer",
            "default": 8,
            "description": "Maximum tree depth to search.",
        },
        "max_results": {
            "type": "integer",
            "default": 20,
            "description": "Maximum number of results to return.",
        },
        "showing_only": {
            "type": "boolean",
            "default": True,
            "description": "Only return elements that are currently showing.",
        },
        "clickable_only": {
            "type": "boolean",
            "default": False,
            "description": "Only return elements that are directly clickable.",
        },
        "bounds_only": {
            "type": "boolean",
            "default": False,
            "description": "Only return elements that have screen bounds.",
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
