"""Tests for set_element_value tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import accessibility


class TestSetElementValue:
    def test_sets_value_on_slider(self) -> None:
        mock_accessible = MagicMock()
        mock_value = MagicMock()
        mock_accessible.get_value_iface.return_value = mock_value
        mock_value.get_minimum_value.return_value = 0.0
        mock_value.get_maximum_value.return_value = 100.0
        mock_value.set_current_value.return_value = True
        mock_value.get_current_value.return_value = 50.0

        with patch.object(accessibility, "_resolve_element", return_value=mock_accessible):
            result = accessibility.set_element_value("0/1/2", 50.0)

        assert result["success"] is True
        mock_value.set_current_value.assert_called_once_with(50.0)

    def test_rejects_out_of_range(self) -> None:
        mock_accessible = MagicMock()
        mock_value = MagicMock()
        mock_accessible.get_value_iface.return_value = mock_value
        mock_value.get_minimum_value.return_value = 0.0
        mock_value.get_maximum_value.return_value = 100.0

        with patch.object(accessibility, "_resolve_element", return_value=mock_accessible):
            result = accessibility.set_element_value("0/1/2", 150.0)

        assert result["success"] is False
        assert "range" in result["error"].lower()

    def test_no_value_interface_returns_error(self) -> None:
        mock_accessible = MagicMock()
        mock_accessible.get_value_iface.return_value = None

        with patch.object(accessibility, "_resolve_element", return_value=mock_accessible):
            result = accessibility.set_element_value("0/1/2", 50.0)

        assert result["success"] is False
        assert "value" in result["error"].lower()

    def test_returns_new_value(self) -> None:
        mock_accessible = MagicMock()
        mock_value = MagicMock()
        mock_accessible.get_value_iface.return_value = mock_value
        mock_value.get_minimum_value.return_value = 0.0
        mock_value.get_maximum_value.return_value = 100.0
        mock_value.set_current_value.return_value = True
        mock_value.get_current_value.return_value = 75.0

        with patch.object(accessibility, "_resolve_element", return_value=mock_accessible):
            result = accessibility.set_element_value("0/1/2", 75.0)

        assert result["current_value"] == 75.0
