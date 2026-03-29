"""Tests for hover_element tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import accessibility, interaction


def _make_accessible_with_bounds(x: int, y: int, width: int, height: int) -> MagicMock:
    mock = MagicMock()
    component = MagicMock()
    extents = MagicMock()
    extents.x = x
    extents.y = y
    extents.width = width
    extents.height = height
    component.get_extents.return_value = extents
    mock.get_component_iface.return_value = component
    mock.get_name.return_value = "TestElement"
    mock.get_role_name.return_value = "push button"
    return mock


class TestHoverElementHappyPath:
    def test_resolves_and_moves_to_center(self) -> None:
        acc = _make_accessible_with_bounds(100, 200, 60, 40)
        with (
            patch.object(accessibility, "_resolve_element", return_value=acc),
            patch("gnome_ui_mcp.desktop.interaction.input") as mock_input,
        ):
            mock_input.perform_mouse_move.return_value = {
                "success": True,
                "x": 130,
                "y": 220,
                "backend": "mutter-remote-desktop",
            }
            result = interaction.hover_element("0/1/2")

        assert result["success"] is True
        assert result["x"] == 130
        assert result["y"] == 220
        mock_input.perform_mouse_move.assert_called_once_with(130, 220)

    def test_includes_element_metadata(self) -> None:
        acc = _make_accessible_with_bounds(100, 200, 60, 40)
        with (
            patch.object(accessibility, "_resolve_element", return_value=acc),
            patch("gnome_ui_mcp.desktop.interaction.input") as mock_input,
        ):
            mock_input.perform_mouse_move.return_value = {
                "success": True,
                "x": 130,
                "y": 220,
                "backend": "mutter-remote-desktop",
            }
            result = interaction.hover_element("0/1/2")

        assert result["element_id"] == "0/1/2"


class TestHoverElementErrors:
    def test_element_not_found(self) -> None:
        with patch.object(accessibility, "_resolve_element", side_effect=ValueError("not found")):
            result = interaction.hover_element("99/99")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_no_bounds(self) -> None:
        acc = MagicMock()
        acc.get_component_iface.return_value = None
        with patch.object(accessibility, "_resolve_element", return_value=acc):
            result = interaction.hover_element("0/1")

        assert result["success"] is False
        assert "bounds" in result["error"].lower()

    def test_propagates_move_fallback_error(self) -> None:
        acc = _make_accessible_with_bounds(100, 200, 60, 40)
        with (
            patch.object(accessibility, "_resolve_element", return_value=acc),
            patch("gnome_ui_mcp.desktop.interaction.input") as mock_input,
        ):
            mock_input.perform_mouse_move.return_value = {
                "success": True,
                "x": 130,
                "y": 220,
                "backend": "atspi",
                "fallback_error": "Mutter failed",
            }
            result = interaction.hover_element("0/1/2")

        assert result["success"] is True
        assert result["fallback_error"] == "Mutter failed"
