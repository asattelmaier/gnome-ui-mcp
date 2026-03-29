"""Tests for app log capture."""

from __future__ import annotations

import os
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
        mock_proc.poll.return_value = None
        al_mod._PROCESSES[42] = {"process": mock_proc, "command": "test"}

        with patch.object(al_mod, "_read_available", side_effect=["line1\nline2\nline3\n", ""]):
            result = al_mod.read_app_log(42)

        assert result["success"] is True
        assert "line1" in result["stdout"]

    def test_last_n_lines(self) -> None:
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        al_mod._PROCESSES[43] = {"process": mock_proc, "command": "test"}

        with patch.object(al_mod, "_read_available", side_effect=["a\nb\nc\nd\ne\n", ""]):
            result = al_mod.read_app_log(43, last_n_lines=2)

        lines = result["stdout"].strip().split("\n")
        assert len(lines) == 2

    def test_unknown_pid_returns_error(self) -> None:
        result = al_mod.read_app_log(99999)
        assert result["success"] is False

    def test_includes_running_status(self) -> None:
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        al_mod._PROCESSES[44] = {"process": mock_proc, "command": "test"}

        with patch.object(al_mod, "_read_available", return_value=""):
            result = al_mod.read_app_log(44)

        assert result["running"] is True

    def test_running_process_does_not_block(self) -> None:
        """Reading from a running process with available data must not block."""
        read_fd, write_fd = os.pipe()
        os.write(write_fd, b"hello\n")

        mock_proc = MagicMock()
        mock_proc.stdout = os.fdopen(read_fd, "rb", buffering=0)
        mock_proc.stderr = None
        mock_proc.poll.return_value = None
        al_mod._PROCESSES[50] = {"process": mock_proc, "command": "test"}

        result = al_mod.read_app_log(50)

        assert result["success"] is True
        assert "hello" in result["stdout"]

        mock_proc.stdout.close()
        os.close(write_fd)
        del al_mod._PROCESSES[50]

    def test_finished_process_uses_communicate(self) -> None:
        """Finished processes use communicate() to read remaining output."""
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 0
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"done\n", b"err\n")
        al_mod._PROCESSES[51] = {"process": mock_proc, "command": "test"}

        result = al_mod.read_app_log(51)

        assert result["success"] is True
        assert result["running"] is False
        assert "done" in result["stdout"]
        assert "err" in result["stderr"]
        mock_proc.communicate.assert_called_once()
        del al_mod._PROCESSES[51]
