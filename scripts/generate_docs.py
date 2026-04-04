#!/usr/bin/env python3
"""Generate OpenAPI 3.1 documentation from the low-level MCP tool registry."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from gnome_ui_mcp import __version__  # noqa: E402
from gnome_ui_mcp.server import _build_input_schema  # noqa: E402
from gnome_ui_mcp.tools.categories import TOOL_CATEGORY_LABELS  # noqa: E402
from gnome_ui_mcp.tools.tools import create_tools  # noqa: E402

OUTPUT = ROOT / "docs" / "openapi.json"


def _response_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "description": "Structured MCP tool result payload.",
        "additionalProperties": True,
    }


def tool_to_operation(tool: Any) -> dict[str, Any]:
    """Convert a ToolDefinition to an OpenAPI operation (POST)."""
    operation: dict[str, Any] = {
        "operationId": tool.name,
        "summary": tool.description,
        "description": tool.description,
        "tags": [TOOL_CATEGORY_LABELS[tool.category]],
        "responses": {
            "200": {
                "description": "Tool result as structured JSON",
                "content": {
                    "application/json": {
                        "schema": _response_schema(),
                    }
                },
            }
        },
    }

    schema = _build_input_schema(tool)
    if schema.get("properties"):
        operation["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": schema,
                }
            },
        }

    return operation


def build_openapi(version: str) -> dict[str, Any]:
    """Build a complete OpenAPI 3.1 spec from all MCP tools."""
    tools = create_tools()
    paths = {f"/tools/{tool.name}": {"post": tool_to_operation(tool)} for tool in tools}
    tag_names = sorted({TOOL_CATEGORY_LABELS[tool.category] for tool in tools})
    tags = [{"name": name} for name in tag_names]

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "gnome-ui-mcp Tool Reference",
            "version": version,
            "description": (
                "Complete reference for all MCP tools provided by gnome-ui-mcp. "
                "The server automates GNOME desktop sessions via AT-SPI, Mutter, D-Bus, "
                "and Wayland. Tools are invoked via MCP, not HTTP. This OpenAPI spec "
                "is documentation only."
            ),
            "license": {"name": "MIT"},
            "contact": {
                "url": "https://github.com/asattelmaier/gnome-ui-mcp",
            },
        },
        "tags": tags,
        "paths": paths,
    }


def main() -> None:
    tools = create_tools()
    if not tools:
        print("Error: No tools found in registry.", file=sys.stderr)
        sys.exit(1)

    spec = build_openapi(str(__version__))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(spec, indent=2))
    print(f"Generated {OUTPUT} with {len(tools)} tools (version {__version__})")


if __name__ == "__main__":
    main()
