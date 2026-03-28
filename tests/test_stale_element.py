"""Tests for stale AT-SPI element handling in focus_element and set_element_text."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import accessibility


def _mock_resolve(accessible: MagicMock) -> MagicMock:
    """Patch _resolve_element to return the given mock."""
    return patch.object(accessibility, "_resolve_element", return_value=accessible)


class TestFocusElementStale:
    """grab_focus() on a stale element must return structured error, not crash."""

    def test_grab_focus_exception_returns_error(self) -> None:
        mock_acc = MagicMock()
        mock_component = MagicMock()
        mock_acc.get_component_iface.return_value = mock_component
        mock_component.grab_focus.side_effect = Exception("Stale reference")

        with _mock_resolve(mock_acc):
            result = accessibility.focus_element("0/1/2")

        assert result["success"] is False
        assert "Stale reference" in result["error"]
        assert result["element_id"] == "0/1/2"

    def test_grab_focus_success_still_works(self) -> None:
        mock_acc = MagicMock()
        mock_component = MagicMock()
        mock_acc.get_component_iface.return_value = mock_component
        mock_component.grab_focus.return_value = True

        with _mock_resolve(mock_acc):
            result = accessibility.focus_element("0/1/2")

        assert result["success"] is True
        assert result["element_id"] == "0/1/2"


class TestSetElementTextStale:
    """set_text_contents() on a stale element must return structured error, not crash."""

    def test_set_text_exception_returns_error(self) -> None:
        mock_acc = MagicMock()
        mock_editable = MagicMock()
        mock_acc.get_editable_text_iface.return_value = mock_editable
        mock_editable.set_text_contents.side_effect = Exception("Object gone")

        with _mock_resolve(mock_acc):
            result = accessibility.set_element_text("0/1/2", "hello")

        assert result["success"] is False
        assert "Object gone" in result["error"]
        assert result["element_id"] == "0/1/2"

    def test_set_text_success_still_works(self) -> None:
        mock_acc = MagicMock()
        mock_editable = MagicMock()
        mock_acc.get_editable_text_iface.return_value = mock_editable

        with _mock_resolve(mock_acc):
            result = accessibility.set_element_text("0/1/2", "hello")

        assert result["success"] is True
        assert result["element_id"] == "0/1/2"
        assert result["text_length"] == 5
