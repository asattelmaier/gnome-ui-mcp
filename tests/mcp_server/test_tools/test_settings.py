"""Tests for settings tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.adapters.dbus import DbusCallResult
from gnome_ui_mcp.adapters.keyboard import KeyboardLayout
from gnome_ui_mcp.adapters.monitor import MonitorGeometry, MonitorInfo
from gnome_ui_mcp.mcp_context import McpContext
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.tools import settings
from gnome_ui_mcp.tools.tool_definition import ToolRequest


@pytest.fixture()
def ctx() -> McpContext:
    return MagicMock(spec=McpContext)


class TestGetKeyboardLayout:
    @patch("gnome_ui_mcp.adapters.keyboard.get_keyboard_layout")
    def test_returns_layout_via_formatter(self, mock_kl, ctx) -> None:
        mock_kl.return_value = KeyboardLayout(
            layout="de",
            variant="nodeadkeys",
            source_type="xkb",
            all_sources=[("xkb", "de+nodeadkeys")],
        )
        response = McpResponse()
        settings._get_keyboard_layout(ToolRequest({}), response, ctx)

        structured = response.to_tool_result().structuredContent
        assert structured["layout"] == "de"
        assert structured["variant"] == "nodeadkeys"
        assert "de" in response.text_lines[0]


class TestListKeyNames:
    @patch("gnome_ui_mcp.adapters.keyboard.list_key_names")
    def test_returns_keys_via_formatter(self, mock_ln, ctx) -> None:
        mock_ln.return_value = ("navigation", ["Up", "Down", "Left", "Right"])
        response = McpResponse()
        settings._list_key_names(ToolRequest({"category": "navigation"}), response, ctx)

        structured = response.to_tool_result().structuredContent
        assert structured["category"] == "navigation"
        assert len(structured["keys"]) == 4
        assert "4 keys" in response.text_lines[0]

    @patch("gnome_ui_mcp.adapters.keyboard.list_key_names")
    def test_invalid_category_raises(self, mock_ln, ctx) -> None:
        mock_ln.side_effect = ValueError("Unknown category")
        response = McpResponse()
        with pytest.raises(ValueError, match="Unknown category"):
            settings._list_key_names(ToolRequest({"category": "bogus"}), response, ctx)


class TestGetMonitorForPoint:
    @patch("gnome_ui_mcp.adapters.monitor.get_monitor_for_point")
    def test_returns_monitor_via_formatter(self, mock_mp, ctx) -> None:
        mock_mp.return_value = MonitorInfo(
            index=0,
            model="DELL U2720Q",
            geometry=MonitorGeometry(x=0, y=0, width=3840, height=2160),
        )
        response = McpResponse()
        settings._get_monitor_for_point(ToolRequest({"x": 100, "y": 200}), response, ctx)

        structured = response.to_tool_result().structuredContent
        assert structured["index"] == 0
        assert structured["model"] == "DELL U2720Q"
        assert structured["geometry"]["width"] == 3840
        assert "DELL U2720Q" in response.text_lines[0]

    @patch("gnome_ui_mcp.adapters.monitor.get_monitor_for_point")
    def test_point_outside_raises(self, mock_mp, ctx) -> None:
        mock_mp.side_effect = ValueError("not contained in any monitor")
        response = McpResponse()
        with pytest.raises(ValueError, match="not contained"):
            settings._get_monitor_for_point(ToolRequest({"x": 9999, "y": 9999}), response, ctx)


class TestWaylandProtocols:
    @patch("gnome_ui_mcp.adapters.wayland.list_protocols")
    def test_returns_protocols_via_formatter(self, mock_wp, ctx) -> None:
        mock_wp.return_value = ["wl_compositor", "xdg_shell", "wp_viewporter"]
        response = McpResponse()
        settings._wayland_protocols(ToolRequest({}), response, ctx)

        structured = response.to_tool_result().structuredContent
        assert structured["protocol_count"] == 3
        assert "wl_compositor" in structured["protocols"]
        assert "3 Wayland protocols" in response.text_lines[0]


class TestGsettingsGet:
    @patch("gnome_ui_mcp.adapters.gsettings.gsettings_get")
    def test_get_success(self, mock_get, ctx) -> None:
        mock_get.return_value = "dark"
        response = McpResponse()
        settings._gsettings_get(
            ToolRequest({"schema": "org.gnome.desktop", "key": "theme"}), response, ctx
        )

        structured = response.to_tool_result().structuredContent
        assert structured["value"] == "dark"


class TestGsettingsSet:
    @patch("gnome_ui_mcp.adapters.gsettings.gsettings_set")
    def test_set_success(self, mock_set, ctx) -> None:
        response = McpResponse()
        settings._gsettings_set(
            ToolRequest({"schema": "org.gnome.desktop", "key": "theme", "value": "dark"}),
            response,
            ctx,
        )

        assert "Set" in response.text_lines[0]


class TestGsettingsListKeys:
    @patch("gnome_ui_mcp.adapters.gsettings.gsettings_list_keys")
    def test_list_keys(self, mock_list, ctx) -> None:
        mock_list.return_value = ["theme", "font-name"]
        response = McpResponse()
        settings._gsettings_list_keys(ToolRequest({"schema": "org.gnome.desktop"}), response, ctx)

        structured = response.to_tool_result().structuredContent
        assert len(structured["keys"]) == 2


class TestDbusCall:
    @patch("gnome_ui_mcp.adapters.dbus.dbus_call")
    def test_dbus_call(self, mock_dbus, ctx) -> None:
        mock_dbus.return_value = DbusCallResult(
            bus_name="org.gnome.Shell",
            object_path="/org/gnome/Shell",
            interface="org.gnome.Shell",
            method="Eval",
            value="42",
        )
        response = McpResponse()
        settings._dbus_call(
            ToolRequest(
                {
                    "bus_name": "org.gnome.Shell",
                    "object_path": "/org/gnome/Shell",
                    "interface": "org.gnome.Shell",
                    "method": "Eval",
                }
            ),
            response,
            ctx,
        )

        structured = response.to_tool_result().structuredContent
        assert structured["value"] == "42"


class TestListMonitors:
    @patch("gnome_ui_mcp.adapters.display.list_monitors")
    def test_list_monitors(self, mock_lm, ctx) -> None:
        mock_lm.return_value = [{"connector": "DP-1"}]
        response = McpResponse()
        settings._list_monitors(ToolRequest({}), response, ctx)

        structured = response.to_tool_result().structuredContent
        assert structured["monitor_count"] == 1
