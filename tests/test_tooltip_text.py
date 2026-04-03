"""Tests for get_tooltip_text in accessibility module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import accessibility


class TestGetTooltipText:
    def test_tooltip_from_description(self) -> None:
        mock_element = MagicMock()
        mock_element.get_description.return_value = "Save document"
        mock_element.get_relation_set.return_value = []

        with patch.object(accessibility, "_resolve_element", return_value=mock_element):
            result = accessibility.get_tooltip_text("0/0/1")

        assert result["success"] is True
        assert result["tooltip_text"] == "Save document"
        assert result["source"] == "description"

    def test_tooltip_from_relation(self) -> None:
        mock_element = MagicMock()
        mock_element.get_description.return_value = ""

        mock_rel_type = MagicMock()
        mock_rel_type.value_nick = "tooltip-for"

        mock_target = MagicMock()
        mock_target.get_name.return_value = "Tooltip content"

        mock_rel = MagicMock()
        mock_rel.get_relation_type.return_value = mock_rel_type
        mock_rel.get_n_targets.return_value = 1
        mock_rel.get_target.return_value = mock_target

        mock_element.get_relation_set.return_value = [mock_rel]

        with patch.object(accessibility, "_resolve_element", return_value=mock_element):
            result = accessibility.get_tooltip_text("0/0/1")

        assert result["success"] is True
        assert result["tooltip_text"] == "Tooltip content"
        assert result["source"] == "relation"

    def test_no_tooltip_returns_null(self) -> None:
        mock_element = MagicMock()
        mock_element.get_description.return_value = ""
        mock_element.get_relation_set.return_value = []

        with patch.object(accessibility, "_resolve_element", return_value=mock_element):
            result = accessibility.get_tooltip_text("0/0/1")

        assert result["success"] is True
        assert result["tooltip_text"] is None
        assert result["source"] is None
