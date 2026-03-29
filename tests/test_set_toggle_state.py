"""Tests for set_toggle_state tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import accessibility


def _make_accessible(states: list[str]) -> MagicMock:
    mock = MagicMock()
    mock.get_role_name.return_value = "toggle button"
    return mock


class TestSetToggleState:
    def test_already_correct_state_returns_noop(self) -> None:
        mock_accessible = _make_accessible(["checked"])

        with (
            patch.object(accessibility, "_resolve_element", return_value=mock_accessible),
            patch.object(accessibility, "_element_states", return_value=["checked", "showing"]),
        ):
            result = accessibility.set_toggle_state("0/1/2", desired_state=True)

        assert result["success"] is True
        assert result["toggled"] is False

    def test_toggles_when_different(self) -> None:
        mock_accessible = _make_accessible([])
        mock_accessible.do_action.return_value = True

        with (
            patch.object(accessibility, "_resolve_element", return_value=mock_accessible),
            patch.object(
                accessibility,
                "_element_states",
                side_effect=[["showing"], ["checked", "showing"]],
            ),
            patch.object(accessibility, "_find_action_index", return_value=0),
        ):
            result = accessibility.set_toggle_state("0/1/2", desired_state=True)

        assert result["success"] is True
        assert result["toggled"] is True

    def test_returns_new_state(self) -> None:
        mock_accessible = _make_accessible(["checked"])
        mock_accessible.do_action.return_value = True

        with (
            patch.object(accessibility, "_resolve_element", return_value=mock_accessible),
            patch.object(
                accessibility,
                "_element_states",
                side_effect=[["checked", "showing"], ["showing"]],
            ),
            patch.object(accessibility, "_find_action_index", return_value=0),
        ):
            result = accessibility.set_toggle_state("0/1/2", desired_state=False)

        assert result["success"] is True
        assert result["toggled"] is True
        assert result["new_active"] is False

    def test_no_checkable_element_error(self) -> None:
        mock_accessible = _make_accessible([])

        with (
            patch.object(accessibility, "_resolve_element", return_value=mock_accessible),
            patch.object(accessibility, "_element_states", return_value=["showing"]),
            patch.object(accessibility, "_find_action_index", return_value=None),
        ):
            result = accessibility.set_toggle_state("0/1/2", desired_state=True)

        assert result["success"] is False
        assert "toggle" in result["error"].lower() or "action" in result["error"].lower()
