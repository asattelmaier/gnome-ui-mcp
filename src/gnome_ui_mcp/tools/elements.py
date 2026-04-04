"""Element interaction and query tools."""

from __future__ import annotations

from ..adapters import elements
from ..desktop.types import ElementFilter
from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory
from .tool_definition import ToolRequest, define_tool

# -- focus_element --


def _focus_element(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    context.check_boundary(element_id)
    elements.focus_element(element_id=element_id)
    response.append_text(f"Focused element {element_id}.")


focus_element = define_tool(
    name="focus_element",
    description="Focus an element through the AT-SPI component interface.",
    handler=_focus_element,
    category=ToolCategory.ACCESSIBILITY,
    read_only=False,
    parameters={
        "element_id": {"type": "string", "description": "Element ID to focus."},
    },
)


# -- click_element --


def _click_element(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    action_name = request.params.get("action_name", None)
    click_count = request.params.get("click_count", 1)
    button = request.params.get("button", "left")
    context.check_boundary(element_id)
    result = elements.click_element(
        element_id=element_id,
        action_name=action_name,
        click_count=click_count,
        button=button,
    )
    context.record_action(
        "click_element",
        {"element_id": element_id, "action_name": action_name, "button": button},
    )
    response.set_element_result(
        element_id=result.element_id,
        method=result.method,
        input_injected=result.input_injected,
        effect_verified=result.effect_verified,
    )
    response.append_text(f"Clicked element {element_id}.")


click_element = define_tool(
    name="click_element",
    description=(
        "Click an element or its resolved clickable ancestor, and report "
        "input injection plus observable effect verification."
    ),
    handler=_click_element,
    category=ToolCategory.ACCESSIBILITY,
    read_only=False,
    parameters={
        "element_id": {"type": "string", "description": "Element ID to click."},
        "action_name": {
            "type": "string",
            "default": None,
            "description": "Specific AT-SPI action to invoke.",
        },
        "click_count": {
            "type": "integer",
            "default": 1,
            "description": "Number of clicks (1=single, 2=double, 3=triple).",
        },
        "button": {
            "type": "string",
            "default": "left",
            "description": "Mouse button: left, middle, or right.",
        },
    },
)


# -- activate_element --


def _activate_element(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    action_name = request.params.get("action_name", None)
    context.check_boundary(element_id)
    result = elements.activate_element(element_id=element_id, action_name=action_name)
    context.record_action(
        "activate_element",
        {"element_id": element_id, "action_name": action_name},
    )
    response.set_result(result)
    response.append_text(f"Activated element {element_id}.")


activate_element = define_tool(
    name="activate_element",
    description=(
        "Activate an element with action first, then focus plus keyboard, then mouse fallback."
    ),
    handler=_activate_element,
    category=ToolCategory.ACCESSIBILITY,
    read_only=False,
    parameters={
        "element_id": {"type": "string", "description": "Element ID to activate."},
        "action_name": {
            "type": "string",
            "default": None,
            "description": "Specific AT-SPI action to invoke.",
        },
    },
)


# -- find_and_activate --


def _find_and_activate(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    query = request.params.get("query", "")
    app_name = request.params.get("app_name", None)
    role = request.params.get("role", None)
    max_depth = request.params.get("max_depth", 8)
    showing_only = request.params.get("showing_only", True)
    clickable_only = request.params.get("clickable_only", False)
    bounds_only = request.params.get("bounds_only", False)
    within_element_id = request.params.get("within_element_id", None)
    within_popup = request.params.get("within_popup", False)
    action_name = request.params.get("action_name", None)
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
    result = elements.find_and_activate(filt, max_depth=max_depth, action_name=action_name)
    response.set_result(result)
    response.append_text(f"Found and activated element matching '{query}'.")


find_and_activate = define_tool(
    name="find_and_activate",
    description=(
        "Find the best matching element and activate it, optionally scoped "
        "to a subtree or visible popup."
    ),
    handler=_find_and_activate,
    category=ToolCategory.ACCESSIBILITY,
    read_only=False,
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
            "description": "Only match elements with this role.",
        },
        "max_depth": {
            "type": "integer",
            "default": 8,
            "description": "Maximum tree depth to search.",
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
        "action_name": {
            "type": "string",
            "default": None,
            "description": "Specific AT-SPI action to invoke.",
        },
    },
)


# -- hover_element --


def _hover_element(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    context.check_boundary(element_id)
    elements.hover_element(element_id=element_id)
    response.append_text(f"Hovering over element {element_id}.")


hover_element = define_tool(
    name="hover_element",
    description="Move cursor to an element's center without clicking.",
    handler=_hover_element,
    category=ToolCategory.ACCESSIBILITY,
    read_only=False,
    parameters={
        "element_id": {"type": "string", "description": "Element ID to hover over."},
    },
)


# -- resolve_click_target --


def _resolve_click_target(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    result = elements.resolve_click_target(element_id=element_id)
    response.set_data("element_id", result.element_id)
    response.set_data("resolved_element_id", result.resolved_element_id)
    response.set_data("click_target", result.click_target)
    response.append_text(f"Resolved click target for {element_id}.")


resolve_click_target = define_tool(
    name="resolve_click_target",
    description=(
        "Resolve the nearest actionable ancestor for an element so labels "
        "can map to clickable parents."
    ),
    handler=_resolve_click_target,
    category=ToolCategory.ACCESSIBILITY,
    parameters={
        "element_id": {
            "type": "string",
            "description": "Element ID to resolve click target for.",
        },
    },
)


# -- set_element_text --


def _set_element_text(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    text = request.params.get("text", "")
    context.check_boundary(element_id)
    elements.set_element_text(element_id=element_id, text=text)
    context.record_action("set_element_text", {"element_id": element_id, "text": text})
    response.append_text(f"Set text of element {element_id}.")


set_element_text = define_tool(
    name="set_element_text",
    description="Replace the text contents of an editable element.",
    handler=_set_element_text,
    category=ToolCategory.ACCESSIBILITY,
    read_only=False,
    parameters={
        "element_id": {"type": "string", "description": "Element ID to set text on."},
        "text": {"type": "string", "description": "New text content."},
    },
)


# -- select_element_text --


def _select_element_text(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    start_offset = request.params.get("start_offset", None)
    end_offset = request.params.get("end_offset", None)
    elements.select_element_text(
        element_id=element_id,
        start_offset=start_offset,
        end_offset=end_offset,
    )
    response.append_text(f"Selected text in element {element_id}.")


select_element_text = define_tool(
    name="select_element_text",
    description=(
        "Select text within an element using the AT-SPI Text interface. "
        "Provide start_offset and end_offset for a range, or omit both to select all text."
    ),
    handler=_select_element_text,
    category=ToolCategory.ACCESSIBILITY,
    read_only=False,
    parameters={
        "element_id": {
            "type": "string",
            "description": "Element ID containing text.",
        },
        "start_offset": {
            "type": "integer",
            "default": None,
            "description": "Start offset for text selection.",
        },
        "end_offset": {
            "type": "integer",
            "default": None,
            "description": "End offset for text selection.",
        },
    },
)


# -- set_element_value --


def _set_element_value(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    value = request.params.get("value", 0.0)
    context.check_boundary(element_id)
    elements.set_element_value(element_id=element_id, value=value)
    context.record_action("set_element_value", {"element_id": element_id, "value": value})
    response.append_text(f"Set value of element {element_id} to {value}.")


set_element_value = define_tool(
    name="set_element_value",
    description=(
        "Set the numeric value of a slider, spinbutton, or progress bar "
        "via the AT-SPI Value interface."
    ),
    handler=_set_element_value,
    category=ToolCategory.ACCESSIBILITY,
    read_only=False,
    parameters={
        "element_id": {
            "type": "string",
            "description": "Element ID to set value on.",
        },
        "value": {
            "type": "number",
            "description": "Numeric value to set.",
        },
    },
)


# -- expand_node --


def _expand_node(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    context.check_boundary(element_id)
    elements.expand_node(element_id=element_id)
    response.append_text(f"Expanded node {element_id}.")


expand_node = define_tool(
    name="expand_node",
    description="Expand a tree or expander node if it is currently collapsed.",
    handler=_expand_node,
    category=ToolCategory.ACCESSIBILITY,
    read_only=False,
    parameters={
        "element_id": {"type": "string", "description": "Element ID to expand."},
    },
)


# -- collapse_node --


def _collapse_node(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    context.check_boundary(element_id)
    elements.collapse_node(element_id=element_id)
    response.append_text(f"Collapsed node {element_id}.")


collapse_node = define_tool(
    name="collapse_node",
    description="Collapse a tree or expander node if it is currently expanded.",
    handler=_collapse_node,
    category=ToolCategory.ACCESSIBILITY,
    read_only=False,
    parameters={
        "element_id": {"type": "string", "description": "Element ID to collapse."},
    },
)


# -- select_option --


def _select_option(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    child_index = request.params.get("child_index", 0)
    context.check_boundary(element_id)
    elements.select_option(element_id=element_id, child_index=child_index)
    response.append_text(f"Selected option at index {child_index} in element {element_id}.")


select_option = define_tool(
    name="select_option",
    description=(
        "Select a child item within a container element via the AT-SPI Selection "
        "interface. Use for combo boxes, list boxes, and menus."
    ),
    handler=_select_option,
    category=ToolCategory.ACCESSIBILITY,
    read_only=False,
    parameters={
        "element_id": {
            "type": "string",
            "description": "Container element ID.",
        },
        "child_index": {
            "type": "integer",
            "description": "Index of the child to select.",
        },
    },
)


# -- set_toggle_state --


def _set_toggle_state(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    desired_state = request.params.get("desired_state", True)
    context.check_boundary(element_id)
    elements.set_toggle_state(element_id=element_id, desired_state=desired_state)
    state_str = "on" if desired_state else "off"
    response.append_text(f"Set toggle {element_id} to {state_str}.")


set_toggle_state = define_tool(
    name="set_toggle_state",
    description=(
        "Set a toggle button or checkbox to a desired on/off state. "
        "Returns no-op if already in the desired state."
    ),
    handler=_set_toggle_state,
    category=ToolCategory.ACCESSIBILITY,
    read_only=False,
    parameters={
        "element_id": {
            "type": "string",
            "description": "Toggle element ID.",
        },
        "desired_state": {
            "type": "boolean",
            "description": "Desired state: true for on, false for off.",
        },
    },
)


# -- navigate_menu --


def _navigate_menu(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    menu_path = request.params.get("menu_path", None)
    app_name = request.params.get("app_name", None)
    if menu_path is None:
        menu_path = []
    result = elements.navigate_menu(menu_path=menu_path, app_name=app_name)
    response.set_data("menu_path", result.menu_path)
    response.set_data("activated_count", len(result.activated_items))
    response.append_text(f"Navigated menu path: {' > '.join(menu_path)}.")


navigate_menu = define_tool(
    name="navigate_menu",
    description=(
        "Navigate a menu hierarchy by sequentially activating each item in the path. "
        "Waits for sub-menus to appear between levels."
    ),
    handler=_navigate_menu,
    category=ToolCategory.ACCESSIBILITY,
    read_only=False,
    parameters={
        "menu_path": {
            "type": "array",
            "items_type": "string",
            "description": "List of menu item names to navigate through.",
        },
        "app_name": {
            "type": "string",
            "default": None,
            "description": "Application to search menus in.",
        },
    },
)


# -- get_focused_element --


def _get_focused_element(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    result = elements.get_focused_element()
    name = result.get("name", "unknown")
    role = result.get("role", "")
    element_id = result.get("id", "")
    response.set_data("name", name)
    response.set_data("role", role)
    response.set_data("element_id", element_id)
    for k in ("states", "application", "bounds", "editable"):
        if k in result:
            response.set_data(k, result[k])
    response.append_text(f"Focused element: {name}.")


get_focused_element = define_tool(
    name="get_focused_element",
    description="Return metadata about the currently focused element.",
    handler=_get_focused_element,
    category=ToolCategory.ACCESSIBILITY,
)


# -- get_element_properties --


def _get_element_properties(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    result = elements.get_element_properties(element_id=element_id)
    for k, v in result.items():
        if k != "success":
            response.set_data(k, v)
    response.append_text(f"Properties for element {element_id}.")


get_element_properties = define_tool(
    name="get_element_properties",
    description=(
        "Return extended AT-SPI properties for an element: value, selection, "
        "relations, attributes, and image info."
    ),
    handler=_get_element_properties,
    category=ToolCategory.ACCESSIBILITY,
    parameters={
        "element_id": {
            "type": "string",
            "description": "Element ID to get properties for.",
        },
    },
)


# -- get_element_text --


def _get_element_text(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    result = elements.get_element_text(element_id=element_id)
    for k, v in result.items():
        if k != "success":
            response.set_data(k, v)
    response.append_text(f"Text for element {element_id}.")


get_element_text = define_tool(
    name="get_element_text",
    description=(
        "Return detailed text information for an element: full text, caret offset, "
        "selections, and text attributes at the caret position."
    ),
    handler=_get_element_text,
    category=ToolCategory.ACCESSIBILITY,
    parameters={
        "element_id": {
            "type": "string",
            "description": "Element ID to get text from.",
        },
    },
)


# -- get_table_info --


def _get_table_info(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    result = elements.get_table_info(element_id=element_id)
    for k, v in result.items():
        if k != "success":
            response.set_data(k, v)
    response.append_text(f"Table info for element {element_id}.")


get_table_info = define_tool(
    name="get_table_info",
    description="Return table dimensions, column headers, and caption for a table element.",
    handler=_get_table_info,
    category=ToolCategory.ACCESSIBILITY,
    parameters={
        "element_id": {
            "type": "string",
            "description": "Table element ID.",
        },
    },
)


# -- get_table_cell --


def _get_table_cell(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    row = request.params.get("row", 0)
    col = request.params.get("col", 0)
    result = elements.get_table_cell(element_id=element_id, row=row, col=col)
    for k, v in result.items():
        if k != "success":
            response.set_data(k, v)
    response.append_text(f"Cell ({row}, {col}) of table {element_id}.")


get_table_cell = define_tool(
    name="get_table_cell",
    description="Return information about a specific cell in a table element.",
    handler=_get_table_cell,
    category=ToolCategory.ACCESSIBILITY,
    parameters={
        "element_id": {"type": "string", "description": "Table element ID."},
        "row": {"type": "integer", "description": "Row index."},
        "col": {"type": "integer", "description": "Column index."},
    },
)


# -- get_element_path --


def _get_element_path(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    result = elements.get_element_path(element_id=element_id)
    path = result.get("path", [])
    response.set_data("element_id", element_id)
    response.set_data("path", path)
    response.append_text(f"Path for element {element_id}.")


get_element_path = define_tool(
    name="get_element_path",
    description=("Return the ancestry chain from root to a given element as a list of nodes."),
    handler=_get_element_path,
    category=ToolCategory.ACCESSIBILITY,
    parameters={
        "element_id": {"type": "string", "description": "Element ID to trace path for."},
    },
)


# -- get_elements_by_ids --


def _get_elements_by_ids(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_ids = request.params.get("element_ids", None)
    if element_ids is None:
        element_ids = []
    result = elements.get_elements_by_ids(element_ids=element_ids)
    found = result.get("elements", [])
    missing = result.get("missing", [])
    response.set_items("elements", found)
    response.set_data("missing", missing)
    response.append_text(f"Resolved {len(found)} of {len(element_ids)} elements.")


get_elements_by_ids = define_tool(
    name="get_elements_by_ids",
    description=(
        "Resolve multiple element IDs in one call, returning summaries for found "
        "elements and a list of missing IDs."
    ),
    handler=_get_elements_by_ids,
    category=ToolCategory.ACCESSIBILITY,
    parameters={
        "element_ids": {
            "type": "array",
            "items_type": "string",
            "description": "List of element IDs to resolve.",
        },
    },
)


# -- get_tooltip_text --


def _get_tooltip_text(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    tooltip = elements.get_tooltip_text(element_id=element_id)
    response.set_data("element_id", element_id)
    response.set_data("tooltip_text", tooltip)
    response.append_text(f"Tooltip for {element_id}: {tooltip}")


get_tooltip_text = define_tool(
    name="get_tooltip_text",
    description=(
        "Get the tooltip text for an element. Checks the element's description first, "
        "then looks for tooltip relations in the AT-SPI tree."
    ),
    handler=_get_tooltip_text,
    category=ToolCategory.ACCESSIBILITY,
    parameters={
        "element_id": {
            "type": "string",
            "description": "Element ID to get tooltip from.",
        },
    },
)


# -- element_at_point --


def _element_at_point(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    x = request.params.get("x", 0)
    y = request.params.get("y", 0)
    app_name = request.params.get("app_name", None)
    max_depth = request.params.get("max_depth", 10)
    include_click_target = request.params.get("include_click_target", True)
    result = elements.element_at_point(
        x=x,
        y=y,
        app_name=app_name,
        max_depth=max_depth,
        include_click_target=include_click_target,
    )
    name = result.get("name", result.get("match", {}).get("name", "unknown"))
    for k, v in result.items():
        if k != "success":
            response.set_data(k, v)
    response.append_text(f"Element at ({x}, {y}): {name}.")


element_at_point = define_tool(
    name="element_at_point",
    description="Return the deepest visible element at a given screen coordinate.",
    handler=_element_at_point,
    category=ToolCategory.ACCESSIBILITY,
    parameters={
        "x": {"type": "integer", "description": "X screen coordinate."},
        "y": {"type": "integer", "description": "Y screen coordinate."},
        "app_name": {
            "type": "string",
            "default": None,
            "description": "Restrict search to this application.",
        },
        "max_depth": {
            "type": "integer",
            "default": 10,
            "description": "Maximum depth to search.",
        },
        "include_click_target": {
            "type": "boolean",
            "default": True,
            "description": "Include resolved click target in result.",
        },
    },
)


# -- scroll_to_element --


def _scroll_to_element(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    max_scrolls = request.params.get("max_scrolls", 20)
    scroll_clicks = request.params.get("scroll_clicks", 3)
    result = elements.scroll_to_element(
        element_id=element_id,
        max_scrolls=max_scrolls,
        scroll_clicks=scroll_clicks,
    )
    response.set_data("scrolls_performed", result.scrolls_performed)
    response.set_data("now_showing", result.now_showing)
    response.set_data("element_bounds", result.element_bounds)
    response.append_text(f"Scrolled element {element_id} into view.")


scroll_to_element = define_tool(
    name="scroll_to_element",
    description="Scroll an element into view if it is off-screen.",
    handler=_scroll_to_element,
    category=ToolCategory.ACCESSIBILITY,
    read_only=False,
    parameters={
        "element_id": {"type": "string", "description": "Element ID to scroll to."},
        "max_scrolls": {
            "type": "integer",
            "default": 20,
            "description": "Maximum number of scroll attempts.",
        },
        "scroll_clicks": {
            "type": "integer",
            "default": 3,
            "description": "Number of scroll clicks per attempt.",
        },
    },
)
