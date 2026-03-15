# ruff: noqa: E402, I001

from __future__ import annotations

import warnings

import gi

gi.require_version("Atspi", "2.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Gio", "2.0")

from gi.repository import Atspi, Gdk, Gio, GLib  # type: ignore


warnings.filterwarnings("ignore", category=DeprecationWarning)

__all__ = ["Atspi", "Gdk", "Gio", "GLib"]
