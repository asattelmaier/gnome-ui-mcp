"""Close or forcefully kill applications by name."""

from __future__ import annotations

import os
import signal
import time

from . import accessibility
from . import input as input_mod
from .types import JsonDict


def _find_windows_for_app(app_name: str) -> list[JsonDict]:
    """Return windows matching *app_name* via the accessibility tree."""
    windows_result = accessibility.list_windows(app_name=app_name)
    return windows_result.get("windows", [])


def _find_pid_for_app(app_name: str) -> int | None:
    """Return the PID for an application via AT-SPI, or ``None``."""
    try:
        apps_result = accessibility.list_applications()
        for app_info in apps_result.get("applications", []):
            if app_info.get("name", "").casefold() == app_name.casefold():
                element = accessibility._resolve_element(app_info["id"])
                pid = element.get_process_id()
                if pid and pid > 0:
                    return int(pid)
    except Exception:
        pass
    return None


def close_app(app_name: str) -> JsonDict:
    """Gracefully close all windows of *app_name* by sending Alt+F4 to each."""
    windows = _find_windows_for_app(app_name)
    if not windows:
        return {
            "success": False,
            "error": f"No windows found for application {app_name!r}",
            "app_name": app_name,
        }

    closed: list[str] = []
    errors: list[str] = []
    for win in windows:
        try:
            input_mod.key_combo("alt+F4")
            closed.append(win.get("id", "unknown"))
            time.sleep(0.2)
        except Exception as exc:
            errors.append(f"{win.get('id', 'unknown')}: {exc}")

    return {
        "success": len(closed) > 0,
        "app_name": app_name,
        "closed_windows": closed,
        "errors": errors,
    }


def kill_app(app_name: str) -> JsonDict:
    """Forcefully kill *app_name*: SIGTERM first, then SIGKILL if still alive."""
    pid = _find_pid_for_app(app_name)
    if pid is None:
        return {
            "success": False,
            "error": f"Could not find PID for application {app_name!r}",
            "app_name": app_name,
        }

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return {
            "success": True,
            "app_name": app_name,
            "pid": pid,
            "signal": "already_dead",
        }
    except OSError as exc:
        return {
            "success": False,
            "error": f"Failed to send SIGTERM to PID {pid}: {exc}",
            "app_name": app_name,
            "pid": pid,
        }

    for _ in range(30):
        time.sleep(0.1)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return {
                "success": True,
                "app_name": app_name,
                "pid": pid,
                "signal": "SIGTERM",
            }
        except OSError:
            break

    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return {
            "success": True,
            "app_name": app_name,
            "pid": pid,
            "signal": "SIGTERM",
        }
    except OSError as exc:
        return {
            "success": False,
            "error": f"Failed to send SIGKILL to PID {pid}: {exc}",
            "app_name": app_name,
            "pid": pid,
        }

    return {
        "success": True,
        "app_name": app_name,
        "pid": pid,
        "signal": "SIGKILL",
    }
