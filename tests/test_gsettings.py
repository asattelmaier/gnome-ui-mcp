"""Tests for GSettings read/write tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import gsettings as gs_mod


class TestGsettingsGet:
    def test_returns_value(self) -> None:
        with patch("gnome_ui_mcp.desktop.gsettings.Gio") as mock_gio:
            mock_settings = MagicMock()
            mock_gio.Settings.return_value = mock_settings
            from gi.repository import GLib

            mock_settings.get_value.return_value = GLib.Variant("s", "prefer-dark")

            result = gs_mod.gsettings_get("org.gnome.desktop.interface", "color-scheme")

        assert result["success"] is True
        assert result["value"] == "prefer-dark"

    def test_invalid_schema_returns_error(self) -> None:
        with patch("gnome_ui_mcp.desktop.gsettings.Gio") as mock_gio:
            mock_gio.Settings.side_effect = Exception("No such schema")

            result = gs_mod.gsettings_get("org.nonexistent.schema", "key")

        assert result["success"] is False


class TestGsettingsSet:
    def test_set_string(self) -> None:
        with patch("gnome_ui_mcp.desktop.gsettings.Gio") as mock_gio:
            mock_settings = MagicMock()
            mock_gio.Settings.return_value = mock_settings
            from gi.repository import GLib

            mock_settings.get_value.return_value = GLib.Variant("s", "prefer-dark")
            mock_settings.set_value.return_value = True

            result = gs_mod.gsettings_set("org.gnome.desktop.interface", "color-scheme", "default")

        assert result["success"] is True
        mock_settings.set_value.assert_called_once()


class TestGsettingsListKeys:
    def test_returns_key_list(self) -> None:
        with patch("gnome_ui_mcp.desktop.gsettings.Gio") as mock_gio:
            mock_source = MagicMock()
            mock_gio.SettingsSchemaSource.get_default.return_value = mock_source
            mock_schema = MagicMock()
            mock_source.lookup.return_value = mock_schema
            mock_schema.list_keys.return_value = ["color-scheme", "gtk-theme", "icon-theme"]

            result = gs_mod.gsettings_list_keys("org.gnome.desktop.interface")

        assert result["success"] is True
        assert "color-scheme" in result["keys"]

    def test_invalid_schema_returns_error(self) -> None:
        with patch("gnome_ui_mcp.desktop.gsettings.Gio") as mock_gio:
            mock_source = MagicMock()
            mock_gio.SettingsSchemaSource.get_default.return_value = mock_source
            mock_source.lookup.return_value = None

            result = gs_mod.gsettings_list_keys("org.nonexistent")

        assert result["success"] is False


class TestGsettingsReset:
    def test_resets_key(self) -> None:
        with patch("gnome_ui_mcp.desktop.gsettings.Gio") as mock_gio:
            mock_settings = MagicMock()
            mock_gio.Settings.return_value = mock_settings

            result = gs_mod.gsettings_reset("org.gnome.desktop.interface", "color-scheme")

        assert result["success"] is True
        mock_settings.reset.assert_called_once_with("color-scheme")
