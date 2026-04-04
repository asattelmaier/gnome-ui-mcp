"""Application management tools."""

from __future__ import annotations

from ..adapters import apps
from ..formatters.apps_formatter import DesktopAppListFormatter
from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory
from .tool_definition import ToolRequest, define_tool

# -- list_desktop_apps --


def _list_desktop_apps(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    query = request.params.get("query", "")
    include_hidden = request.params.get("include_hidden", False)
    max_results = request.params.get("max_results", 50)
    result = apps.list_desktop_apps(
        query=query,
        include_hidden=include_hidden,
        max_results=max_results,
    )
    fmt = DesktopAppListFormatter(result)
    response.set_items("apps", fmt.to_json())
    response.set_data("count", result.count)
    response.append_text(fmt.to_string())


list_desktop_apps = define_tool(
    name="list_desktop_apps",
    description="List installed desktop applications.",
    handler=_list_desktop_apps,
    category=ToolCategory.APPS,
    parameters={
        "query": {
            "type": "string",
            "default": "",
            "description": "Search query to filter applications.",
        },
        "include_hidden": {
            "type": "boolean",
            "default": False,
            "description": "Include hidden applications.",
        },
        "max_results": {
            "type": "integer",
            "default": 50,
            "description": "Maximum number of results to return.",
        },
    },
)


# -- launch_app --


def _launch_app(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    desktop_id = request.params.get("desktop_id", "")
    result = apps.launch_app(desktop_id=desktop_id)
    response.set_data("desktop_id", result.desktop_id)
    response.set_data("name", result.name)
    response.set_data("executable", result.executable)
    response.append_text(f"Launched application: {desktop_id}")


launch_app = define_tool(
    name="launch_app",
    description="Launch an application by desktop ID.",
    handler=_launch_app,
    category=ToolCategory.APPS,
    read_only=False,
    parameters={
        "desktop_id": {
            "type": "string",
            "description": "Desktop file ID (e.g. org.gnome.Calculator.desktop).",
        },
    },
)


# -- launch_with_logging --


def _launch_with_logging(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    command = request.params.get("command", "")
    result = apps.launch_with_logging(command=command)
    response.set_data("pid", result.pid)
    response.set_data("command", result.command)
    response.append_text(f"Launched '{command}' with PID {result.pid}.")


launch_with_logging = define_tool(
    name="launch_with_logging",
    description=(
        "Launch an application with stdout/stderr capture. "
        "Warning: executes the specified command on the host system."
    ),
    handler=_launch_with_logging,
    category=ToolCategory.APPS,
    read_only=False,
    parameters={
        "command": {
            "type": "string",
            "description": "Command to execute.",
        },
    },
)


# -- read_app_log --


def _read_app_log(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    pid = request.params.get("pid", 0)
    last_n_lines = request.params.get("last_n_lines", 0)
    result = apps.read_app_log(pid=pid, last_n_lines=last_n_lines)
    response.set_data("pid", result.pid)
    response.set_data("command", result.command)
    response.set_data("running", result.running)
    response.set_data("exit_code", result.exit_code)
    response.set_data("stdout", result.stdout)
    response.set_data("stderr", result.stderr)
    response.append_text(f"Read log for PID {pid}.")


read_app_log = define_tool(
    name="read_app_log",
    description="Read stdout/stderr of a launched application by PID.",
    handler=_read_app_log,
    category=ToolCategory.APPS,
    parameters={
        "pid": {"type": "integer", "description": "Process ID."},
        "last_n_lines": {
            "type": "integer",
            "default": 0,
            "description": "Number of lines from the end (0 = all).",
        },
    },
)


# -- close_app --


def _close_app(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    app_name = request.params.get("app_name", "")
    apps.close_app(app_name=app_name)
    response.append_text(f"Closed application: {app_name}")


close_app = define_tool(
    name="close_app",
    description="Gracefully close all windows of an application by sending Alt+F4.",
    handler=_close_app,
    category=ToolCategory.APPS,
    read_only=False,
    parameters={
        "app_name": {
            "type": "string",
            "description": "Application name to close.",
        },
    },
)


# -- kill_app --


def _kill_app(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    app_name = request.params.get("app_name", "")
    apps.kill_app(app_name=app_name)
    response.append_text(f"Killed application: {app_name}")


kill_app = define_tool(
    name="kill_app",
    description=(
        "Forcefully kill an application by PID. Sends SIGTERM first, then SIGKILL if still alive."
    ),
    handler=_kill_app,
    category=ToolCategory.APPS,
    read_only=False,
    parameters={
        "app_name": {
            "type": "string",
            "description": "Application name to kill.",
        },
    },
)
