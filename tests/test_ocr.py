"""Tests for OCR hybrid (Tesseract + AT-SPI)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

PIL = pytest.importorskip("PIL", reason="Pillow not installed")
from PIL import Image

from gnome_ui_mcp.desktop import ocr as ocr_mod

_has_tesseract = ocr_mod._HAS_OCR_DEPS
_skip_no_tesseract = pytest.mark.skipif(not _has_tesseract, reason="pytesseract not installed")


def _make_light_image(width: int = 200, height: int = 50) -> Image.Image:
    """Create a light-background test image."""
    return Image.new("RGB", (width, height), (240, 240, 240))


def _make_dark_image(width: int = 200, height: int = 50) -> Image.Image:
    """Create a dark-background test image."""
    return Image.new("RGB", (width, height), (30, 30, 30))


class TestPreprocess:
    def test_inverts_dark_image(self) -> None:
        dark = _make_dark_image()
        processed = ocr_mod._preprocess_for_ocr(dark)
        # After inversion, grayscale pixel should be light
        val = processed.getpixel((0, 0))
        assert val > 128

    def test_keeps_light_image(self) -> None:
        light = _make_light_image()
        processed = ocr_mod._preprocess_for_ocr(light)
        val = processed.getpixel((0, 0))
        assert val > 128


class TestFilterWords:
    def test_filters_low_confidence(self) -> None:
        raw_data = {
            "level": [5, 5, 5],
            "left": [10, 50, 90],
            "top": [10, 10, 10],
            "width": [30, 30, 30],
            "height": [15, 15, 15],
            "conf": [95, 10, 80],
            "text": ["hello", "x", "world"],
        }
        words = ocr_mod._filter_words(raw_data, min_conf=30)
        assert len(words) == 2
        assert words[0]["text"] == "hello"
        assert words[1]["text"] == "world"

    def test_empty_text_filtered(self) -> None:
        raw_data = {
            "level": [5, 5],
            "left": [10, 50],
            "top": [10, 10],
            "width": [30, 30],
            "height": [15, 15],
            "conf": [95, 90],
            "text": ["hello", "  "],
        }
        words = ocr_mod._filter_words(raw_data, min_conf=30)
        assert len(words) == 1


class TestFindText:
    def test_single_word_match(self) -> None:
        words = [
            {"text": "hello", "x": 10, "y": 5, "width": 40, "height": 12},
            {"text": "world", "x": 60, "y": 5, "width": 40, "height": 12},
        ]
        matches = ocr_mod._find_text_in_words(words, "world")
        assert len(matches) == 1
        assert matches[0]["x"] == 60

    def test_case_insensitive(self) -> None:
        words = [{"text": "Hello", "x": 10, "y": 5, "width": 40, "height": 12}]
        matches = ocr_mod._find_text_in_words(words, "hello")
        assert len(matches) == 1

    def test_no_match_returns_empty(self) -> None:
        words = [{"text": "hello", "x": 10, "y": 5, "width": 40, "height": 12}]
        matches = ocr_mod._find_text_in_words(words, "xyz")
        assert len(matches) == 0

    def test_multi_word_phrase(self) -> None:
        words = [
            {"text": "Save", "x": 10, "y": 5, "width": 30, "height": 12},
            {"text": "As", "x": 45, "y": 5, "width": 20, "height": 12},
            {"text": "other", "x": 80, "y": 5, "width": 35, "height": 12},
        ]
        matches = ocr_mod._find_text_in_words(words, "Save As")
        assert len(matches) == 1
        # Bounding box should span Save + As
        assert matches[0]["x"] == 10
        assert matches[0]["width"] == 55  # 45 + 20 - 10


@_skip_no_tesseract
class TestOcrScreen:
    def test_returns_words_and_text(self) -> None:
        mock_data = {
            "level": [5, 5],
            "left": [10, 60],
            "top": [5, 5],
            "width": [40, 40],
            "height": [12, 12],
            "conf": [95, 90],
            "text": ["hello", "world"],
        }
        with (
            patch("gnome_ui_mcp.desktop.ocr.input") as mock_input,
            patch("gnome_ui_mcp.desktop.ocr.pytesseract") as mock_tess,
            patch("gnome_ui_mcp.desktop.ocr.Image") as mock_pil,
        ):
            mock_input.screenshot.return_value = {"success": True, "path": "/tmp/shot.png"}
            mock_pil.open.return_value = _make_light_image()
            mock_tess.Output.DICT = "dict"
            mock_tess.image_to_data.return_value = mock_data
            mock_tess.image_to_string.return_value = "hello world"

            result = ocr_mod.ocr_screen()

        assert result["success"] is True
        assert len(result["words"]) == 2
        assert "hello" in result["text"]

    def test_region_uses_screenshot_area(self) -> None:
        mock_data = {
            "level": [],
            "left": [],
            "top": [],
            "width": [],
            "height": [],
            "conf": [],
            "text": [],
        }
        with (
            patch("gnome_ui_mcp.desktop.ocr.input") as mock_input,
            patch("gnome_ui_mcp.desktop.ocr.pytesseract") as mock_tess,
            patch("gnome_ui_mcp.desktop.ocr.Image") as mock_pil,
        ):
            mock_input.screenshot_area.return_value = {"success": True, "path": "/tmp/area.png"}
            mock_pil.open.return_value = _make_light_image()
            mock_tess.Output.DICT = "dict"
            mock_tess.image_to_data.return_value = mock_data

            ocr_mod.ocr_screen(x=100, y=200, width=300, height=400)

        mock_input.screenshot_area.assert_called_once_with(100, 200, 300, 400)
