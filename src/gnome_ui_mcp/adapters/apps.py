"""Application management: list, launch, close, kill, logging.

Wraps desktop modules. Returns dataclasses and raises exceptions on
failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..desktop import app_lifecycle as _desktop_lifecycle
from ..desktop import app_log as _desktop_app_log
from ..desktop import apps as _desktop_apps


@dataclass
class DesktopApp:
    desktop_id: str
    name: str
    description: str
    executable: str
    categories: str
    icon: str | None


@dataclass
class DesktopAppList:
    apps: list[DesktopApp]
    count: int


@dataclass
class LaunchResult:
    desktop_id: str
    name: str
    executable: str


@dataclass
class LaunchWithLoggingResult:
    pid: int
    command: str


@dataclass
class AppLog:
    pid: int
    command: str
    running: bool
    exit_code: int | None
    stdout: str
    stderr: str


def list_desktop_apps(
    query: str = "",
    include_hidden: bool = False,
    max_results: int = 50,
) -> DesktopAppList:
    """List installed desktop applications. Raises on failure."""
    result = _desktop_apps.list_desktop_apps(
        query=query,
        include_hidden=include_hidden,
        max_results=max_results,
    )
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Failed to list apps")))

    apps = [
        DesktopApp(
            desktop_id=a.get("desktop_id", ""),
            name=a.get("name", ""),
            description=a.get("description", ""),
            executable=a.get("executable", ""),
            categories=a.get("categories", ""),
            icon=a.get("icon"),
        )
        for a in result.get("apps", [])
    ]
    return DesktopAppList(apps=apps, count=len(apps))


def launch_app(desktop_id: str) -> LaunchResult:
    """Launch an application by desktop ID. Raises on failure."""
    result = _desktop_apps.launch_app(desktop_id=desktop_id)
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Launch failed")))
    return LaunchResult(
        desktop_id=result.get("desktop_id", desktop_id),
        name=result.get("name", ""),
        executable=result.get("executable", ""),
    )


def launch_with_logging(command: str) -> LaunchWithLoggingResult:
    """Launch with stdout/stderr capture. Raises on failure."""
    result = _desktop_app_log.launch_with_logging(command=command)
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Launch failed")))
    return LaunchWithLoggingResult(
        pid=int(result.get("pid", 0)),
        command=result.get("command", command),
    )


def read_app_log(pid: int, last_n_lines: int = 0) -> AppLog:
    """Read stdout/stderr of a launched application. Raises on failure."""
    result = _desktop_app_log.read_app_log(pid=pid, last_n_lines=last_n_lines)
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Failed to read log")))
    return AppLog(
        pid=result.get("pid", pid),
        command=result.get("command", ""),
        running=result.get("running", False),
        exit_code=result.get("exit_code"),
        stdout=result.get("stdout", ""),
        stderr=result.get("stderr", ""),
    )


def close_app(app_name: str) -> None:
    """Gracefully close all windows of an application. Raises on failure."""
    result = _desktop_lifecycle.close_app(app_name=app_name)
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Close failed")))


def kill_app(app_name: str) -> None:
    """Forcefully kill an application. Raises on failure."""
    result = _desktop_lifecycle.kill_app(app_name=app_name)
    if result.get("success") is False:
        raise ValueError(str(result.get("error", "Kill failed")))
