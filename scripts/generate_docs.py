#!/usr/bin/env python3
"""Generate OpenAPI 3.1 JSON documentation from FastMCP tool definitions."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Add src/ to sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from gnome_ui_mcp import __version__
from gnome_ui_mcp.server import mcp  # noqa: E402

OUTPUT = ROOT / "docs" / "openapi.json"


def rewrite_defs_refs(obj: Any) -> Any:
    """Recursively rewrite #/$defs/Foo refs to #/components/schemas/Foo."""
    if isinstance(obj, dict):
        if "$ref" in obj and obj["$ref"].startswith("#/$defs/"):
            name = obj["$ref"].removeprefix("#/$defs/")
            return {"$ref": f"#/components/schemas/{name}"}
        return {k: rewrite_defs_refs(v) for k, v in obj.items() if k != "$defs"}
    if isinstance(obj, list):
        return [rewrite_defs_refs(item) for item in obj]
    return obj


def _infer_tag(tool_name: str) -> str:
    """Map tool names to logical groups for Redoc sidebar sections."""
    tag_map = {
        "ping": "Health",
        "list_applications": "Applications",
        "list_windows": "Window Management",
        "accessibility_tree": "Accessibility",
        "find_elements": "Accessibility",
        "find_elements_for_elements": "Accessibility",
        "element_at_point": "Accessibility",
        "get_focused_element": "Accessibility",
        "get_element_properties": "Accessibility",
        "get_element_text": "Accessibility",
        "get_element_path": "Accessibility",
        "get_elements_by_ids": "Accessibility",
        "get_table_info": "Accessibility",
        "get_table_cell": "Accessibility",
        "current_focus_metadata": "Accessibility",
        "resolve_click_target": "Accessibility",
        "assert_element": "Assertions",
        "assert_text": "Assertions",
        "click_element": "Interaction",
        "click_at": "Interaction",
        "activate_element": "Interaction",
        "find_and_activate": "Interaction",
        "hover_element": "Interaction",
        "drag": "Interaction",
        "focus_element": "Interaction",
        "type_text": "Input",
        "press_key": "Input",
        "key_combo": "Input",
        "set_element_text": "Input",
        "set_element_value": "Input",
        "select_element_text": "Input",
        "type_into": "Input",
        "screenshot": "Screenshots",
        "screenshot_area": "Screenshots",
        "screenshot_window": "Screenshots",
        "screenshot_burst": "Screenshots",
        "ocr_screen": "Vision & OCR",
        "find_text_ocr": "Vision & OCR",
        "click_text_ocr": "Vision & OCR",
        "analyze_screenshot": "Vision & OCR",
        "compare_screenshots": "Vision & OCR",
        "get_pixel_color": "Vision & OCR",
        "get_region_color": "Vision & OCR",
        "visual_diff": "Vision & OCR",
        "scroll": "Mouse",
        "mouse_move": "Mouse",
        "scroll_to_element": "Mouse",
        "wait_for_element": "Wait & Timing",
        "wait_for_element_gone": "Wait & Timing",
        "wait_for_app": "Wait & Timing",
        "wait_for_window": "Wait & Timing",
        "wait_for_popup_count": "Wait & Timing",
        "wait_for_shell_settled": "Wait & Timing",
        "wait_and_act": "Wait & Timing",
        "app_wait": "Wait & Timing",
        "navigate_menu": "UI Patterns",
        "file_dialog_set_path": "UI Patterns",
        "visible_shell_popups": "UI Patterns",
        "select_option": "UI Patterns",
        "expand_node": "UI Patterns",
        "collapse_node": "UI Patterns",
        "set_toggle_state": "UI Patterns",
        "subscribe_events": "Events",
        "poll_events": "Events",
        "unsubscribe_events": "Events",
        "snapshot_state": "State & History",
        "compare_state": "State & History",
        "get_action_history": "State & History",
        "set_boundaries": "Boundaries",
        "clear_boundaries": "Boundaries",
        "highlight_element": "Inspection",
        "get_keyboard_layout": "Inspection",
        "list_key_names": "Inspection",
        "get_display_scale_factor": "Inspection",
        "get_monitor_for_point": "Inspection",
        "session_start": "Session",
        "session_stop": "Session",
        "session_info": "Session",
        "clipboard_read": "Clipboard",
        "clipboard_write": "Clipboard",
        "dbus_call": "System",
        "list_monitors": "System",
        "gsettings_get": "System",
        "gsettings_set": "System",
        "gsettings_list_keys": "System",
        "gsettings_reset": "System",
        "wayland_protocols": "System",
        "notification_monitor_start": "Notifications",
        "notification_monitor_read": "Notifications",
        "notification_monitor_stop": "Notifications",
        "dismiss_notification": "Notifications",
        "click_notification_action": "Notifications",
        "screen_record_start": "Screen Recording",
        "screen_record_stop": "Screen Recording",
        "switch_workspace": "Workspace",
        "move_window_to_workspace": "Workspace",
        "list_workspaces": "Workspace",
        "toggle_overview": "Workspace",
        "close_window": "Window Mgmt",
        "move_window": "Window Mgmt",
        "resize_window": "Window Mgmt",
        "snap_window": "Window Mgmt",
        "toggle_window_state": "Window Mgmt",
        "list_desktop_apps": "App Launcher",
        "launch_app": "App Launcher",
        "launch_with_logging": "App Launcher",
        "read_app_log": "App Launcher",
    }
    return tag_map.get(tool_name, "General")


def tool_to_operation(tool: Any) -> dict:
    """Convert a FastMCP Tool to an OpenAPI operation (POST)."""
    params_schema = tool.parameters  # Already a full JSON Schema from Pydantic

    # Strip $defs from inline schema
    inline_schema = {k: v for k, v in params_schema.items() if k != "$defs"}

    # Rewrite any $defs refs to components/schemas refs
    inline_schema = rewrite_defs_refs(inline_schema)

    has_params = bool(params_schema.get("properties"))

    operation: dict = {
        "operationId": tool.name,
        "summary": tool.description,
        "description": tool.description,
        "tags": [_infer_tag(tool.name)],
        "responses": {
            "200": {
                "description": "Tool result as JSON object",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "success": {"type": "boolean", "description": "Whether the tool call succeeded"},
                                "error": {"type": "string", "description": "Error message if success is false"},
                            },
                        }
                    }
                },
            }
        },
    }

    if has_params:
        operation["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": inline_schema,
                }
            },
        }

    return operation


def collect_global_defs(tools: list) -> dict:
    """Collect all $defs from all tool parameter schemas into one dict."""
    global_defs: dict = {}
    for tool in tools:
        defs = tool.parameters.get("$defs", {})
        global_defs.update(defs)
    return rewrite_defs_refs(global_defs)


def build_openapi(tools: list, version: str) -> dict:
    """Build complete OpenAPI 3.1 spec from tools."""
    tags_seen: set[str] = set()
    paths: dict = {}

    for tool in sorted(tools, key=lambda t: t.name):
        tag = _infer_tag(tool.name)
        tags_seen.add(tag)
        paths[f"/tools/{tool.name}"] = {"post": tool_to_operation(tool)}

    global_defs = collect_global_defs(tools)

    spec: dict = {
        "openapi": "3.1.0",
        "info": {
            "title": "gnome-ui-mcp Tool Reference",
            "version": version,
            "description": (
                "Complete reference for all MCP tools provided by gnome-ui-mcp. "
                "This server automates GNOME desktop sessions via AT-SPI, Mutter, D-Bus, "
                "and Wayland. Tools are invoked via the MCP protocol, not HTTP — "
                "this OpenAPI spec is documentation only."
            ),
            "license": {"name": "MIT"},
            "contact": {
                "url": "https://github.com/asattelmaier/gnome-ui-mcp",
            },
        },
        "tags": sorted([{"name": tag} for tag in tags_seen], key=lambda t: t["name"]),
        "paths": paths,
    }

    if global_defs:
        spec["components"] = {"schemas": global_defs}

    return spec


def main() -> None:
    """Generate OpenAPI spec and write to file."""
    try:
        tools = mcp._tool_manager.list_tools()
    except AttributeError:
        print("Error: Could not access FastMCP tool registry. Is mcp._tool_manager available?", file=sys.stderr)
        sys.exit(1)

    if not tools:
        print("Error: No tools found in FastMCP registry.", file=sys.stderr)
        sys.exit(1)

    version = str(__version__)
    spec = build_openapi(tools, version)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(spec, indent=2))
    print(f"✓ Generated {OUTPUT} with {len(tools)} tools (version {version})")


if __name__ == "__main__":
    main()
