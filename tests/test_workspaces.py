"""Tests for workspace management tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import workspaces as ws_mod


class TestSwitchWorkspace:
    def test_down_sends_ctrl_alt_down(self) -> None:
        with patch("gnome_ui_mcp.desktop.workspaces.input") as mock_input:
            mock_input.press_key.return_value = {"success": True}
            result = ws_mod.switch_workspace(direction="down")

        assert result["success"] is True
        mock_input.press_key.assert_called()
        # Should have sent key combo for Ctrl+Alt+Down
        calls = [str(c) for c in mock_input.press_key.call_args_list]
        assert any("Down" in c for c in calls)

    def test_up_sends_ctrl_alt_up(self) -> None:
        with patch("gnome_ui_mcp.desktop.workspaces.input") as mock_input:
            mock_input.press_key.return_value = {"success": True}
            result = ws_mod.switch_workspace(direction="up")

        assert result["success"] is True
        calls = [str(c) for c in mock_input.press_key.call_args_list]
        assert any("Up" in c for c in calls)

    def test_invalid_direction_returns_error(self) -> None:
        result = ws_mod.switch_workspace(direction="sideways")
        assert result["success"] is False


class TestMoveWindowToWorkspace:
    def test_down_sends_ctrl_shift_alt_down(self) -> None:
        with patch("gnome_ui_mcp.desktop.workspaces.input") as mock_input:
            mock_input.press_key.return_value = {"success": True}
            result = ws_mod.move_window_to_workspace(direction="down")

        assert result["success"] is True
        mock_input.press_key.assert_called()

    def test_invalid_direction_returns_error(self) -> None:
        result = ws_mod.move_window_to_workspace(direction="left")
        assert result["success"] is False


class TestListWorkspaces:
    def test_returns_workspace_data(self) -> None:
        from gi.repository import GLib

        # Mock Shell.Introspect.GetWindows return
        windows = {
            1: {
                "title": GLib.Variant("s", "Terminal"),
                "app-id": GLib.Variant("s", "org.gnome.Terminal"),
                "wm-class": GLib.Variant("s", "Gnome-terminal"),
                "workspace-index": GLib.Variant("i", 0),
            },
            2: {
                "title": GLib.Variant("s", "Firefox"),
                "app-id": GLib.Variant("s", "firefox"),
                "wm-class": GLib.Variant("s", "firefox"),
                "workspace-index": GLib.Variant("i", 1),
            },
        }
        mock_result = GLib.Variant("(a{ta{sv}})", (windows,))

        with patch("gnome_ui_mcp.desktop.workspaces.Gio") as mock_gio:
            mock_bus = MagicMock()
            mock_gio.bus_get_sync.return_value = mock_bus
            mock_bus.call_sync.return_value = mock_result

            result = ws_mod.list_workspaces()

        assert result["success"] is True
        assert len(result["workspaces"]) == 2
        ws0 = [w for w in result["workspaces"] if w["index"] == 0][0]
        assert len(ws0["windows"]) == 1
        assert ws0["windows"][0]["title"] == "Terminal"


class TestToggleOverview:
    def test_sets_overview_active(self) -> None:
        with patch("gnome_ui_mcp.desktop.workspaces.Gio") as mock_gio:
            mock_bus = MagicMock()
            mock_gio.bus_get_sync.return_value = mock_bus
            mock_bus.call_sync.return_value = None

            result = ws_mod.toggle_overview(active=True)

        assert result["success"] is True
        mock_bus.call_sync.assert_called_once()
