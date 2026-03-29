"""Tests for get_monitor_for_point (Item 18)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import monitor_point

_MOD = "gnome_ui_mcp.desktop.monitor_point"


def _make_monitor(x: int, y: int, w: int, h: int) -> MagicMock:
    monitor = MagicMock()
    geom = MagicMock()
    geom.x = x
    geom.y = y
    geom.width = w
    geom.height = h
    monitor.get_geometry.return_value = geom
    monitor.get_model.return_value = f"Monitor-{x}"
    return monitor


class TestGetMonitorForPoint:
    def test_point_in_first_monitor(self) -> None:
        m0 = _make_monitor(0, 0, 1920, 1080)
        m1 = _make_monitor(1920, 0, 2560, 1440)
        display = MagicMock()
        display.get_n_monitors.return_value = 2
        display.get_monitor.side_effect = lambda i: [m0, m1][i]

        with patch(f"{_MOD}.Gdk.Display.get_default", return_value=display):
            result = monitor_point.get_monitor_for_point(500, 500)

        assert result["success"] is True
        assert result["monitor_index"] == 0
        assert result["geometry"]["x"] == 0
        assert result["geometry"]["width"] == 1920

    def test_point_outside_all_monitors(self) -> None:
        m0 = _make_monitor(0, 0, 1920, 1080)
        display = MagicMock()
        display.get_n_monitors.return_value = 1
        display.get_monitor.side_effect = lambda i: [m0][i]

        with patch(f"{_MOD}.Gdk.Display.get_default", return_value=display):
            result = monitor_point.get_monitor_for_point(5000, 5000)

        assert result["success"] is False
