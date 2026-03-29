"""Tests for record_action being called by mutating backend functions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp import backend
from gnome_ui_mcp.desktop import history


class TestHistoryWiring:
    """Mutating backend functions should record actions in history."""

    def setup_method(self) -> None:
        history._history.clear()

    @patch("gnome_ui_mcp.desktop.interaction.click_element")
    def test_click_element_records_action(
        self,
        mock_click: MagicMock,
    ) -> None:
        mock_click.return_value = {"success": True}
        backend.click_element(element_id="0/1/2")

        result = history.get_action_history(last_n=10)
        assert result["count"] == 1
        assert result["history"][0]["tool"] == "click_element"

    @patch("gnome_ui_mcp.desktop.input.type_text")
    def test_type_text_records_action(self, mock_type: MagicMock) -> None:
        mock_type.return_value = {"success": True}
        backend.type_text(text="hello")

        result = history.get_action_history(last_n=10)
        assert result["count"] == 1
        assert result["history"][0]["tool"] == "type_text"
        assert result["history"][0]["params"]["text"] == "hello"

    @patch("gnome_ui_mcp.desktop.accessibility.list_applications")
    def test_readonly_does_not_record(self, mock_list: MagicMock) -> None:
        mock_list.return_value = {"success": True, "applications": []}
        backend.list_applications()

        result = history.get_action_history(last_n=10)
        assert result["count"] == 0
