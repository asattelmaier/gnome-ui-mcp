"""Low-level MCP server factory, transport helpers, and tool registration."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import sys
from collections.abc import AsyncIterator
from typing import Literal

import anyio
from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.shared.message import SessionMessage

from .mcp_context import McpContext
from .mcp_response import McpResponse
from .tools.categories import ToolCategory
from .tools.tool_definition import ToolDefinition, ToolRequest
from .tools.tools import create_tools

logger = logging.getLogger(__name__)

_DEFAULT_ENABLED: set[ToolCategory] = set(ToolCategory)
_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8000
_SSE_PATH = "/sse"
_MESSAGE_PATH = "/messages/"
_STREAMABLE_HTTP_PATH = "/mcp"


def create_server(
    enabled_categories: set[ToolCategory] | None = None,
) -> Server:
    """Create and configure the MCP server with all tools registered."""
    enabled = enabled_categories if enabled_categories is not None else _DEFAULT_ENABLED

    all_tools = create_tools()
    tools = [tool for tool in all_tools if tool.category in enabled]
    tools_by_name = {tool.name: tool for tool in tools}

    logger.info(
        "Registered %d of %d tools (categories: %s).",
        len(tools),
        len(all_tools),
        ", ".join(sorted(category.value for category in enabled)),
    )

    server = Server(
        name="gnome-ui-mcp",
        instructions=(
            "Use the GNOME accessibility stack to inspect and control the current desktop session."
        ),
    )

    context: McpContext | None = None
    lock = asyncio.Lock()

    def get_context() -> McpContext:
        nonlocal context
        if context is None:
            context = McpContext()
        return context

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=tool.name,
                description=tool.description,
                inputSchema=_build_input_schema(tool),
                annotations=types.ToolAnnotations(
                    title=tool.category.label,
                    readOnlyHint=tool.read_only,
                ),
            )
            for tool in tools
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict | None) -> types.CallToolResult:
        tool = tools_by_name.get(name)
        if tool is None:
            return McpResponse.fail(f"Unknown tool: {name}").to_tool_result()

        async with lock:
            response = McpResponse()
            try:
                request = ToolRequest(tool.validate_arguments(arguments))
                tool.handler(request, response, get_context())
            except Exception as exc:
                logger.debug("%s error: %s", name, exc, exc_info=True)
                error_text = str(exc)
                if exc.__cause__ is not None:
                    error_text += f"\nCause: {exc.__cause__}"
                response.set_error(error_text)
            return response.to_tool_result()

    return server


def _schema_type(value: str | list[str]) -> str | list[str]:
    if isinstance(value, list) and len(value) == 1:
        return value[0]
    return value


def _build_input_schema(tool: ToolDefinition) -> dict[str, object]:
    """Build JSON Schema for a tool's declared parameters."""
    if not tool.parameters:
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }

    properties: dict[str, dict[str, object]] = {}
    required: list[str] = []

    for name, spec in tool.parameters.items():
        prop: dict[str, object] = {"type": _schema_type(spec.type)}

        if spec.description is not None:
            prop["description"] = spec.description

        spec_types = spec.type if isinstance(spec.type, list) else [spec.type]
        if "array" in spec_types and spec.items_type is not None:
            prop["items"] = {"type": _schema_type(spec.items_type)}

        if spec.enum is not None:
            prop["enum"] = spec.enum

        if spec.has_default and spec.default is not None:
            prop["default"] = spec.default

        if spec.has_default and spec.default is None and "null" not in spec_types:
            prop = {"anyOf": [prop, {"type": "null"}], "default": None}
            if spec.description is not None:
                prop["description"] = spec.description
        elif not spec.has_default:
            required.append(name)

        properties[name] = prop

    schema: dict[str, object] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema


@contextlib.asynccontextmanager
async def _stdio_jsonrpc_server() -> AsyncIterator[
    tuple[anyio.abc.ObjectReceiveStream, anyio.abc.ObjectSendStream]
]:
    """Serve newline-delimited JSON-RPC over stdio.

    This avoids transport quirks we observed with the library stdio helper in
    subprocess mode while keeping the same SessionMessage contract expected by
    the low-level MCP server.
    """

    read_stream_writer, read_stream = anyio.create_memory_object_stream[SessionMessage | Exception](
        1
    )
    write_stream, write_stream_reader = anyio.create_memory_object_stream[SessionMessage](1)
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    read_transport, _ = await loop.connect_read_pipe(lambda: protocol, sys.stdin.buffer)

    async def stdin_reader() -> None:
        try:
            async with read_stream_writer:
                while True:
                    line = await reader.readline()
                    if line == b"":
                        return

                    text = line.decode("utf-8").strip()
                    if not text:
                        continue

                    try:
                        message = types.JSONRPCMessage.model_validate_json(text)
                    except Exception as exc:  # pragma: no cover
                        await read_stream_writer.send(exc)
                        continue

                    await read_stream_writer.send(SessionMessage(message))
        except anyio.ClosedResourceError:  # pragma: no cover
            await anyio.lowlevel.checkpoint()
        finally:
            read_transport.close()

    async def stdout_writer() -> None:
        try:
            async with write_stream_reader:
                async for session_message in write_stream_reader:
                    json_message = session_message.message.model_dump_json(
                        by_alias=True,
                        exclude_none=True,
                    )
                    sys.stdout.buffer.write((json_message + "\n").encode("utf-8"))
                    sys.stdout.buffer.flush()
        except anyio.ClosedResourceError:  # pragma: no cover
            await anyio.lowlevel.checkpoint()

    async with anyio.create_task_group() as tg:
        tg.start_soon(stdin_reader)
        tg.start_soon(stdout_writer)
        yield read_stream, write_stream


async def run_stdio_async(server: Server | None = None) -> None:
    """Run the server over stdio."""
    app = server or mcp
    async with _stdio_jsonrpc_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def _normalize_path(prefix: str | None, path: str) -> str:
    if not prefix:
        return path
    return f"{prefix.rstrip('/')}{path}"


def sse_app(server: Server | None = None, mount_path: str | None = None):
    """Build a Starlette app serving the MCP server over SSE."""
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.routing import Mount, Route
    from starlette.types import Receive, Scope, Send

    app = server or mcp
    sse = SseServerTransport(_normalize_path(mount_path, _MESSAGE_PATH))

    async def handle_sse(scope: Scope, receive: Receive, send: Send) -> None:
        async with sse.connect_sse(scope, receive, send) as streams:
            await app.run(
                streams[0],
                streams[1],
                app.create_initialization_options(),
            )

    async def sse_endpoint(request: Request) -> Response:
        await handle_sse(request.scope, request.receive, request._send)  # type: ignore[attr-defined]
        return Response()

    routes = [
        Route(_SSE_PATH, endpoint=sse_endpoint, methods=["GET"]),
        Mount(_MESSAGE_PATH, app=sse.handle_post_message),
    ]
    return Starlette(routes=routes)


class _StreamableHTTPASGIApp:
    def __init__(self, session_manager: StreamableHTTPSessionManager):
        self._session_manager = session_manager

    async def __call__(self, scope, receive, send) -> None:
        await self._session_manager.handle_request(scope, receive, send)


def streamable_http_app(server: Server | None = None):
    """Build a Starlette app serving the MCP server over Streamable HTTP."""
    from starlette.applications import Starlette
    from starlette.routing import Route

    app = server or mcp
    session_manager = StreamableHTTPSessionManager(app=app)
    asgi_app = _StreamableHTTPASGIApp(session_manager)

    @contextlib.asynccontextmanager
    async def lifespan(_: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            yield

    routes = [
        Route(_STREAMABLE_HTTP_PATH, endpoint=asgi_app),
    ]
    return Starlette(routes=routes, lifespan=lifespan)


async def run_sse_async(server: Server | None = None, mount_path: str | None = None) -> None:
    """Run the server over SSE."""
    import uvicorn

    config = uvicorn.Config(
        sse_app(server=server, mount_path=mount_path),
        host=_DEFAULT_HOST,
        port=_DEFAULT_PORT,
        log_level="info",
    )
    await uvicorn.Server(config).serve()


async def run_streamable_http_async(server: Server | None = None) -> None:
    """Run the server over Streamable HTTP."""
    import uvicorn

    config = uvicorn.Config(
        streamable_http_app(server=server),
        host=_DEFAULT_HOST,
        port=_DEFAULT_PORT,
        log_level="info",
    )
    await uvicorn.Server(config).serve()


def run(
    transport: Literal["stdio", "sse", "streamable-http"] = "stdio",
    mount_path: str | None = None,
) -> None:
    """Run the default server using the requested transport."""
    if transport == "stdio":
        anyio.run(run_stdio_async)
        return
    if transport == "sse":
        anyio.run(lambda: run_sse_async(mount_path=mount_path))
        return
    if transport == "streamable-http":
        anyio.run(run_streamable_http_async)
        return
    raise ValueError(f"Unknown transport: {transport}")


mcp = create_server()
