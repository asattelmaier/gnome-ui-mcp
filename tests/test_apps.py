"""Tests for desktop app listing and launching."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import apps


def _make_app_info(
    desktop_id: str,
    name: str,
    *,
    hidden: bool = False,
    nodisplay: bool = False,
    description: str = "",
) -> MagicMock:
    mock = MagicMock()
    mock.get_id.return_value = desktop_id
    mock.get_name.return_value = name
    mock.get_description.return_value = description
    mock.get_is_hidden.return_value = hidden
    mock.get_nodisplay.return_value = nodisplay
    mock.get_executable.return_value = f"/usr/bin/{name.lower()}"
    mock.get_categories.return_value = "Utility;"
    mock.get_icon.return_value = None
    return mock


class TestListDesktopApps:
    def test_returns_visible_apps(self) -> None:
        visible = _make_app_info("calc.desktop", "Calculator")
        hidden = _make_app_info("secret.desktop", "Secret", hidden=True)
        nodisplay = _make_app_info("helper.desktop", "Helper", nodisplay=True)

        with patch.object(apps, "Gio") as mock_gio:
            mock_gio.AppInfo.get_all.return_value = [visible, hidden, nodisplay]
            result = apps.list_desktop_apps()

        assert result["success"] is True
        assert result["count"] == 1
        assert result["apps"][0]["name"] == "Calculator"

    def test_include_hidden(self) -> None:
        visible = _make_app_info("calc.desktop", "Calculator")
        hidden = _make_app_info("secret.desktop", "Secret", hidden=True)

        with patch.object(apps, "Gio") as mock_gio:
            mock_gio.AppInfo.get_all.return_value = [visible, hidden]
            result = apps.list_desktop_apps(include_hidden=True)

        assert result["count"] == 2

    def test_max_results(self) -> None:
        app_list = [_make_app_info(f"app{i}.desktop", f"App{i}") for i in range(10)]

        with patch.object(apps, "Gio") as mock_gio:
            mock_gio.AppInfo.get_all.return_value = app_list
            result = apps.list_desktop_apps(max_results=3)

        assert result["count"] == 3
        assert len(result["apps"]) == 3

    def test_search_query(self) -> None:
        calc = _make_app_info("calc.desktop", "Calculator")

        with patch.object(apps, "Gio") as mock_gio:
            mock_gio.DesktopAppInfo.search.return_value = [["calc.desktop"]]
            mock_gio.DesktopAppInfo.new.return_value = calc
            result = apps.list_desktop_apps(query="calc")

        assert result["success"] is True
        assert result["count"] == 1
        assert result["apps"][0]["name"] == "Calculator"

    def test_search_empty_results(self) -> None:
        with patch.object(apps, "Gio") as mock_gio:
            mock_gio.DesktopAppInfo.search.return_value = []
            result = apps.list_desktop_apps(query="nonexistent")

        assert result["success"] is True
        assert result["count"] == 0

    def test_empty_query_uses_get_all(self) -> None:
        app = _make_app_info("calc.desktop", "Calculator")

        with patch.object(apps, "Gio") as mock_gio:
            mock_gio.AppInfo.get_all.return_value = [app]
            result = apps.list_desktop_apps(query="")

        mock_gio.AppInfo.get_all.assert_called_once()
        assert result["count"] == 1


class TestLaunchApp:
    def test_launch_success(self) -> None:
        mock_info = MagicMock()
        mock_info.get_name.return_value = "Calculator"
        mock_info.get_executable.return_value = "/usr/bin/gnome-calculator"
        mock_info.launch.return_value = True

        with patch.object(apps, "Gio") as mock_gio:
            mock_gio.DesktopAppInfo.new.return_value = mock_info
            mock_gio.AppLaunchContext.return_value = MagicMock()
            result = apps.launch_app("org.gnome.Calculator.desktop")

        assert result["success"] is True
        assert result["name"] == "Calculator"

    def test_launch_not_found(self) -> None:
        with patch.object(apps, "Gio") as mock_gio:
            mock_gio.DesktopAppInfo.new.side_effect = TypeError("constructor returned NULL")
            result = apps.launch_app("nonexistent.desktop")

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_launch_returns_false(self) -> None:
        mock_info = MagicMock()
        mock_info.get_name.return_value = "Broken"
        mock_info.launch.return_value = False

        with patch.object(apps, "Gio") as mock_gio:
            mock_gio.DesktopAppInfo.new.return_value = mock_info
            mock_gio.AppLaunchContext.return_value = MagicMock()
            result = apps.launch_app("broken.desktop")

        assert result["success"] is False

    def test_auto_appends_desktop_suffix(self) -> None:
        mock_info = MagicMock()
        mock_info.get_name.return_value = "Calculator"
        mock_info.get_executable.return_value = "/usr/bin/calc"
        mock_info.launch.return_value = True

        with patch.object(apps, "Gio") as mock_gio:
            mock_gio.DesktopAppInfo.new.return_value = mock_info
            mock_gio.AppLaunchContext.return_value = MagicMock()
            apps.launch_app("org.gnome.Calculator")

        mock_gio.DesktopAppInfo.new.assert_called_once_with("org.gnome.Calculator.desktop")

    def test_none_icon_handled(self) -> None:
        mock_info = _make_app_info("calc.desktop", "Calculator")
        mock_info.get_icon.return_value = None

        result = apps._app_info_to_dict(mock_info)
        assert result["icon"] is None
