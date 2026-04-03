"""Tests for pixel color sampling and visual diff tools."""

from __future__ import annotations

from unittest.mock import patch

import pytest

PIL = pytest.importorskip("PIL", reason="Pillow not installed")
pytest.importorskip("numpy", reason="numpy not installed")
pytest.importorskip("scipy", reason="scipy not installed")
from PIL import Image  # noqa: E402

from gnome_ui_mcp.desktop import visual as visual_mod  # noqa: E402
from gnome_ui_mcp.desktop.input import CACHE_DIR  # noqa: E402


class TestGetPixelColor:
    def test_returns_rgba_and_hex(self) -> None:
        img = Image.new("RGBA", (100, 100), (255, 128, 0, 255))
        with (
            patch("gnome_ui_mcp.desktop.visual.input") as mock_input,
            patch("gnome_ui_mcp.desktop.visual.Image") as mock_pil,
        ):
            mock_input.screenshot.return_value = {"success": True, "path": "/tmp/shot.png"}
            mock_pil.open.return_value = img

            result = visual_mod.get_pixel_color(50, 50)

        assert result["success"] is True
        assert result["r"] == 255
        assert result["g"] == 128
        assert result["b"] == 0
        assert result["a"] == 255
        assert result["hex"] == "#FF8000"

    def test_rgb_image_no_alpha(self) -> None:
        img = Image.new("RGB", (100, 100), (0, 255, 0))
        with (
            patch("gnome_ui_mcp.desktop.visual.input") as mock_input,
            patch("gnome_ui_mcp.desktop.visual.Image") as mock_pil,
        ):
            mock_input.screenshot.return_value = {"success": True, "path": "/tmp/shot.png"}
            mock_pil.open.return_value = img

            result = visual_mod.get_pixel_color(10, 10)

        assert result["success"] is True
        assert result["g"] == 255
        assert result["a"] == 255  # default alpha

    def test_out_of_bounds_returns_error(self) -> None:
        img = Image.new("RGB", (100, 100), (0, 0, 0))
        with (
            patch("gnome_ui_mcp.desktop.visual.input") as mock_input,
            patch("gnome_ui_mcp.desktop.visual.Image") as mock_pil,
        ):
            mock_input.screenshot.return_value = {"success": True, "path": "/tmp/shot.png"}
            mock_pil.open.return_value = img

            result = visual_mod.get_pixel_color(200, 200)

        assert result["success"] is False


class TestGetRegionColor:
    def test_returns_average(self) -> None:
        img = Image.new("RGB", (100, 100), (100, 150, 200))
        with (
            patch("gnome_ui_mcp.desktop.visual.input") as mock_input,
            patch("gnome_ui_mcp.desktop.visual.Image") as mock_pil,
        ):
            mock_input.screenshot.return_value = {"success": True, "path": "/tmp/shot.png"}
            mock_pil.open.return_value = img

            result = visual_mod.get_region_color(10, 10, 20, 20)

        assert result["success"] is True
        assert result["r"] == 100
        assert result["g"] == 150
        assert result["b"] == 200


class TestVisualDiff:
    def test_identical_images_no_change(self) -> None:
        img = Image.new("RGB", (100, 100), (128, 128, 128))
        p1 = str(CACHE_DIR / "a.png")
        p2 = str(CACHE_DIR / "b.png")
        with patch("gnome_ui_mcp.desktop.visual.Image") as mock_pil:
            mock_pil.open.side_effect = [img.copy(), img.copy()]

            result = visual_mod.visual_diff(p1, p2)

        assert result["success"] is True
        assert result["changed"] is False
        assert result["changed_percent"] == 0.0
        assert len(result["regions"]) == 0

    def test_different_images_detected(self) -> None:
        img1 = Image.new("RGB", (100, 100), (0, 0, 0))
        img2 = Image.new("RGB", (100, 100), (0, 0, 0))
        # Paint a white rectangle on img2
        for x in range(20, 40):
            for y in range(20, 40):
                img2.putpixel((x, y), (255, 255, 255))

        p1 = str(CACHE_DIR / "a.png")
        p2 = str(CACHE_DIR / "b.png")
        with patch("gnome_ui_mcp.desktop.visual.Image") as mock_pil:
            mock_pil.open.side_effect = [img1, img2]

            result = visual_mod.visual_diff(p1, p2)

        assert result["success"] is True
        assert result["changed"] is True
        assert result["changed_percent"] > 0
        assert len(result["regions"]) >= 1

    def test_regions_have_bbox_format(self) -> None:
        img1 = Image.new("RGB", (100, 100), (0, 0, 0))
        img2 = Image.new("RGB", (100, 100), (0, 0, 0))
        for x in range(50, 60):
            for y in range(50, 60):
                img2.putpixel((x, y), (255, 0, 0))

        p1 = str(CACHE_DIR / "a.png")
        p2 = str(CACHE_DIR / "b.png")
        with patch("gnome_ui_mcp.desktop.visual.Image") as mock_pil:
            mock_pil.open.side_effect = [img1, img2]

            result = visual_mod.visual_diff(p1, p2)

        region = result["regions"][0]
        assert "x" in region
        assert "y" in region
        assert "width" in region
        assert "height" in region

    def test_invalid_path_returns_error(self) -> None:
        p1 = str(CACHE_DIR / "missing1.png")
        p2 = str(CACHE_DIR / "missing2.png")
        with patch("gnome_ui_mcp.desktop.visual.Image") as mock_pil:
            mock_pil.open.side_effect = FileNotFoundError("No such file")

            result = visual_mod.visual_diff(p1, p2)

        assert result["success"] is False
