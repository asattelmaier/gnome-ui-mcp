"""Smoke tests verifying the MCP server loads correctly."""

from __future__ import annotations


def test_server_instance_loads() -> None:
    from gnome_ui_mcp.server import mcp

    assert mcp.name == "gnome-ui-mcp"


def test_gi_imports() -> None:
    from gnome_ui_mcp.runtime.gi_env import Atspi, Gdk, Gio, GLib

    assert Atspi is not None
    assert Gdk is not None
    assert Gio is not None
    assert GLib is not None
