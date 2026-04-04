"""Visual tools: screenshots, pixel colors, diffs, and highlights."""

from __future__ import annotations

from ..adapters import elements, screenshots, state
from ..adapters import input as input_mod
from ..formatters.state_formatter import VisualDiffFormatter
from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory
from .tool_definition import ToolRequest, define_tool

# -- screenshot --


def _screenshot(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    filename = request.params.get("filename", None)
    return_base64 = request.params.get("return_base64", False)
    result = input_mod.screenshot(filename=filename, return_base64=return_base64)
    response.set_screenshot(
        path=result.path,
        scale_factor=result.scale_factor,
        pixel_size=result.pixel_size,
        logical_size=result.logical_size,
    )
    response.append_text(f"Screenshot saved to {result.path}.")

    if result.image_base64 is not None:
        response.attach_image(result.image_base64)


screenshot = define_tool(
    name="screenshot",
    description=(
        "Capture the current GNOME desktop to a PNG file. "
        "Optionally return the image as a base64-encoded string."
    ),
    handler=_screenshot,
    category=ToolCategory.VISUAL,
    parameters={
        "filename": {
            "type": "string",
            "default": None,
            "description": "Output file path. Auto-generated if omitted.",
        },
        "return_base64": {
            "type": "boolean",
            "default": False,
            "description": "Include the image in the response content.",
        },
    },
)


# -- screenshot_area --


def _screenshot_area(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    x = request.params.get("x", 0)
    y = request.params.get("y", 0)
    width = request.params.get("width", 100)
    height = request.params.get("height", 100)
    filename = request.params.get("filename", None)
    result = screenshots.screenshot_area(x=x, y=y, width=width, height=height, filename=filename)
    response.set_data("path", result.path)
    response.append_text(f"Area screenshot saved to {result.path}.")


screenshot_area = define_tool(
    name="screenshot_area",
    description="Capture a rectangular region of the screen to a PNG file.",
    handler=_screenshot_area,
    category=ToolCategory.VISUAL,
    parameters={
        "x": {"type": "integer", "description": "X coordinate of the region."},
        "y": {"type": "integer", "description": "Y coordinate of the region."},
        "width": {"type": "integer", "description": "Width of the region."},
        "height": {"type": "integer", "description": "Height of the region."},
        "filename": {
            "type": "string",
            "default": None,
            "description": "Output file path. Auto-generated if omitted.",
        },
    },
)


# -- screenshot_window --


def _screenshot_window(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    window_element_id = request.params.get("window_element_id", "")
    include_frame = request.params.get("include_frame", True)
    include_cursor = request.params.get("include_cursor", False)
    filename = request.params.get("filename", None)
    result = screenshots.screenshot_window(
        window_element_id=window_element_id,
        include_frame=include_frame,
        include_cursor=include_cursor,
        filename=filename,
    )
    response.set_data("path", result.path)
    response.set_data("window_element_id", result.window_element_id)
    response.append_text(f"Window screenshot saved to {result.path}.")


screenshot_window = define_tool(
    name="screenshot_window",
    description=(
        "Capture a window to a PNG file. Focuses the window by element_id first, "
        "then captures the currently focused window via D-Bus ScreenshotWindow."
    ),
    handler=_screenshot_window,
    category=ToolCategory.VISUAL,
    parameters={
        "window_element_id": {
            "type": "string",
            "description": "Element ID of the window to capture.",
        },
        "include_frame": {
            "type": "boolean",
            "default": True,
            "description": "Include window frame decorations.",
        },
        "include_cursor": {
            "type": "boolean",
            "default": False,
            "description": "Include mouse cursor in screenshot.",
        },
        "filename": {
            "type": "string",
            "default": None,
            "description": "Output file path. Auto-generated if omitted.",
        },
    },
)


# -- get_pixel_color --


def _get_pixel_color(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    x = request.params.get("x", 0)
    y = request.params.get("y", 0)
    result = state.get_pixel_color(x=x, y=y)
    response.set_data("x", result.x)
    response.set_data("y", result.y)
    response.set_data("r", result.r)
    response.set_data("g", result.g)
    response.set_data("b", result.b)
    response.set_data("a", result.a)
    response.set_data("hex", result.hex)
    response.append_text(f"Pixel color at ({x}, {y}): {result.hex}")


get_pixel_color = define_tool(
    name="get_pixel_color",
    description="Get the pixel color at screen coordinates.",
    handler=_get_pixel_color,
    category=ToolCategory.VISUAL,
    parameters={
        "x": {"type": "integer", "description": "X screen coordinate."},
        "y": {"type": "integer", "description": "Y screen coordinate."},
    },
)


# -- get_region_color --


def _get_region_color(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    x = request.params.get("x", 0)
    y = request.params.get("y", 0)
    width = request.params.get("width", 1)
    height = request.params.get("height", 1)
    result = state.get_region_color(x=x, y=y, width=width, height=height)
    response.set_data("x", result.x)
    response.set_data("y", result.y)
    response.set_data("width", result.width)
    response.set_data("height", result.height)
    response.set_data("r", result.r)
    response.set_data("g", result.g)
    response.set_data("b", result.b)
    response.set_data("a", result.a)
    response.set_data("hex", result.hex)
    response.append_text(f"Average color of region at ({x}, {y}): {result.hex}")


get_region_color = define_tool(
    name="get_region_color",
    description="Get the average color of a screen region.",
    handler=_get_region_color,
    category=ToolCategory.VISUAL,
    parameters={
        "x": {"type": "integer", "description": "X coordinate of region."},
        "y": {"type": "integer", "description": "Y coordinate of region."},
        "width": {"type": "integer", "description": "Width of region."},
        "height": {"type": "integer", "description": "Height of region."},
    },
)


# -- visual_diff --


def _visual_diff(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    image_path_1 = request.params.get("image_path_1", "")
    image_path_2 = request.params.get("image_path_2", "")
    threshold = request.params.get("threshold", 30)
    result = state.visual_diff(
        image_path_1=image_path_1,
        image_path_2=image_path_2,
        threshold=threshold,
    )
    fmt = VisualDiffFormatter(result)
    for k, v in fmt.to_json().items():
        response.set_data(k, v)
    response.append_text(fmt.to_string())


visual_diff = define_tool(
    name="visual_diff",
    description="Compare two screenshots and return changed regions.",
    handler=_visual_diff,
    category=ToolCategory.VISUAL,
    parameters={
        "image_path_1": {
            "type": "string",
            "description": "Path to the first image.",
        },
        "image_path_2": {
            "type": "string",
            "description": "Path to the second image.",
        },
        "threshold": {
            "type": "integer",
            "default": 30,
            "description": "Color difference threshold (0-255).",
        },
    },
)


# -- highlight_element --


def _highlight_element(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    element_id = request.params.get("element_id", "")
    color = request.params.get("color", "red")
    label = request.params.get("label", None)
    result = elements.highlight_element(element_id=element_id, color=color, label=label)
    response.set_data("path", result.path)
    response.set_data("element_id", result.element_id)
    response.set_data("bounds", result.bounds)
    response.append_text(f"Highlighted element {element_id} in {color}.")


highlight_element = define_tool(
    name="highlight_element",
    description=(
        "Take a screenshot with a colored rectangle highlighting an element for visual debugging."
    ),
    handler=_highlight_element,
    category=ToolCategory.VISUAL,
    parameters={
        "element_id": {"type": "string", "description": "Element ID to highlight."},
        "color": {
            "type": "string",
            "default": "red",
            "description": "Color of the highlight rectangle.",
        },
        "label": {
            "type": "string",
            "default": None,
            "description": "Optional label to display on the highlight.",
        },
    },
)


# -- analyze_screenshot --


def _analyze_screenshot(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    prompt = request.params.get("prompt", "")
    provider = request.params.get("provider", "openrouter")
    model = request.params.get("model", None)
    result = state.analyze_screenshot(prompt=prompt, provider=provider, model=model)
    response.set_data("analysis", result.analysis)
    response.set_data("provider", result.provider)
    response.set_data("model", result.model)
    response.append_text(f"Screenshot analysis: {result.analysis[:200]}")


analyze_screenshot = define_tool(
    name="analyze_screenshot",
    description="Analyze a screenshot using a vision language model.",
    handler=_analyze_screenshot,
    category=ToolCategory.VISUAL,
    parameters={
        "prompt": {"type": "string", "description": "Analysis prompt."},
        "provider": {
            "type": "string",
            "default": "openrouter",
            "description": "VLM provider: openrouter, anthropic, or ollama.",
        },
        "model": {
            "type": "string",
            "default": None,
            "description": "Specific model to use.",
        },
    },
)


# -- compare_screenshots --


def _compare_screenshots(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    image_path_1 = request.params.get("image_path_1", "")
    image_path_2 = request.params.get("image_path_2", "")
    prompt = request.params.get("prompt", None)
    provider = request.params.get("provider", "openrouter")
    model = request.params.get("model", None)
    result = state.compare_screenshots(
        path1=image_path_1,
        path2=image_path_2,
        prompt=prompt,
        provider=provider,
        model=model,
    )
    response.set_data("analysis", result.analysis)
    response.set_data("provider", result.provider)
    response.set_data("model", result.model)
    response.set_data("path1", result.path1)
    response.set_data("path2", result.path2)
    response.append_text("Screenshot comparison complete.")


compare_screenshots = define_tool(
    name="compare_screenshots",
    description="Compare two screenshots using a vision language model.",
    handler=_compare_screenshots,
    category=ToolCategory.VISUAL,
    parameters={
        "image_path_1": {
            "type": "string",
            "description": "Path to the first screenshot.",
        },
        "image_path_2": {
            "type": "string",
            "description": "Path to the second screenshot.",
        },
        "prompt": {
            "type": "string",
            "default": None,
            "description": "Custom comparison prompt.",
        },
        "provider": {
            "type": "string",
            "default": "openrouter",
            "description": "VLM provider: openrouter, anthropic, or ollama.",
        },
        "model": {
            "type": "string",
            "default": None,
            "description": "Specific model to use.",
        },
    },
)
