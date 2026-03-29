"""Tests for monitor/display info tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import display as display_mod


def _mock_get_current_state():
    """Build a realistic GetCurrentState return value."""
    from gi.repository import GLib

    # Simplified but structurally correct mock
    # Real signature: (u serial, a((ssss)a(siiddada{sv})a{sv}) monitors,
    #                  a(iiduba(ssss)a{sv}) logical_monitors, a{sv} properties)
    monitors = [
        (
            ("HDMI-2", "ACR", "SB322QU A", "142903EBE2X00"),  # connector info
            [
                ("2560x1440@60.000", 2560, 1440, 60.0, 1.0, [1.0, 2.0], {}),  # current mode
            ],
            {
                "display-name": GLib.Variant("s", 'Acer Technologies 32"'),
                "is-builtin": GLib.Variant("b", False),
            },
        )
    ]
    logical_monitors = [
        (0, 0, 1.0, 0, True, [("HDMI-2", "ACR", "SB322QU A", "142903EBE2X00")], {}),
    ]
    return GLib.Variant(
        "(ua((ssss)a(siiddada{sv})a{sv})a(iiduba(ssss)a{sv})a{sv})",
        (1, monitors, logical_monitors, {}),
    )


class TestListMonitors:
    def test_returns_monitor_list(self) -> None:
        with patch("gnome_ui_mcp.desktop.display.Gio") as mock_gio:
            mock_bus = MagicMock()
            mock_gio.bus_get_sync.return_value = mock_bus
            mock_bus.call_sync.return_value = _mock_get_current_state()

            result = display_mod.list_monitors()

        assert result["success"] is True
        assert len(result["monitors"]) >= 1

    def test_monitor_has_required_fields(self) -> None:
        with patch("gnome_ui_mcp.desktop.display.Gio") as mock_gio:
            mock_bus = MagicMock()
            mock_gio.bus_get_sync.return_value = mock_bus
            mock_bus.call_sync.return_value = _mock_get_current_state()

            result = display_mod.list_monitors()

        monitor = result["monitors"][0]
        assert "connector" in monitor
        assert "manufacturer" in monitor
        assert "model" in monitor
        assert "resolution" in monitor
        assert "scale" in monitor
        assert "position" in monitor

    def test_resolution_format(self) -> None:
        with patch("gnome_ui_mcp.desktop.display.Gio") as mock_gio:
            mock_bus = MagicMock()
            mock_gio.bus_get_sync.return_value = mock_bus
            mock_bus.call_sync.return_value = _mock_get_current_state()

            result = display_mod.list_monitors()

        monitor = result["monitors"][0]
        assert monitor["resolution"] == "2560x1440"

    def test_position_has_x_y(self) -> None:
        with patch("gnome_ui_mcp.desktop.display.Gio") as mock_gio:
            mock_bus = MagicMock()
            mock_gio.bus_get_sync.return_value = mock_bus
            mock_bus.call_sync.return_value = _mock_get_current_state()

            result = display_mod.list_monitors()

        pos = result["monitors"][0]["position"]
        assert "x" in pos
        assert "y" in pos

    def test_is_primary_field(self) -> None:
        with patch("gnome_ui_mcp.desktop.display.Gio") as mock_gio:
            mock_bus = MagicMock()
            mock_gio.bus_get_sync.return_value = mock_bus
            mock_bus.call_sync.return_value = _mock_get_current_state()

            result = display_mod.list_monitors()

        assert result["monitors"][0]["is_primary"] is True

    def test_dbus_error_returns_failure(self) -> None:
        with patch("gnome_ui_mcp.desktop.display.Gio") as mock_gio:
            mock_bus = MagicMock()
            mock_gio.bus_get_sync.return_value = mock_bus
            mock_bus.call_sync.side_effect = RuntimeError("D-Bus not available")

            result = display_mod.list_monitors()

        assert result["success"] is False
        assert "error" in result
