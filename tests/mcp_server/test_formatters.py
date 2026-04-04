"""Tests for formatters."""

from __future__ import annotations

from gnome_ui_mcp.adapters.accessibility import AppInfo, WindowInfo
from gnome_ui_mcp.adapters.keyboard import KeyboardLayout
from gnome_ui_mcp.adapters.monitor import MonitorGeometry, MonitorInfo
from gnome_ui_mcp.formatters.accessibility_formatter import (
    ApplicationListFormatter,
    WindowListFormatter,
)
from gnome_ui_mcp.formatters.settings_formatter import (
    KeyboardLayoutFormatter,
    KeyListFormatter,
    MonitorFormatter,
    ProtocolListFormatter,
)


class TestApplicationListFormatter:
    def test_to_string_with_apps(self) -> None:
        apps = [
            AppInfo(id="0", name="Firefox", role="application", children=2),
            AppInfo(id="1", name="Terminal", role="application", children=1),
        ]
        fmt = ApplicationListFormatter(apps)
        text = fmt.to_string()
        assert "2 applications" in text
        assert "Firefox" in text

    def test_to_string_empty(self) -> None:
        fmt = ApplicationListFormatter([])
        assert "No applications found" in fmt.to_string()

    def test_to_json(self) -> None:
        apps = [AppInfo(id="0", name="Firefox", role="application", children=2)]
        result = ApplicationListFormatter(apps).to_json()
        assert result[0]["name"] == "Firefox"


class TestWindowListFormatter:
    def test_to_string_with_windows(self) -> None:
        windows = [
            WindowInfo(id="0/0", name="Doc", role="frame", application="Firefox"),
        ]
        fmt = WindowListFormatter(windows)
        assert "1 windows" in fmt.to_string()
        assert "Firefox" in fmt.to_string()

    def test_to_string_empty(self) -> None:
        assert "No windows found" in WindowListFormatter([]).to_string()

    def test_to_json(self) -> None:
        windows = [
            WindowInfo(id="0/0", name="Doc", role="frame", application="Firefox"),
        ]
        result = WindowListFormatter(windows).to_json()
        assert result[0]["application"] == "Firefox"


class TestKeyboardLayoutFormatter:
    def test_to_string(self) -> None:
        layout = KeyboardLayout(
            layout="de",
            variant="nodeadkeys",
            source_type="xkb",
            all_sources=[],
        )
        text = KeyboardLayoutFormatter(layout).to_string()
        assert "de" in text
        assert "nodeadkeys" in text

    def test_to_json(self) -> None:
        layout = KeyboardLayout(
            layout="us",
            variant=None,
            source_type="xkb",
            all_sources=[("xkb", "us")],
        )
        result = KeyboardLayoutFormatter(layout).to_json()
        assert result["layout"] == "us"
        assert result["variant"] is None


class TestKeyListFormatter:
    def test_to_string(self) -> None:
        text = KeyListFormatter("navigation", ["Up", "Down"]).to_string()
        assert "navigation" in text
        assert "2 keys" in text

    def test_to_json(self) -> None:
        result = KeyListFormatter("editing", ["Return"]).to_json()
        assert result["category"] == "editing"
        assert result["keys"] == ["Return"]


class TestMonitorFormatter:
    def test_to_string(self) -> None:
        info = MonitorInfo(
            index=0,
            model="DELL",
            geometry=MonitorGeometry(x=0, y=0, width=1920, height=1080),
        )
        text = MonitorFormatter(info).to_string()
        assert "DELL" in text
        assert "1920x1080" in text

    def test_to_json(self) -> None:
        info = MonitorInfo(
            index=1,
            model="LG",
            geometry=MonitorGeometry(x=1920, y=0, width=2560, height=1440),
        )
        result = MonitorFormatter(info).to_json()
        assert result["index"] == 1
        assert result["geometry"]["width"] == 2560


class TestProtocolListFormatter:
    def test_to_string(self) -> None:
        text = ProtocolListFormatter(["wl_compositor", "xdg_shell"]).to_string()
        assert "2 Wayland protocols" in text

    def test_to_json(self) -> None:
        result = ProtocolListFormatter(["wl_compositor"]).to_json()
        assert result["protocols"] == ["wl_compositor"]
        assert result["protocol_count"] == 1
