"""Tests for expand_node and collapse_node tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import accessibility


class TestExpandCollapseNode:
    def test_expand_when_collapsed(self) -> None:
        mock_accessible = MagicMock()
        mock_accessible.do_action.return_value = True

        with (
            patch.object(accessibility, "_resolve_element", return_value=mock_accessible),
            patch.object(accessibility, "_element_states", return_value=["showing"]),
            patch.object(accessibility, "_find_action_index", return_value=0),
        ):
            result = accessibility.expand_node("0/1/2")

        assert result["success"] is True
        assert result["toggled"] is True

    def test_collapse_when_expanded(self) -> None:
        mock_accessible = MagicMock()
        mock_accessible.do_action.return_value = True

        with (
            patch.object(accessibility, "_resolve_element", return_value=mock_accessible),
            patch.object(
                accessibility,
                "_element_states",
                return_value=["expanded", "showing"],
            ),
            patch.object(accessibility, "_find_action_index", return_value=0),
        ):
            result = accessibility.collapse_node("0/1/2")

        assert result["success"] is True
        assert result["toggled"] is True

    def test_already_expanded_noop(self) -> None:
        mock_accessible = MagicMock()

        with (
            patch.object(accessibility, "_resolve_element", return_value=mock_accessible),
            patch.object(
                accessibility,
                "_element_states",
                return_value=["expanded", "showing"],
            ),
        ):
            result = accessibility.expand_node("0/1/2")

        assert result["success"] is True
        assert result["toggled"] is False

    def test_no_expandable_state_error(self) -> None:
        mock_accessible = MagicMock()

        with (
            patch.object(accessibility, "_resolve_element", return_value=mock_accessible),
            patch.object(accessibility, "_element_states", return_value=["showing"]),
            patch.object(accessibility, "_find_action_index", return_value=None),
        ):
            result = accessibility.expand_node("0/1/2")

        assert result["success"] is False
        assert "expand" in result["error"].lower() or "action" in result["error"].lower()
