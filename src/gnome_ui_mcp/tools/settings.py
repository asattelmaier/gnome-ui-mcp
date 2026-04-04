"""Settings and system integration tools."""

from __future__ import annotations

from ..adapters import dbus as dbus_mod
from ..adapters import display as display_mod
from ..adapters import gsettings as gsettings_mod
from ..adapters import keyboard, monitor, wayland
from ..formatters.settings_formatter import (
    KeyboardLayoutFormatter,
    KeyListFormatter,
    MonitorFormatter,
    ProtocolListFormatter,
)
from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory
from .tool_definition import ToolRequest, define_tool

# -- gsettings_get --


def _gsettings_get(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    schema = request.params.get("schema", "")
    key = request.params.get("key", "")
    value = gsettings_mod.gsettings_get(schema=schema, key=key)
    response.set_data("schema", schema)
    response.set_data("key", key)
    response.set_data("value", value)
    response.append_text(f"{schema} {key} = {value}")


gsettings_get = define_tool(
    name="gsettings_get",
    description="Read a GSettings key value.",
    handler=_gsettings_get,
    category=ToolCategory.SETTINGS,
    parameters={
        "schema": {"type": "string", "description": "GSettings schema ID."},
        "key": {"type": "string", "description": "Key name within the schema."},
    },
)


# -- gsettings_set --


def _gsettings_set(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    schema = request.params.get("schema", "")
    key = request.params.get("key", "")
    value = request.params.get("value", "")
    gsettings_mod.gsettings_set(schema=schema, key=key, value=value)
    response.append_text(f"Set {schema} {key} = {value}")


gsettings_set = define_tool(
    name="gsettings_set",
    description="Write a GSettings key value.",
    handler=_gsettings_set,
    category=ToolCategory.SETTINGS,
    read_only=False,
    parameters={
        "schema": {"type": "string", "description": "GSettings schema ID."},
        "key": {"type": "string", "description": "Key name within the schema."},
        "value": {
            "type": ["string", "integer", "number", "boolean"],
            "description": "Value to set (string, number, or boolean).",
        },
    },
)


# -- gsettings_list_keys --


def _gsettings_list_keys(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    schema = request.params.get("schema", "")
    keys = gsettings_mod.gsettings_list_keys(schema=schema)
    response.set_data("schema", schema)
    response.set_items("keys", keys)
    response.append_text(f"Schema {schema}: {len(keys)} keys.")


gsettings_list_keys = define_tool(
    name="gsettings_list_keys",
    description="List all keys in a GSettings schema.",
    handler=_gsettings_list_keys,
    category=ToolCategory.SETTINGS,
    parameters={
        "schema": {"type": "string", "description": "GSettings schema ID."},
    },
)


# -- gsettings_reset --


def _gsettings_reset(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    schema = request.params.get("schema", "")
    key = request.params.get("key", "")
    gsettings_mod.gsettings_reset(schema=schema, key=key)
    response.append_text(f"Reset {schema} {key} to default.")


gsettings_reset = define_tool(
    name="gsettings_reset",
    description="Reset a GSettings key to its default value.",
    handler=_gsettings_reset,
    category=ToolCategory.SETTINGS,
    read_only=False,
    parameters={
        "schema": {"type": "string", "description": "GSettings schema ID."},
        "key": {"type": "string", "description": "Key name within the schema."},
    },
)


# -- dbus_call --


def _dbus_call(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    bus_name = request.params.get("bus_name", "")
    object_path = request.params.get("object_path", "")
    interface = request.params.get("interface", "")
    method = request.params.get("method", "")
    args = request.params.get("args", None)
    signature = request.params.get("signature", None)
    timeout_ms = request.params.get("timeout_ms", 5000)
    result = dbus_mod.dbus_call(
        bus_name=bus_name,
        object_path=object_path,
        interface=interface,
        method=method,
        args=args,
        signature=signature,
        timeout_ms=timeout_ms,
    )
    response.set_data("bus_name", result.bus_name)
    response.set_data("method", result.method)
    if result.value is not None:
        response.set_data("value", result.value)
    response.append_text(f"Called {bus_name} {method}.")


dbus_call = define_tool(
    name="dbus_call",
    description="Call any D-Bus method on the session bus. Use with caution.",
    handler=_dbus_call,
    category=ToolCategory.SETTINGS,
    read_only=False,
    parameters={
        "bus_name": {"type": "string", "description": "D-Bus bus name."},
        "object_path": {"type": "string", "description": "D-Bus object path."},
        "interface": {"type": "string", "description": "D-Bus interface name."},
        "method": {"type": "string", "description": "Method to call."},
        "args": {
            "type": "array",
            "items_type": "string",
            "default": None,
            "description": "Arguments to pass to the method.",
        },
        "signature": {
            "type": "string",
            "default": None,
            "description": "D-Bus type signature for the arguments.",
        },
        "timeout_ms": {
            "type": "integer",
            "default": 5000,
            "description": "Timeout in milliseconds.",
        },
    },
)


# -- list_monitors --


def _list_monitors(request: ToolRequest, response: McpResponse, context: McpContext) -> None:
    monitors = display_mod.list_monitors()
    response.set_items("monitors", monitors)
    response.set_data("monitor_count", len(monitors))
    response.append_text(f"Found {len(monitors)} monitors.")


list_monitors = define_tool(
    name="list_monitors",
    description="List all connected monitors with geometry and properties.",
    handler=_list_monitors,
    category=ToolCategory.SETTINGS,
)


# -- get_keyboard_layout  --


def _get_keyboard_layout(request: ToolRequest, response: McpResponse, context: McpContext) -> None:
    layout = keyboard.get_keyboard_layout()
    fmt = KeyboardLayoutFormatter(layout)
    for k, v in fmt.to_json().items():
        response.set_data(k, v)
    response.append_text(fmt.to_string())


get_keyboard_layout = define_tool(
    name="get_keyboard_layout",
    description="Read the active keyboard layout from GSettings.",
    handler=_get_keyboard_layout,
    category=ToolCategory.SETTINGS,
)


# -- list_key_names  --


def _list_key_names(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    category = request.params.get("category", "all")
    cat, keys = keyboard.list_key_names(category)
    fmt = KeyListFormatter(cat, keys)
    for k, v in fmt.to_json().items():
        response.set_data(k, v)
    response.append_text(fmt.to_string())


list_key_names = define_tool(
    name="list_key_names",
    description="List symbolic key names by category.",
    handler=_list_key_names,
    category=ToolCategory.SETTINGS,
    parameters={
        "category": {
            "type": "string",
            "default": "all",
            "description": ("Key category: navigation, function, modifier, editing, or all."),
        },
    },
)


# -- get_monitor_for_point  --


def _get_monitor_for_point(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    x = request.params.get("x", 0)
    y = request.params.get("y", 0)
    info = monitor.get_monitor_for_point(x, y)
    fmt = MonitorFormatter(info)
    for k, v in fmt.to_json().items():
        response.set_data(k, v)
    response.append_text(fmt.to_string())


get_monitor_for_point = define_tool(
    name="get_monitor_for_point",
    description="Return which monitor contains the given screen coordinates.",
    handler=_get_monitor_for_point,
    category=ToolCategory.SETTINGS,
    parameters={
        "x": {"type": "integer", "description": "X screen coordinate."},
        "y": {"type": "integer", "description": "Y screen coordinate."},
    },
)


# -- wayland_protocols  --


def _wayland_protocols(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    filter_protocol = request.params.get("filter_protocol", None)
    protocols = wayland.list_protocols(filter_protocol)
    fmt = ProtocolListFormatter(protocols)
    for k, v in fmt.to_json().items():
        response.set_data(k, v)
    response.append_text(fmt.to_string())


wayland_protocols = define_tool(
    name="wayland_protocols",
    description="List Wayland protocols supported by the compositor.",
    handler=_wayland_protocols,
    category=ToolCategory.SETTINGS,
    parameters={
        "filter_protocol": {
            "type": "string",
            "default": None,
            "description": "Filter protocols by substring match.",
        },
    },
)
