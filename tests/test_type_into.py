"""Tests for OCR-based type_into: AT-SPI first, OCR fallback, optional submit."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import ocr


class TestTypeIntoAtSpi:
    """type_into should try AT-SPI first to find an editable element by label."""

    @patch("gnome_ui_mcp.desktop.ocr.input")
    @patch("gnome_ui_mcp.desktop.ocr.accessibility")
    def test_atspi_editable_found(self, mock_acc: MagicMock, mock_input: MagicMock) -> None:
        """When AT-SPI finds an editable element, focus it and type."""
        mock_acc.find_elements.return_value = {
            "success": True,
            "matches": [
                {
                    "id": "0/1/2",
                    "name": "Username",
                    "states": ["editable", "showing", "focusable"],
                    "bounds": {"x": 100, "y": 200, "width": 200, "height": 30},
                }
            ],
        }
        mock_acc.focus_element.return_value = {"success": True}
        mock_input.type_text.return_value = {"success": True}

        result = ocr.type_into("Username", "admin")
        assert result["success"] is True
        assert result["method"] == "atspi"
        mock_acc.focus_element.assert_called_once_with("0/1/2")
        mock_input.type_text.assert_called_once_with("admin")

    @patch("gnome_ui_mcp.desktop.ocr.input")
    @patch("gnome_ui_mcp.desktop.ocr.accessibility")
    def test_atspi_no_editable_falls_through(
        self, mock_acc: MagicMock, mock_input: MagicMock
    ) -> None:
        """When AT-SPI finds no editable match, try OCR fallback."""
        # Return a non-editable match
        mock_acc.find_elements.return_value = {
            "success": True,
            "matches": [
                {
                    "id": "0/1/3",
                    "name": "Username",
                    "states": ["showing"],
                    "bounds": {"x": 100, "y": 200, "width": 200, "height": 30},
                }
            ],
        }
        # OCR fallback also fails
        with patch("gnome_ui_mcp.desktop.ocr.find_text_ocr", return_value=None):
            result = ocr.type_into("Username", "admin")
        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestTypeIntoOcr:
    """When AT-SPI fails, fall back to OCR-based text location."""

    @patch("gnome_ui_mcp.desktop.ocr.input")
    @patch("gnome_ui_mcp.desktop.ocr.interaction")
    @patch("gnome_ui_mcp.desktop.ocr.accessibility")
    @patch("gnome_ui_mcp.desktop.ocr.find_text_ocr")
    def test_ocr_fallback_clicks_and_types(
        self,
        mock_find_ocr: MagicMock,
        mock_acc: MagicMock,
        mock_interaction: MagicMock,
        mock_input: MagicMock,
    ) -> None:
        """OCR finds label, clicks its center, then types text."""
        mock_acc.find_elements.return_value = {"success": True, "matches": []}
        mock_find_ocr.return_value = {
            "x": 100,
            "y": 200,
            "width": 80,
            "height": 20,
        }
        mock_interaction.click_at.return_value = {"success": True}
        mock_input.type_text.return_value = {"success": True}

        result = ocr.type_into("Username", "admin")
        assert result["success"] is True
        assert result["method"] == "ocr"
        # Click at center of OCR bounding box
        mock_interaction.click_at.assert_called_once_with(x=140, y=210)
        mock_input.type_text.assert_called_once_with("admin")

    @patch("gnome_ui_mcp.desktop.ocr.input")
    @patch("gnome_ui_mcp.desktop.ocr.accessibility")
    @patch("gnome_ui_mcp.desktop.ocr.find_text_ocr")
    def test_ocr_not_found_returns_error(
        self,
        mock_find_ocr: MagicMock,
        mock_acc: MagicMock,
        mock_input: MagicMock,
    ) -> None:
        """When both AT-SPI and OCR fail, return error."""
        mock_acc.find_elements.return_value = {"success": True, "matches": []}
        mock_find_ocr.return_value = None

        result = ocr.type_into("Username", "admin")
        assert result["success"] is False


class TestTypeIntoSubmit:
    """type_into with submit=True presses Return after typing."""

    @patch("gnome_ui_mcp.desktop.ocr.input")
    @patch("gnome_ui_mcp.desktop.ocr.accessibility")
    def test_submit_presses_return(self, mock_acc: MagicMock, mock_input: MagicMock) -> None:
        mock_acc.find_elements.return_value = {
            "success": True,
            "matches": [
                {
                    "id": "0/1/2",
                    "name": "Search",
                    "states": ["editable", "showing"],
                    "bounds": {"x": 10, "y": 20, "width": 100, "height": 30},
                }
            ],
        }
        mock_acc.focus_element.return_value = {"success": True}
        mock_input.type_text.return_value = {"success": True}
        mock_input.press_key.return_value = {"success": True}

        result = ocr.type_into("Search", "hello", submit=True)
        assert result["success"] is True
        mock_input.press_key.assert_called_once_with("Return")

    @patch("gnome_ui_mcp.desktop.ocr.input")
    @patch("gnome_ui_mcp.desktop.ocr.accessibility")
    def test_no_submit_does_not_press_return(
        self, mock_acc: MagicMock, mock_input: MagicMock
    ) -> None:
        mock_acc.find_elements.return_value = {
            "success": True,
            "matches": [
                {
                    "id": "0/1/2",
                    "name": "Search",
                    "states": ["editable", "showing"],
                    "bounds": {"x": 10, "y": 20, "width": 100, "height": 30},
                }
            ],
        }
        mock_acc.focus_element.return_value = {"success": True}
        mock_input.type_text.return_value = {"success": True}

        result = ocr.type_into("Search", "hello", submit=False)
        assert result["success"] is True
        mock_input.press_key.assert_not_called()
