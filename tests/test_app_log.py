"""Tests for app log capture."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import app_log as al_mod


class TestLaunchWithLogging:
    def test_returns_pid(self) -> None:
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        with patch("subprocess.Popen", return_value=mock_proc):
            result = al_mod.launch_with_logging("gnome-calculator")

        assert result["success"] is True
        assert result["pid"] == 12345

    def test_stores_process(self) -> None:
        mock_proc = MagicMock()
        mock_proc.pid = 99
        with patch("subprocess.Popen", return_value=mock_proc):
            al_mod.launch_with_logging("echo hello")

        assert 99 in al_mod._PROCESSES


class TestReadAppLog:
    def test_reads_stdout(self) -> None:
        mock_proc = MagicMock()
        mock_proc.stdout = MagicMock()
        mock_proc.stdout.readable.return_value = True
        mock_proc.stdout.read.return_value = b"line1\nline2\nline3\n"
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.readable.return_value = True
        mock_proc.stderr.read.return_value = b""
        mock_proc.poll.return_value = None
        al_mod._PROCESSES[42] = {"process": mock_proc, "command": "test"}

        result = al_mod.read_app_log(42)

        assert result["success"] is True
        assert "line1" in result["stdout"]

    def test_last_n_lines(self) -> None:
        mock_proc = MagicMock()
        mock_proc.stdout = MagicMock()
        mock_proc.stdout.readable.return_value = True
        mock_proc.stdout.read.return_value = b"a\nb\nc\nd\ne\n"
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.readable.return_value = True
        mock_proc.stderr.read.return_value = b""
        mock_proc.poll.return_value = None
        al_mod._PROCESSES[43] = {"process": mock_proc, "command": "test"}

        result = al_mod.read_app_log(43, last_n_lines=2)

        lines = result["stdout"].strip().split("\n")
        assert len(lines) == 2

    def test_unknown_pid_returns_error(self) -> None:
        result = al_mod.read_app_log(99999)
        assert result["success"] is False

    def test_includes_running_status(self) -> None:
        mock_proc = MagicMock()
        mock_proc.stdout = MagicMock()
        mock_proc.stdout.readable.return_value = True
        mock_proc.stdout.read.return_value = b""
        mock_proc.stderr = MagicMock()
        mock_proc.stderr.readable.return_value = True
        mock_proc.stderr.read.return_value = b""
        mock_proc.poll.return_value = None
        al_mod._PROCESSES[44] = {"process": mock_proc, "command": "test"}

        result = al_mod.read_app_log(44)

        assert result["running"] is True
