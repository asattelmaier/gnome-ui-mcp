"""Wayland protocol info."""

from __future__ import annotations

import subprocess


def list_protocols(filter_protocol: str | None = None) -> list[str]:
    """Return Wayland protocol names. Raises on failure."""
    try:
        result = subprocess.run(
            ["wayland-info", "--interface"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except FileNotFoundError as exc:
        msg = "wayland-info not found. Install wayland-utils."
        raise RuntimeError(msg) from exc

    if result.returncode != 0:
        msg = f"wayland-info exited with code {result.returncode}"
        raise RuntimeError(msg)

    protocols = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]

    if filter_protocol:
        protocols = [p for p in protocols if filter_protocol.lower() in p.lower()]

    return protocols
