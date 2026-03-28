"""Tests for VLM screenshot analysis: analyze_screenshot and compare_screenshots."""

from __future__ import annotations

import base64
from unittest.mock import MagicMock, mock_open, patch

import pytest

from gnome_ui_mcp.desktop import vlm


class TestAnalyzeScreenshot:
    """analyze_screenshot captures screen and sends to a VLM provider."""

    @patch("gnome_ui_mcp.desktop.vlm.urllib.request.urlopen")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fakepng")
    @patch("gnome_ui_mcp.desktop.vlm.input")
    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
    def test_openrouter_default(
        self,
        mock_input: MagicMock,
        mock_file: MagicMock,
        mock_urlopen: MagicMock,
    ) -> None:
        mock_input.screenshot.return_value = {"success": True, "path": "/tmp/shot.png"}
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"choices":[{"message":{"content":"A desktop"}}]}'
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = vlm.analyze_screenshot("What do you see?")
        assert result["success"] is True
        assert result["analysis"] == "A desktop"
        assert result["provider"] == "openrouter"
        assert result["model"] == "google/gemma-3-27b-it:free"

    @patch("gnome_ui_mcp.desktop.vlm.urllib.request.urlopen")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fakepng")
    @patch("gnome_ui_mcp.desktop.vlm.input")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_anthropic_provider(
        self,
        mock_input: MagicMock,
        mock_file: MagicMock,
        mock_urlopen: MagicMock,
    ) -> None:
        mock_input.screenshot.return_value = {"success": True, "path": "/tmp/shot.png"}
        mock_response = MagicMock()
        mock_response.read.return_value = (
            b'{"content":[{"type":"text","text":"GNOME desktop"}]}'
        )
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = vlm.analyze_screenshot("Describe", provider="anthropic")
        assert result["success"] is True
        assert result["analysis"] == "GNOME desktop"
        assert result["provider"] == "anthropic"
        assert result["model"] == "claude-sonnet-4-20250514"

    @patch("gnome_ui_mcp.desktop.vlm.urllib.request.urlopen")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fakepng")
    @patch("gnome_ui_mcp.desktop.vlm.input")
    def test_ollama_provider(
        self,
        mock_input: MagicMock,
        mock_file: MagicMock,
        mock_urlopen: MagicMock,
    ) -> None:
        mock_input.screenshot.return_value = {"success": True, "path": "/tmp/shot.png"}
        mock_response = MagicMock()
        mock_response.read.return_value = (
            b'{"message":{"content":"Some text"}}'
        )
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = vlm.analyze_screenshot("Describe", provider="ollama")
        assert result["success"] is True
        assert result["analysis"] == "Some text"
        assert result["provider"] == "ollama"
        assert result["model"] == "gemma3"

    @patch("gnome_ui_mcp.desktop.vlm.input")
    def test_screenshot_failure(self, mock_input: MagicMock) -> None:
        mock_input.screenshot.return_value = {"success": False, "error": "no display"}
        result = vlm.analyze_screenshot("What?")
        assert result["success"] is False
        assert "screenshot" in result["error"].lower()

    def test_invalid_provider(self) -> None:
        with patch("gnome_ui_mcp.desktop.vlm.input") as mock_input:
            mock_input.screenshot.return_value = {
                "success": True,
                "path": "/tmp/shot.png",
            }
            with patch("builtins.open", mock_open(read_data=b"fakepng")):
                result = vlm.analyze_screenshot("What?", provider="invalid_provider")
        assert result["success"] is False
        assert "provider" in result["error"].lower()


class TestCompareScreenshots:
    """compare_screenshots sends two images for comparison."""

    @patch("gnome_ui_mcp.desktop.vlm.urllib.request.urlopen")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fakepng")
    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
    def test_compare_two_images(
        self,
        mock_file: MagicMock,
        mock_urlopen: MagicMock,
    ) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = (
            b'{"choices":[{"message":{"content":"Image 2 has a new button"}}]}'
        )
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = vlm.compare_screenshots("/tmp/a.png", "/tmp/b.png")
        assert result["success"] is True
        assert "new button" in result["analysis"]

    @patch("gnome_ui_mcp.desktop.vlm.urllib.request.urlopen")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fakepng")
    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
    def test_compare_custom_prompt(
        self,
        mock_file: MagicMock,
        mock_urlopen: MagicMock,
    ) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = (
            b'{"choices":[{"message":{"content":"Colors differ"}}]}'
        )
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = vlm.compare_screenshots(
            "/tmp/a.png", "/tmp/b.png", prompt="Compare colors"
        )
        assert result["success"] is True
        assert result["analysis"] == "Colors differ"

    @patch("builtins.open", side_effect=FileNotFoundError("no file"))
    def test_compare_missing_file(self, mock_file: MagicMock) -> None:
        result = vlm.compare_screenshots("/tmp/nonexistent.png", "/tmp/b.png")
        assert result["success"] is False
