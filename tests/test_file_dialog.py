"""Tests for file_dialog_set_path tool."""

from __future__ import annotations

from unittest.mock import patch

from gnome_ui_mcp.desktop import file_dialog


class TestFileDialogSetPath:
    def test_sends_ctrl_l_then_types_path_then_return(self) -> None:
        combo_result = {"success": True}
        type_result = {"success": True, "text_length": 10}
        key_result = {"success": True}

        with (
            patch.object(file_dialog.input, "key_combo", return_value=combo_result) as mock_combo,
            patch.object(file_dialog.input, "type_text", return_value=type_result) as mock_type,
            patch.object(file_dialog.input, "press_key", return_value=key_result) as mock_key,
            patch("time.sleep"),
        ):
            result = file_dialog.file_dialog_set_path("/home/user/test.txt")

        assert result["success"] is True
        mock_combo.assert_called_once_with("ctrl+l")
        mock_type.assert_called_once_with("/home/user/test.txt")
        mock_key.assert_called_once_with("Return")

    def test_relative_path_handling(self) -> None:
        combo_result = {"success": True}
        type_result = {"success": True, "text_length": 8}
        key_result = {"success": True}

        with (
            patch.object(file_dialog.input, "key_combo", return_value=combo_result),
            patch.object(file_dialog.input, "type_text", return_value=type_result) as mock_type,
            patch.object(file_dialog.input, "press_key", return_value=key_result),
            patch("time.sleep"),
        ):
            result = file_dialog.file_dialog_set_path("docs/file.txt")

        assert result["success"] is True
        mock_type.assert_called_once_with("docs/file.txt")

    def test_empty_path_error(self) -> None:
        result = file_dialog.file_dialog_set_path("")

        assert result["success"] is False
        assert "empty" in result["error"].lower() or "path" in result["error"].lower()
