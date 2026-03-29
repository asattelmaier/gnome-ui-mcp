"""Isolated GNOME session management via gnome-shell --headless."""

from __future__ import annotations

import os
import select
import shutil
import subprocess
import time
from typing import Any

JsonDict = dict[str, Any]

_session: JsonDict | None = None


def _wait_for_shell_ready(proc: subprocess.Popen, timeout: float = 10.0) -> bool:
    """Wait for gnome-shell to emit 'GNOME Shell started' on stderr."""
    deadline = time.monotonic() + timeout
    fd = proc.stderr.fileno()
    buf = b""

    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False
        ready, _, _ = select.select([fd], [], [], 0.5)
        if ready:
            chunk = os.read(fd, 4096)
            if not chunk:
                continue
            buf += chunk
            if b"GNOME Shell started" in buf:
                return True
    return False


def _extract_bus_address(proc: subprocess.Popen) -> str | None:
    """Extract DBUS_SESSION_BUS_ADDRESS from the process environment."""
    try:
        environ_path = f"/proc/{proc.pid}/environ"
        with open(environ_path, "rb") as f:
            environ = f.read()
        for entry in environ.split(b"\0"):
            if entry.startswith(b"DBUS_SESSION_BUS_ADDRESS="):
                return entry.split(b"=", 1)[1].decode("utf-8")
    except Exception:
        pass
    return None


def session_start(
    width: int = 1920,
    height: int = 1080,
) -> JsonDict:
    global _session

    if _session is not None:
        proc = _session["process"]
        if proc.poll() is None:
            return {
                "success": True,
                "already_running": True,
                "pid": _session["pid"],
                "bus_address": _session["bus_address"],
                "width": _session["width"],
                "height": _session["height"],
            }
        _session = None

    if not shutil.which("gnome-shell"):
        return {"success": False, "error": "gnome-shell not found"}
    if not shutil.which("dbus-run-session"):
        return {"success": False, "error": "dbus-run-session not found"}

    cmd = [
        "dbus-run-session",
        "--",
        "gnome-shell",
        "--headless",
        "--virtual-monitor",
        f"{width}x{height}",
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env={**os.environ, "MUTTER_DEBUG_DUMMY_MODE_SPECS": f"{width}x{height}"},
        )
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    if not _wait_for_shell_ready(proc):
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        return {
            "success": False,
            "error": "gnome-shell --headless did not start within timeout",
        }

    bus_address = _extract_bus_address(proc)

    _session = {
        "process": proc,
        "pid": proc.pid,
        "bus_address": bus_address,
        "width": width,
        "height": height,
    }

    return {
        "success": True,
        "pid": proc.pid,
        "bus_address": bus_address,
        "width": width,
        "height": height,
    }


def session_stop() -> JsonDict:
    global _session

    if _session is None:
        return {"success": True, "already_stopped": True}

    proc = _session["process"]
    pid = _session["pid"]
    _session = None

    if proc.poll() is not None:
        return {"success": True, "pid": pid, "already_exited": True}

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)

    return {"success": True, "pid": pid, "stopped": True}


def session_info() -> JsonDict:
    if _session is None:
        return {"success": True, "running": False}

    proc = _session["process"]
    running = proc.poll() is None

    return {
        "success": True,
        "running": running,
        "pid": _session["pid"],
        "bus_address": _session["bus_address"],
        "width": _session["width"],
        "height": _session["height"],
    }
