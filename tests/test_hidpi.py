"""Tests for HiDPI coordinate handling and screenshot format options."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import input as input_mod


class TestGetScaleFactor:
    def test_returns_scale_from_gdk(self) -> None:
        with patch("gnome_ui_mcp.desktop.input.Gdk") as mock_gdk:
            mock_display = MagicMock()
            mock_gdk.Display.get_default.return_value = mock_display
            mock_monitor = MagicMock()
            mock_display.get_n_monitors.return_value = 1
            mock_display.get_monitor.return_value = mock_monitor
            mock_monitor.get_scale_factor.return_value = 2

            scale = input_mod.get_display_scale_factor()

        assert scale == 2

    def test_returns_1_when_no_display(self) -> None:
        with patch("gnome_ui_mcp.desktop.input.Gdk") as mock_gdk:
            mock_gdk.Display.get_default.return_value = None

            scale = input_mod.get_display_scale_factor()

        assert scale == 1


class TestScreenshotMetadata:
    def test_includes_scale_and_logical_size(self) -> None:
        with (
            patch("gnome_ui_mcp.desktop.input._screenshot_dbus") as mock_dbus,
            patch("gnome_ui_mcp.desktop.input.get_display_scale_factor", return_value=2),
            patch("gnome_ui_mcp.desktop.input.Path") as mock_path_cls,
            patch("gnome_ui_mcp.desktop.input.Image") as mock_pil,
        ):
            mock_dbus.return_value = (True, "/tmp/shot.png")
            mock_path_cls.home.return_value = MagicMock()
            mock_path = MagicMock()
            mock_path_cls.return_value = mock_path
            mock_path.expanduser.return_value = mock_path
            mock_path.resolve.return_value = mock_path
            mock_path.__str__ = lambda s: "/tmp/shot.png"

            mock_img = MagicMock()
            mock_img.size = (3840, 2160)
            mock_pil.open.return_value = mock_img

            result = input_mod.screenshot()

        assert result["success"] is True
        assert result["scale_factor"] == 2
        assert result["pixel_size"] == [3840, 2160]
        assert result["logical_size"] == [1920, 1080]


class TestScreenshotFormat:
    def test_jpeg_format_changes_extension(self) -> None:
        mock_img = MagicMock()
        mock_img.size = (200, 100)
        mock_img.mode = "RGB"

        with (
            patch("gnome_ui_mcp.desktop.input._screenshot_dbus") as mock_dbus,
            patch("gnome_ui_mcp.desktop.input.get_display_scale_factor", return_value=1),
            patch("gnome_ui_mcp.desktop.input.Image") as mock_pil,
        ):
            mock_dbus.return_value = (True, "/tmp/shot.png")
            mock_pil.open.return_value = mock_img

            result = input_mod.screenshot(output_format="jpeg", quality=85)

        assert result["success"] is True
        assert result["path"].endswith(".jpg")
        mock_img.save.assert_called_once()
        save_args = mock_img.save.call_args
        assert save_args.kwargs.get("format") == "JPEG"

    def test_scale_to_logical(self) -> None:
        mock_img = MagicMock()
        mock_img.size = (3840, 2160)
        resized = MagicMock()
        resized.size = (1920, 1080)
        mock_img.resize.return_value = resized

        with (
            patch("gnome_ui_mcp.desktop.input._screenshot_dbus") as mock_dbus,
            patch("gnome_ui_mcp.desktop.input.get_display_scale_factor", return_value=2),
            patch("gnome_ui_mcp.desktop.input.Image") as mock_pil,
        ):
            mock_dbus.return_value = (True, "/tmp/shot.png")
            mock_pil.open.return_value = mock_img
            mock_pil.Resampling.LANCZOS = 1

            result = input_mod.screenshot(scale_to_logical=True)

        # Should have called resize
        mock_img.resize.assert_called_once()
        assert result["success"] is True

    def test_max_width_resizes(self) -> None:
        mock_img = MagicMock()
        mock_img.size = (1920, 1080)
        resized = MagicMock()
        resized.size = (960, 540)
        mock_img.resize.return_value = resized

        with (
            patch("gnome_ui_mcp.desktop.input._screenshot_dbus") as mock_dbus,
            patch("gnome_ui_mcp.desktop.input.get_display_scale_factor", return_value=1),
            patch("gnome_ui_mcp.desktop.input.Image") as mock_pil,
        ):
            mock_dbus.return_value = (True, "/tmp/shot.png")
            mock_pil.open.return_value = mock_img
            mock_pil.Resampling.LANCZOS = 1

            result = input_mod.screenshot(max_width=960)

        mock_img.resize.assert_called_once()
        assert result["success"] is True


class TestClickAtCoordinateSpace:
    def test_pixel_coords_divided_by_scale(self) -> None:
        """When coordinate_space='pixel', coords should be divided by scale."""
        with (
            patch("gnome_ui_mcp.desktop.input.get_display_scale_factor", return_value=2),
            patch("gnome_ui_mcp.desktop.input._REMOTE_INPUT") as mock_remote,
        ):
            mock_remote.click_at.return_value = {
                "success": True,
                "x": 500,
                "y": 300,
                "button": "left",
                "backend": "mutter-remote-desktop",
            }

            input_mod.perform_mouse_click(1000, 600, coordinate_space="pixel")

        # Should have called with logical coords (1000/2, 600/2)
        mock_remote.click_at.assert_called_once()
        call_args = mock_remote.click_at.call_args
        assert call_args.args[0] == 500  # x
        assert call_args.args[1] == 300  # y

    def test_logical_coords_unchanged(self) -> None:
        """Default coordinate_space='logical' passes coords through."""
        with patch("gnome_ui_mcp.desktop.input._REMOTE_INPUT") as mock_remote:
            mock_remote.click_at.return_value = {
                "success": True,
                "x": 500,
                "y": 300,
                "button": "left",
                "backend": "mutter-remote-desktop",
            }

            input_mod.perform_mouse_click(500, 300)

        call_args = mock_remote.click_at.call_args
        assert call_args.args[0] == 500
        assert call_args.args[1] == 300
