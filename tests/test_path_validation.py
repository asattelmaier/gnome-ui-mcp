"""Tests for path validation in vlm.compare_screenshots and visual.visual_diff."""

from __future__ import annotations

from unittest.mock import MagicMock, mock_open, patch

import pytest

from gnome_ui_mcp.desktop import vlm
from gnome_ui_mcp.desktop.input import CACHE_DIR

PIL = pytest.importorskip("PIL", reason="Pillow not installed")
pytest.importorskip("numpy", reason="numpy not installed")
pytest.importorskip("scipy", reason="scipy not installed")
from PIL import Image  # noqa: E402

from gnome_ui_mcp.desktop import visual as visual_mod  # noqa: E402


class TestVlmPathValidation:
    """compare_screenshots must reject paths outside the screenshot cache."""

    @patch("gnome_ui_mcp.desktop.vlm.urllib.request.urlopen")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fakepng")
    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
    def test_valid_cache_path_accepted(
        self,
        mock_file: MagicMock,
        mock_urlopen: MagicMock,
    ) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"choices":[{"message":{"content":"Same"}}]}'
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        p1 = str(CACHE_DIR / "a.png")
        p2 = str(CACHE_DIR / "b.png")
        result = vlm.compare_screenshots(p1, p2)
        assert result["success"] is True

    def test_path_outside_cache_returns_error(self) -> None:
        result = vlm.compare_screenshots("/etc/passwd", "/tmp/b.png")
        assert result["success"] is False
        assert "outside" in result["error"].lower() or "path" in result["error"].lower()

    def test_path_traversal_returns_error(self) -> None:
        traversal = str(CACHE_DIR / "../../etc/passwd")
        result = vlm.compare_screenshots(traversal, str(CACHE_DIR / "b.png"))
        assert result["success"] is False
        assert "outside" in result["error"].lower() or "path" in result["error"].lower()


class TestVisualDiffPathValidation:
    """visual_diff must reject paths outside the screenshot cache."""

    def test_valid_cache_path_accepted(self) -> None:
        img = Image.new("RGB", (100, 100), (128, 128, 128))
        with patch("gnome_ui_mcp.desktop.visual.Image") as mock_pil:
            mock_pil.open.side_effect = [img.copy(), img.copy()]
            p1 = str(CACHE_DIR / "a.png")
            p2 = str(CACHE_DIR / "b.png")
            result = visual_mod.visual_diff(p1, p2)

        assert result["success"] is True

    def test_path_outside_cache_returns_error(self) -> None:
        result = visual_mod.visual_diff("/etc/passwd", "/tmp/b.png")
        assert result["success"] is False
        assert "outside" in result["error"].lower() or "path" in result["error"].lower()

    def test_path_traversal_returns_error(self) -> None:
        traversal = str(CACHE_DIR / "../../etc/passwd")
        result = visual_mod.visual_diff(traversal, str(CACHE_DIR / "b.png"))
        assert result["success"] is False
        assert "outside" in result["error"].lower() or "path" in result["error"].lower()
