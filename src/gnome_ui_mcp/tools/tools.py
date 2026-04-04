"""Tool aggregation and registration.

Collects all ToolDefinition instances from domain modules and sorts
them alphabetically. New tools are automatically discovered -- no
manual list needed.
"""

from __future__ import annotations

import importlib
from types import ModuleType

from .tool_definition import ToolDefinition

# Domain modules containing tool definitions
_TOOL_MODULES: list[str] = [
    "apps",
    "discovery",
    "elements",
    "input",
    "monitoring",
    "recording",
    "ocr",
    "session_tools",
    "settings",
    "state",
    "system",
    "visual",
    "waiting",
    "window",
    "workspace",
]


def _collect_from_module(module: ModuleType) -> list[ToolDefinition]:
    """Extract all ToolDefinition instances from a module."""
    return [obj for obj in vars(module).values() if isinstance(obj, ToolDefinition)]


def create_tools() -> list[ToolDefinition]:
    """Collect all tool definitions, sorted alphabetically by name."""
    tools: list[ToolDefinition] = []
    package = __package__

    for module_name in _TOOL_MODULES:
        full_name = f"{package}.{module_name}"
        module = importlib.import_module(full_name)
        tools.extend(_collect_from_module(module))

    tools.sort(key=lambda t: t.name)
    return tools
