"""Tests for clipboard_read/clipboard_write with mime_type parameter."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import input as input_mod


class TestClipboardReadMime:
    def test_read_custom_mime_text(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "<html>hello</html>"
        with (
            patch("shutil.which", return_value="/usr/bin/wl-paste"),
            patch.object(subprocess, "run", return_value=mock_result) as mock_run,
        ):
            result = input_mod.clipboard_read(mime_type="text/html")

        cmd = mock_run.call_args.args[0]
        assert "--type" in cmd
        idx = cmd.index("--type")
        assert cmd[idx + 1] == "text/html"
        assert result["success"] is True
        assert result["text"] == "<html>hello</html>"
        assert result["mime_type"] == "text/html"

    def test_read_binary_mime_returns_base64(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"\x89PNG\r\n\x1a\n"
        with (
            patch("shutil.which", return_value="/usr/bin/wl-paste"),
            patch.object(subprocess, "run", return_value=mock_result) as mock_run,
        ):
            result = input_mod.clipboard_read(mime_type="image/png")

        # Should use text=False for binary
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs.get("text") is False
        assert result["success"] is True
        assert "data_base64" in result
        assert result["data_length"] == 8
        assert result["mime_type"] == "image/png"

    def test_read_default_mime_is_text_plain(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello"
        with (
            patch("shutil.which", return_value="/usr/bin/wl-paste"),
            patch.object(subprocess, "run", return_value=mock_result) as mock_run,
        ):
            result = input_mod.clipboard_read()

        cmd = mock_run.call_args.args[0]
        assert "text/plain" in cmd
        assert result["mime_type"] == "text/plain"


class TestClipboardWriteMime:
    def test_write_custom_mime_text(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        with (
            patch("shutil.which", return_value="/usr/bin/wl-copy"),
            patch.object(subprocess, "run", return_value=mock_result) as mock_run,
        ):
            result = input_mod.clipboard_write("<b>bold</b>", mime_type="text/html")

        cmd = mock_run.call_args.args[0]
        assert "--type" in cmd
        idx = cmd.index("--type")
        assert cmd[idx + 1] == "text/html"
        assert result["success"] is True
        assert result["mime_type"] == "text/html"

    def test_write_binary_mime_decodes_base64(self) -> None:
        import base64

        raw_data = b"\x89PNG"
        b64_str = base64.b64encode(raw_data).decode("ascii")

        mock_result = MagicMock()
        mock_result.returncode = 0
        with (
            patch("shutil.which", return_value="/usr/bin/wl-copy"),
            patch.object(subprocess, "run", return_value=mock_result) as mock_run,
        ):
            result = input_mod.clipboard_write(b64_str, mime_type="image/png")

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs.get("text") is False
        assert call_kwargs["input"] == raw_data
        assert result["success"] is True

    def test_write_default_mime_is_text_plain(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        with (
            patch("shutil.which", return_value="/usr/bin/wl-copy"),
            patch.object(subprocess, "run", return_value=mock_result) as mock_run,
        ):
            result = input_mod.clipboard_write("hello")

        cmd = mock_run.call_args.args[0]
        assert "text/plain" in cmd
        assert result["mime_type"] == "text/plain"
