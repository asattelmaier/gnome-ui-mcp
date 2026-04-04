"""OCR tools: text extraction, search, click, and type by label."""

from __future__ import annotations

from ..adapters import state
from ..formatters.state_formatter import OcrResultFormatter
from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory
from .tool_definition import ToolRequest, define_tool

# -- ocr_screen --


def _ocr_screen(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    x = request.params.get("x", None)
    y = request.params.get("y", None)
    width = request.params.get("width", None)
    height = request.params.get("height", None)
    result = state.ocr_screen(x=x, y=y, width=width, height=height)
    fmt = OcrResultFormatter(result)
    for k, v in fmt.to_json().items():
        response.set_data(k, v)
    response.append_text(fmt.to_string())


ocr_screen = define_tool(
    name="ocr_screen",
    description=(
        "Extract text from the screen or a region using OCR. Use for apps with poor accessibility."
    ),
    handler=_ocr_screen,
    category=ToolCategory.STATE,
    parameters={
        "x": {
            "type": "integer",
            "default": None,
            "description": "X coordinate of region.",
        },
        "y": {
            "type": "integer",
            "default": None,
            "description": "Y coordinate of region.",
        },
        "width": {
            "type": "integer",
            "default": None,
            "description": "Width of region.",
        },
        "height": {
            "type": "integer",
            "default": None,
            "description": "Height of region.",
        },
    },
)


# -- find_text_ocr --


def _find_text_ocr(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    target = request.params.get("target", "")
    x = request.params.get("x", None)
    y = request.params.get("y", None)
    width = request.params.get("width", None)
    height = request.params.get("height", None)
    result = state.find_text_ocr(target=target, x=x, y=y, width=width, height=height)
    response.set_data("target", result.target)
    response.set_data("found", result.found)
    response.set_items("matches", result.matches)
    response.set_data("match_count", result.match_count)
    response.append_text(f"Text '{target}' {'found' if result.found else 'not found'} on screen.")


find_text_ocr = define_tool(
    name="find_text_ocr",
    description="Find text on screen via OCR and return its coordinates.",
    handler=_find_text_ocr,
    category=ToolCategory.STATE,
    parameters={
        "target": {"type": "string", "description": "Text to search for."},
        "x": {
            "type": "integer",
            "default": None,
            "description": "X coordinate of search region.",
        },
        "y": {
            "type": "integer",
            "default": None,
            "description": "Y coordinate of search region.",
        },
        "width": {
            "type": "integer",
            "default": None,
            "description": "Width of search region.",
        },
        "height": {
            "type": "integer",
            "default": None,
            "description": "Height of search region.",
        },
    },
)


# -- click_text_ocr --


def _click_text_ocr(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    target = request.params.get("target", "")
    button = request.params.get("button", "left")
    result = state.click_text_ocr(target=target, button=button)
    response.set_data("target", result.target)
    response.set_data("ocr_match", result.ocr_match)
    response.set_data("input_injected", result.input_injected)
    response.set_data("effect_verified", result.effect_verified)
    response.append_text(f"Clicked text '{target}' via OCR.")


click_text_ocr = define_tool(
    name="click_text_ocr",
    description="Find text on screen via OCR and click it.",
    handler=_click_text_ocr,
    category=ToolCategory.STATE,
    read_only=False,
    parameters={
        "target": {"type": "string", "description": "Text to find and click."},
        "button": {
            "type": "string",
            "default": "left",
            "description": "Mouse button: left, middle, or right.",
        },
    },
)


# -- type_into --


def _type_into(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    label = request.params.get("label", "")
    text = request.params.get("text", "")
    submit = request.params.get("submit", False)
    result = state.type_into(label=label, text=text, submit=submit)
    response.set_data("label", result.label)
    response.set_data("method", result.method)
    if result.element_id is not None:
        response.set_data("element_id", result.element_id)
    response.append_text(f"Typed '{text}' into field labeled '{label}'.")


type_into = define_tool(
    name="type_into",
    description=("Find an input field by label text and type into it. AT-SPI first, OCR fallback."),
    handler=_type_into,
    category=ToolCategory.STATE,
    read_only=False,
    parameters={
        "label": {"type": "string", "description": "Label text of the input field."},
        "text": {"type": "string", "description": "Text to type into the field."},
        "submit": {
            "type": "boolean",
            "default": False,
            "description": "Press Enter after typing.",
        },
    },
)
