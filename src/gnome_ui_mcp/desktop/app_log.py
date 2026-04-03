from __future__ import annotations

import os
import select
import shlex
import shutil
import subprocess

from .types import JsonDict

_PROCESSES: dict[int, JsonDict] = {}
_READ_CHUNK = 65536


def _read_available(stream: object) -> str:
    """Read whatever bytes are available on *stream* without blocking."""
    if stream is None:
        return ""
    fd = stream.fileno()  # type: ignore[union-attr]
    chunks: list[bytes] = []
    while True:
        ready, _, _ = select.select([fd], [], [], 0)
        if not ready:
            break
        data = os.read(fd, _READ_CHUNK)
        if not data:
            break
        chunks.append(data)
    return b"".join(chunks).decode("utf-8", errors="replace")


def launch_with_logging(command: str) -> JsonDict:
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        return {"success": False, "error": f"Invalid command: {exc}"}

    if not parts:
        return {"success": False, "error": "Empty command"}

    if shutil.which(parts[0]) is None:
        return {
            "success": False,
            "error": f"Executable not found: {parts[0]}",
        }

    try:
        proc = subprocess.Popen(
            parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    _PROCESSES[proc.pid] = {"process": proc, "command": command}

    return {
        "success": True,
        "pid": proc.pid,
        "command": command,
    }


def read_app_log(pid: int, last_n_lines: int = 0) -> JsonDict:
    entry = _PROCESSES.get(pid)
    if entry is None:
        return {"success": False, "error": f"No tracked process with PID {pid}"}

    proc = entry["process"]
    running = proc.poll() is None

    stdout_data = ""
    stderr_data = ""
    try:
        if running:
            stdout_data = _read_available(proc.stdout)
            stderr_data = _read_available(proc.stderr)
        else:
            out, err = proc.communicate(timeout=5)
            stdout_data = out.decode("utf-8", errors="replace") if out else ""
            stderr_data = err.decode("utf-8", errors="replace") if err else ""
    except Exception:
        pass

    if last_n_lines > 0 and stdout_data:
        lines = stdout_data.strip().split("\n")
        stdout_data = "\n".join(lines[-last_n_lines:])
    if last_n_lines > 0 and stderr_data:
        lines = stderr_data.strip().split("\n")
        stderr_data = "\n".join(lines[-last_n_lines:])

    return {
        "success": True,
        "pid": pid,
        "command": entry["command"],
        "running": running,
        "exit_code": proc.returncode if not running else None,
        "stdout": stdout_data,
        "stderr": stderr_data,
    }
