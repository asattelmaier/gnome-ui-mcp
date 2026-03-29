"""Tests for navigate_menu tool."""

from __future__ import annotations

from unittest.mock import patch

from gnome_ui_mcp.desktop import interaction


class TestNavigateMenu:
    def test_single_level_menu(self) -> None:
        with patch.object(
            interaction,
            "find_and_activate",
            return_value={"success": True, "match": {"id": "0/1/2"}},
        ):
            result = interaction.navigate_menu(["File"])

        assert result["success"] is True

    def test_two_level_nested(self) -> None:
        activate_results = [
            {"success": True, "match": {"id": "0/1/2"}},
            {"success": True, "match": {"id": "0/1/2/3"}},
        ]
        wait_result = {"success": True, "match": {"id": "0/1/2/3"}}

        with (
            patch.object(
                interaction,
                "find_and_activate",
                side_effect=activate_results,
            ),
            patch.object(
                interaction.accessibility,
                "wait_for_element",
                return_value=wait_result,
            ),
        ):
            result = interaction.navigate_menu(["File", "New"])

        assert result["success"] is True

    def test_item_not_found_error(self) -> None:
        with patch.object(
            interaction,
            "find_and_activate",
            return_value={
                "success": False,
                "error": "No element matched query",
            },
        ):
            result = interaction.navigate_menu(["NonExistent"])

        assert result["success"] is False
        assert "NonExistent" in result.get("error", "")

    def test_empty_path_error(self) -> None:
        result = interaction.navigate_menu([])

        assert result["success"] is False
        assert "empty" in result["error"].lower()
