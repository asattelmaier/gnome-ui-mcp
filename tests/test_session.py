"""Tests for isolated GNOME session management."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import session as session_mod


class TestSessionStart:
    def setup_method(self) -> None:
        session_mod._session = None

    def test_starts_gnome_shell_headless(self) -> None:
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_proc.poll.return_value = None
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.fileno.return_value = 3

        with (
            patch("subprocess.Popen", return_value=mock_proc) as mock_popen,
            patch.object(session_mod, "_wait_for_shell_ready", return_value=True),
            patch.object(
                session_mod,
                "_extract_bus_address",
                return_value="unix:path=/tmp/test-bus",
            ),
        ):
            result = session_mod.session_start(width=1920, height=1080)

        assert result["success"] is True
        assert result["pid"] == 12345
        cmd = mock_popen.call_args.args[0]
        assert "dbus-run-session" in cmd
        assert "--headless" in cmd
        assert "--virtual-monitor" in cmd

    def test_custom_resolution(self) -> None:
        mock_proc = MagicMock()
        mock_proc.pid = 99
        mock_proc.poll.return_value = None
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.fileno.return_value = 3

        with (
            patch("subprocess.Popen", return_value=mock_proc),
            patch.object(session_mod, "_wait_for_shell_ready", return_value=True),
            patch.object(
                session_mod,
                "_extract_bus_address",
                return_value="unix:path=/tmp/bus",
            ),
        ):
            result = session_mod.session_start(width=2560, height=1440)

        assert result["success"] is True
        assert result["width"] == 2560
        assert result["height"] == 1440

    def test_already_running_returns_info(self) -> None:
        session_mod._session = {
            "process": MagicMock(poll=MagicMock(return_value=None)),
            "pid": 111,
            "bus_address": "unix:path=/tmp/bus",
            "width": 1920,
            "height": 1080,
        }

        result = session_mod.session_start()

        assert result["success"] is True
        assert result["already_running"] is True
        session_mod._session = None


class TestSessionStop:
    def test_stops_running_session(self) -> None:
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        session_mod._session = {
            "process": mock_proc,
            "pid": 42,
            "bus_address": "unix:path=/tmp/bus",
            "width": 1920,
            "height": 1080,
        }

        result = session_mod.session_stop()

        assert result["success"] is True
        mock_proc.terminate.assert_called_once()
        assert session_mod._session is None

    def test_stop_when_not_running(self) -> None:
        session_mod._session = None
        result = session_mod.session_stop()
        assert result["success"] is True
        assert result.get("already_stopped") is True


class TestSessionInfo:
    def test_returns_session_details(self) -> None:
        session_mod._session = {
            "process": MagicMock(poll=MagicMock(return_value=None)),
            "pid": 55,
            "bus_address": "unix:path=/tmp/bus",
            "width": 1920,
            "height": 1080,
        }

        result = session_mod.session_info()

        assert result["success"] is True
        assert result["running"] is True
        assert result["pid"] == 55
        session_mod._session = None

    def test_no_session_returns_not_running(self) -> None:
        session_mod._session = None
        result = session_mod.session_info()
        assert result["running"] is False
