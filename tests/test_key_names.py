"""Tests for list_key_names and get_keyboard_layout (Item 17)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import keyboard_info

_MOD = "gnome_ui_mcp.desktop.keyboard_info"


class TestListKeyNames:
    def test_navigation_keys(self) -> None:
        result = keyboard_info.list_key_names("navigation")
        assert result["success"] is True
        names = result["keys"]
        assert "Up" in names
        assert "Down" in names
        assert "Left" in names
        assert "Right" in names

    def test_function_keys(self) -> None:
        result = keyboard_info.list_key_names("function")
        assert result["success"] is True
        assert "F1" in result["keys"]
        assert "F12" in result["keys"]

    def test_modifier_keys(self) -> None:
        result = keyboard_info.list_key_names("modifier")
        assert result["success"] is True
        assert any("Control" in k or "ctrl" in k.lower() for k in result["keys"])

    def test_unknown_category(self) -> None:
        result = keyboard_info.list_key_names("nonexistent")
        assert result["success"] is False


class TestGetKeyboardLayout:
    def test_returns_layout(self) -> None:
        mock_settings = MagicMock()
        mock_settings.get_value.return_value = MagicMock()
        mock_settings.get_value.return_value.unpack.return_value = [("xkb", "us")]

        with patch(f"{_MOD}.Gio.Settings.new", return_value=mock_settings):
            result = keyboard_info.get_keyboard_layout()

        assert result["success"] is True
        assert result["layout"] == "us"

    def test_layout_with_variant(self) -> None:
        mock_settings = MagicMock()
        mock_settings.get_value.return_value = MagicMock()
        mock_settings.get_value.return_value.unpack.return_value = [("xkb", "us+dvorak")]

        with patch(f"{_MOD}.Gio.Settings.new", return_value=mock_settings):
            result = keyboard_info.get_keyboard_layout()

        assert result["success"] is True
        assert result["layout"] == "us"
        assert result["variant"] == "dvorak"

    def test_no_sources(self) -> None:
        mock_settings = MagicMock()
        mock_settings.get_value.return_value = MagicMock()
        mock_settings.get_value.return_value.unpack.return_value = []

        with patch(f"{_MOD}.Gio.Settings.new", return_value=mock_settings):
            result = keyboard_info.get_keyboard_layout()

        assert result["success"] is False

    def test_gsettings_error(self) -> None:
        with patch(f"{_MOD}.Gio.Settings.new", side_effect=Exception("GSettings unavailable")):
            result = keyboard_info.get_keyboard_layout()

        assert result["success"] is False
