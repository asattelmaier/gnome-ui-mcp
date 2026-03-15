#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import GLib, Gtk  # type: ignore


FLAG_FILE = Path("/tmp/gnome-ui-mcp-smoke-test-clicked")
WINDOW_TITLE = "GNOME UI MCP Smoke Test"
STATUS_IDLE = "Smoke test waiting for click"
STATUS_DONE = "Smoke test clicked"
BUTTON_LABEL = "Smoke Test Button"


class SmokeTestWindow(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title=WINDOW_TITLE)
        self.set_border_width(16)
        self.set_default_size(360, 140)
        self.connect("destroy", Gtk.main_quit)

        wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(wrapper)

        header = Gtk.Label(label="GNOME UI MCP click smoke test")
        header.set_xalign(0)
        wrapper.pack_start(header, False, False, 0)

        self.status_label = Gtk.Label(label=STATUS_IDLE)
        self.status_label.set_xalign(0)
        wrapper.pack_start(self.status_label, False, False, 0)

        button = Gtk.Button(label=BUTTON_LABEL)
        button.connect("clicked", self.on_clicked)
        wrapper.pack_start(button, False, False, 0)

    def on_clicked(self, _button: Gtk.Button) -> None:
        self.status_label.set_text(STATUS_DONE)
        self.set_title(f"{WINDOW_TITLE} - clicked")
        FLAG_FILE.write_text("clicked\n", encoding="utf-8")


def main() -> None:
    GLib.set_prgname("gnome-ui-mcp-smoke-test")
    FLAG_FILE.unlink(missing_ok=True)

    window = SmokeTestWindow()
    window.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
