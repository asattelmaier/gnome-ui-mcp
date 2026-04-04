"""Mutable response builder for MCP tool handlers."""

from __future__ import annotations

import json
from dataclasses import asdict

from mcp.types import CallToolResult, ImageContent, TextContent

from . import __version__

type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]


class McpResponse:
    """Accumulates tool output during handler execution."""

    def __init__(self) -> None:
        self._is_error: bool = False
        self._error: str | None = None
        self._data: dict[str, JsonValue] = {}
        self._text_lines: list[str] = []
        self._images: list[ImageContent] = []

    def append_text(self, line: str) -> None:
        self._text_lines.append(line)

    def set_error(self, error: str) -> None:
        self._is_error = True
        self._error = error

    def attach_image(self, data: str, mime_type: str = "image/png") -> None:
        self._images.append(
            ImageContent(type="image", data=data, mimeType=mime_type),
        )

    def set_data(self, key: str, value: JsonValue) -> None:
        self._data[key] = value

    def set_element_result(
        self,
        element_id: str,
        method: str | None = None,
        input_injected: bool | None = None,
        effect_verified: bool | None = None,
        **extra: JsonValue,
    ) -> None:
        self._data["element_id"] = element_id
        if method is not None:
            self._data["method"] = method
        if input_injected is not None:
            self._data["input_injected"] = input_injected
        if effect_verified is not None:
            self._data["effect_verified"] = effect_verified
        self._data.update(extra)

    def set_items(self, key: str, items: list[dict[str, JsonValue]]) -> None:
        self._data[key] = items

    def set_matches(self, matches: list[dict[str, JsonValue]]) -> None:
        self._data["matches"] = matches

    def set_trees(self, trees: list[dict[str, JsonValue]]) -> None:
        self._data["trees"] = trees

    def set_screenshot(
        self,
        path: str,
        scale_factor: int,
        pixel_size: list[int] | None = None,
        logical_size: list[int] | None = None,
    ) -> None:
        self._data["path"] = path
        self._data["scale_factor"] = scale_factor
        if pixel_size is not None:
            self._data["pixel_size"] = pixel_size
        if logical_size is not None:
            self._data["logical_size"] = logical_size

    def set_result(self, result: object) -> None:
        if hasattr(result, "__dataclass_fields__"):
            for key, value in asdict(result).items():
                self._data[key] = value

    @property
    def is_error(self) -> bool:
        return self._is_error

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def text_lines(self) -> list[str]:
        return self._text_lines

    def to_tool_result(self) -> CallToolResult:
        if self._is_error:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=self._error or "Unknown error",
                    ),
                ],
                isError=True,
                _meta={"serverVersion": __version__},
            )

        structured: dict[str, JsonValue] = dict(self._data)
        if self._text_lines:
            structured["message"] = "\n".join(self._text_lines)

        if self._text_lines:
            text = "\n".join(self._text_lines)
        else:
            text = json.dumps(structured, indent=2)

        content: list[TextContent | ImageContent] = [
            TextContent(type="text", text=text),
        ]
        content.extend(self._images)

        return CallToolResult(
            content=content,
            structuredContent=structured,
            isError=False,
            _meta={"serverVersion": __version__},
        )

    @staticmethod
    def fail(error: str) -> McpResponse:
        response = McpResponse()
        response.set_error(error)
        return response
