"""Tests for launch_with_logging command validation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import app_log as al_mod


class TestLaunchCommandValidation:
    """launch_with_logging should validate the executable exists."""

    def test_valid_executable_works(self) -> None:
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        with (
            patch("subprocess.Popen", return_value=mock_proc),
            patch("shutil.which", return_value="/usr/bin/echo"),
        ):
            result = al_mod.launch_with_logging("echo hello")

        assert result["success"] is True
        assert result["pid"] == 12345

    def test_nonexistent_executable_returns_error(self) -> None:
        with patch("shutil.which", return_value=None):
            result = al_mod.launch_with_logging("nonexistent_program_xyz arg1")

        assert result["success"] is False
        assert "not found" in result["error"].lower() or "executable" in result["error"].lower()
