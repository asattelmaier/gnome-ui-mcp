"""Tests for screen recording / GIF capture."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import screencast as sc_mod


class TestScreenRecordStart:
    def test_calls_screencast_dbus(self) -> None:
        with patch.object(sc_mod, "_get_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_get_bus.return_value = mock_bus
            from gi.repository import GLib

            mock_bus.call_sync.return_value = GLib.Variant("(bs)", (True, "/tmp/rec.mp4"))

            result = sc_mod.screen_record_start()

        assert result["success"] is True
        assert result["recording"] is True
        call_args = mock_bus.call_sync.call_args
        assert call_args.args[3] == "Screencast"

    def test_area_calls_screencast_area(self) -> None:
        with patch.object(sc_mod, "_get_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_get_bus.return_value = mock_bus
            from gi.repository import GLib

            mock_bus.call_sync.return_value = GLib.Variant("(bs)", (True, "/tmp/area.mp4"))

            result = sc_mod.screen_record_start(x=0, y=0, width=800, height=600)

        assert result["success"] is True
        call_args = mock_bus.call_sync.call_args
        assert call_args.args[3] == "ScreencastArea"

    def test_returns_path(self) -> None:
        with patch.object(sc_mod, "_get_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_get_bus.return_value = mock_bus
            from gi.repository import GLib

            mock_bus.call_sync.return_value = GLib.Variant("(bs)", (True, "/tmp/rec.mp4"))

            result = sc_mod.screen_record_start()

        assert result["path"] == "/tmp/rec.mp4"


class TestScreenRecordStop:
    def test_calls_stop_screencast(self) -> None:
        sc_mod._recording_path = "/tmp/rec.mp4"
        with patch.object(sc_mod, "_get_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_get_bus.return_value = mock_bus
            from gi.repository import GLib

            mock_bus.call_sync.return_value = GLib.Variant("(b)", (True,))

            result = sc_mod.screen_record_stop()

        assert result["success"] is True
        assert result["path"] == "/tmp/rec.mp4"

    def test_stop_without_start_returns_error(self) -> None:
        sc_mod._recording_path = None
        result = sc_mod.screen_record_stop()
        assert result["success"] is False

    def test_gif_conversion_runs_ffmpeg(self) -> None:
        sc_mod._recording_path = "/tmp/rec.mp4"
        with (
            patch.object(sc_mod, "_get_bus") as mock_get_bus,
            patch("subprocess.run") as mock_run,
        ):
            mock_bus = MagicMock()
            mock_get_bus.return_value = mock_bus
            from gi.repository import GLib

            mock_bus.call_sync.return_value = GLib.Variant("(b)", (True,))
            mock_run.return_value = MagicMock(returncode=0)

            result = sc_mod.screen_record_stop(to_gif=True)

        assert result["success"] is True
        assert "gif_path" in result
        mock_run.assert_called_once()
        cmd = mock_run.call_args.args[0]
        assert cmd[0] == "ffmpeg"

    def test_same_bus_connection_used(self) -> None:
        """Start and stop must use same D-Bus connection."""
        with patch.object(sc_mod, "_get_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_get_bus.return_value = mock_bus
            from gi.repository import GLib

            mock_bus.call_sync.side_effect = [
                GLib.Variant("(bs)", (True, "/tmp/rec.mp4")),
                GLib.Variant("(b)", (True,)),
            ]

            sc_mod.screen_record_start()
            sc_mod.screen_record_stop()

        # Both calls should use the same bus from _get_bus
        assert mock_get_bus.call_count == 2
