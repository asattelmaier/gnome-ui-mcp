"""Tests for close_app and kill_app in app_lifecycle module."""

from __future__ import annotations

from unittest.mock import patch

from gnome_ui_mcp.desktop import app_lifecycle


class TestCloseApp:
    def test_close_sends_alt_f4_for_each_window(self) -> None:
        fake_windows = [{"id": "0/0"}, {"id": "0/1"}]
        with (
            patch.object(
                app_lifecycle,
                "_find_windows_for_app",
                return_value=fake_windows,
            ),
            patch.object(app_lifecycle.input_mod, "key_combo") as mock_combo,
        ):
            result = app_lifecycle.close_app("Firefox")

        assert result["success"] is True
        assert len(result["closed_windows"]) == 2
        assert mock_combo.call_count == 2
        mock_combo.assert_called_with("alt+F4")

    def test_close_no_windows_returns_error(self) -> None:
        with patch.object(
            app_lifecycle,
            "_find_windows_for_app",
            return_value=[],
        ):
            result = app_lifecycle.close_app("NonExistent")

        assert result["success"] is False
        assert "No windows found" in result["error"]


class TestKillApp:
    def test_kill_sigterm_success(self) -> None:
        with (
            patch.object(app_lifecycle, "_find_pid_for_app", return_value=12345),
            patch("os.kill") as mock_kill,
        ):
            # First call is SIGTERM, second call (os.kill(pid, 0)) raises ProcessLookupError
            mock_kill.side_effect = [None, ProcessLookupError()]
            result = app_lifecycle.kill_app("Firefox")

        assert result["success"] is True
        assert result["pid"] == 12345
        assert result["signal"] == "SIGTERM"

    def test_kill_escalates_to_sigkill(self) -> None:
        call_count = 0

        def side_effect(pid: int, sig: int) -> None:
            nonlocal call_count
            call_count += 1
            if sig == 0:
                # Process still alive during all checks
                return None
            if sig == 9:
                # SIGKILL succeeds
                return None
            # SIGTERM succeeds (doesn't raise)
            return None

        with (
            patch.object(app_lifecycle, "_find_pid_for_app", return_value=99),
            patch("os.kill", side_effect=side_effect),
            patch("time.sleep"),
        ):
            result = app_lifecycle.kill_app("Stuck")

        assert result["success"] is True
        assert result["signal"] == "SIGKILL"

    def test_kill_no_pid_returns_error(self) -> None:
        with patch.object(app_lifecycle, "_find_pid_for_app", return_value=None):
            result = app_lifecycle.kill_app("Ghost")

        assert result["success"] is False
        assert "Could not find PID" in result["error"]
