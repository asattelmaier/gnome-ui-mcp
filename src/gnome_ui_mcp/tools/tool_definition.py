"""Tool definition types, schema validation, and factory helpers."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Protocol

from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory

type SchemaType = str | list[str]


@dataclass
class ParamSpec:
    """Schema specification for a single tool parameter."""

    type: SchemaType  # "string", "integer", "boolean", "number", "array", "null"
    default: object = None
    description: str | None = None
    has_default: bool = True
    items_type: SchemaType | None = None
    enum: list[object] | None = None


class ToolRequest:
    """Standardized request object passed to tool handlers."""

    def __init__(self, params: dict[str, object]) -> None:
        self._params = params

    @property
    def params(self) -> dict[str, object]:
        return self._params

    def __getattr__(self, name: str) -> object:
        try:
            return self._params[name]
        except KeyError:
            msg = f"Request has no parameter {name!r}"
            raise AttributeError(msg) from None


class ToolHandler(Protocol):
    """Handler signature: (request, response, context) -> None."""

    def __call__(
        self,
        request: ToolRequest,
        response: McpResponse,
        context: McpContext,
    ) -> None: ...


@dataclass
class ToolDefinition:
    """A single MCP tool: metadata + handler."""

    name: str
    description: str
    handler: ToolHandler
    category: ToolCategory = ToolCategory.SYSTEM
    parameters: dict[str, ParamSpec] = field(default_factory=dict)
    read_only: bool = True

    def validate_arguments(self, arguments: dict[str, object] | None) -> dict[str, object]:
        """Validate raw tool arguments against the declared parameter schema."""
        raw = {} if arguments is None else dict(arguments)
        validated: dict[str, object] = {}

        unknown = sorted(set(raw) - set(self.parameters))
        if unknown:
            joined = ", ".join(unknown)
            raise ValueError(f"Unknown parameter(s) for {self.name}: {joined}")

        for param_name, spec in self.parameters.items():
            if param_name not in raw:
                if spec.has_default:
                    validated[param_name] = deepcopy(spec.default)
                    continue
                raise ValueError(f"Missing required parameter {param_name!r} for {self.name}")

            value = raw[param_name]
            _validate_value(param_name, value, spec)
            validated[param_name] = value

        return validated


def _normalize_types(value: SchemaType | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _type_label(value: SchemaType | None) -> str:
    types = _normalize_types(value)
    return " or ".join(types)


def _matches_type(value: object, expected_type: str) -> bool:
    if expected_type == "null":
        return value is None
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return (isinstance(value, int | float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "array":
        return isinstance(value, list)
    return False


def _validate_value(name: str, value: object, spec: ParamSpec) -> None:
    expected_types = _normalize_types(spec.type)

    if not any(_matches_type(value, expected_type) for expected_type in expected_types):
        actual_type = type(value).__name__
        expected = _type_label(spec.type)
        raise ValueError(f"Parameter {name!r} must be {expected}, got {actual_type}")

    if value is None:
        return

    if "array" in expected_types and isinstance(value, list) and spec.items_type is not None:
        item_types = _normalize_types(spec.items_type)
        for index, item in enumerate(value):
            if not any(_matches_type(item, item_type) for item_type in item_types):
                actual_type = type(item).__name__
                expected = _type_label(spec.items_type)
                raise ValueError(
                    f"Parameter {name!r}[{index}] must be {expected}, got {actual_type}"
                )

    if spec.enum is not None and value not in spec.enum:
        allowed = ", ".join(repr(item) for item in spec.enum)
        raise ValueError(f"Parameter {name!r} must be one of: {allowed}")


def define_tool(
    name: str,
    description: str,
    handler: ToolHandler,
    category: ToolCategory = ToolCategory.SYSTEM,
    parameters: dict[str, dict[str, object]] | None = None,
    read_only: bool = True,
) -> ToolDefinition:
    """Create a tool definition from a parameter dict shorthand."""
    params: dict[str, ParamSpec] = {}
    if parameters:
        for param_name, spec in parameters.items():
            has_default = "default" in spec
            params[param_name] = ParamSpec(
                type=spec.get("type", "string"),
                default=spec.get("default"),
                description=(
                    spec.get("description") if isinstance(spec.get("description"), str) else None
                ),
                has_default=has_default,
                items_type=spec.get("items_type"),
                enum=spec.get("enum") if isinstance(spec.get("enum"), list) else None,
            )
    return ToolDefinition(
        name=name,
        description=description,
        handler=handler,
        category=category,
        parameters=params,
        read_only=read_only,
    )
