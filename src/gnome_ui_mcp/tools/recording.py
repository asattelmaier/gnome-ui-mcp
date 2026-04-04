"""Screen recording tools."""

from __future__ import annotations

from ..adapters import recording
from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory
from .tool_definition import ToolRequest, define_tool

# -- screen_record_start --


def _screen_record_start(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    x = request.params.get("x", None)
    y = request.params.get("y", None)
    width = request.params.get("width", None)
    height = request.params.get("height", None)
    framerate = request.params.get("framerate", 30)
    draw_cursor = request.params.get("draw_cursor", True)
    result = recording.screen_record_start(
        x=x,
        y=y,
        width=width,
        height=height,
        framerate=framerate,
        draw_cursor=draw_cursor,
    )
    response.set_data("path", result.path)
    response.append_text(f"Screen recording started: {result.path}")


screen_record_start = define_tool(
    name="screen_record_start",
    description="Start recording the screen or a region to video.",
    handler=_screen_record_start,
    category=ToolCategory.RECORDING,
    read_only=False,
    parameters={
        "x": {
            "type": "integer",
            "default": None,
            "description": "X coordinate of recording region.",
        },
        "y": {
            "type": "integer",
            "default": None,
            "description": "Y coordinate of recording region.",
        },
        "width": {
            "type": "integer",
            "default": None,
            "description": "Width of recording region.",
        },
        "height": {
            "type": "integer",
            "default": None,
            "description": "Height of recording region.",
        },
        "framerate": {
            "type": "integer",
            "default": 30,
            "description": "Recording framerate.",
        },
        "draw_cursor": {
            "type": "boolean",
            "default": True,
            "description": "Include mouse cursor in recording.",
        },
    },
)


# -- screen_record_stop --


def _screen_record_stop(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    to_gif = request.params.get("to_gif", False)
    gif_fps = request.params.get("gif_fps", 10)
    gif_width = request.params.get("gif_width", 640)
    result = recording.screen_record_stop(to_gif=to_gif, gif_fps=gif_fps, gif_width=gif_width)
    response.set_data("path", result.path)
    if result.gif_path is not None:
        response.set_data("gif_path", result.gif_path)
    response.append_text(f"Screen recording stopped: {result.path}")


screen_record_stop = define_tool(
    name="screen_record_stop",
    description="Stop recording and optionally convert to GIF.",
    handler=_screen_record_stop,
    category=ToolCategory.RECORDING,
    read_only=False,
    parameters={
        "to_gif": {
            "type": "boolean",
            "default": False,
            "description": "Convert recording to GIF.",
        },
        "gif_fps": {
            "type": "integer",
            "default": 10,
            "description": "GIF frames per second.",
        },
        "gif_width": {
            "type": "integer",
            "default": 640,
            "description": "GIF width in pixels.",
        },
    },
)
