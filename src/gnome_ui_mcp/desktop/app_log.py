from __future__ import annotations

import shlex
import shutil
import subprocess

from .types import JsonDict

_PROCESSES: dict[int, JsonDict] = {}


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
        if proc.stdout and proc.stdout.readable():
            raw = proc.stdout.read()
            stdout_data = raw.decode("utf-8", errors="replace") if raw else ""
        if proc.stderr and proc.stderr.readable():
            raw = proc.stderr.read()
            stderr_data = raw.decode("utf-8", errors="replace") if raw else ""
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
