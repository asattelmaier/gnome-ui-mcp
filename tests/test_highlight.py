"""Tests for highlight_element (Item 16)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import highlight

_MOD = "gnome_ui_mcp.desktop.highlight"


class TestHighlightElement:
    def test_success_returns_path(self) -> None:
        mock_acc = MagicMock()
        bounds = {"x": 100, "y": 200, "width": 150, "height": 40}
        screenshot_result = {"success": True, "path": "/tmp/test-screenshot.png"}

        mock_image = MagicMock()
        mock_draw = MagicMock()

        with (
            patch(f"{_MOD}.accessibility._resolve_element", return_value=mock_acc),
            patch(f"{_MOD}.accessibility._element_bounds", return_value=bounds),
            patch(f"{_MOD}.input.screenshot", return_value=screenshot_result),
            patch(f"{_MOD}.Image") as mock_pil_image,
            patch(f"{_MOD}.ImageDraw") as mock_pil_draw,
        ):
            mock_pil_image.open.return_value = mock_image
            mock_pil_draw.Draw.return_value = mock_draw
            result = highlight.highlight_element("0/1/2")

        assert result["success"] is True
        assert "path" in result
        mock_draw.rectangle.assert_called_once()

    def test_with_label(self) -> None:
        mock_acc = MagicMock()
        bounds = {"x": 50, "y": 60, "width": 100, "height": 30}
        screenshot_result = {"success": True, "path": "/tmp/test-screenshot.png"}

        mock_image = MagicMock()
        mock_draw = MagicMock()

        with (
            patch(f"{_MOD}.accessibility._resolve_element", return_value=mock_acc),
            patch(f"{_MOD}.accessibility._element_bounds", return_value=bounds),
            patch(f"{_MOD}.input.screenshot", return_value=screenshot_result),
            patch(f"{_MOD}.Image") as mock_pil_image,
            patch(f"{_MOD}.ImageDraw") as mock_pil_draw,
        ):
            mock_pil_image.open.return_value = mock_image
            mock_pil_draw.Draw.return_value = mock_draw
            result = highlight.highlight_element("0/1/2", label="Button")

        assert result["success"] is True
        mock_draw.text.assert_called_once()

    def test_no_bounds_error(self) -> None:
        mock_acc = MagicMock()
        with (
            patch(f"{_MOD}.accessibility._resolve_element", return_value=mock_acc),
            patch(f"{_MOD}.accessibility._element_bounds", return_value=None),
        ):
            result = highlight.highlight_element("0/1/2")

        assert result["success"] is False

    def test_screenshot_failure(self) -> None:
        mock_acc = MagicMock()
        bounds = {"x": 10, "y": 20, "width": 80, "height": 30}
        with (
            patch(f"{_MOD}.accessibility._resolve_element", return_value=mock_acc),
            patch(f"{_MOD}.accessibility._element_bounds", return_value=bounds),
            patch(
                f"{_MOD}.input.screenshot",
                return_value={"success": False, "error": "no display"},
            ),
        ):
            result = highlight.highlight_element("0/1/2")

        assert result["success"] is False
