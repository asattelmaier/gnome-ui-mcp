"""Tests for get_elements_by_ids (Item 6).

Verifies batch resolution of element IDs with per-element error handling.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import accessibility


def _make_accessible(name: str, role: str) -> MagicMock:
    mock = MagicMock()
    mock.get_name.return_value = name
    mock.get_role_name.return_value = role
    mock.get_description.return_value = ""
    mock.get_component_iface.return_value = None
    mock.get_text_iface.return_value = None
    mock.get_editable_text_iface.return_value = None
    mock.get_n_actions.return_value = 0
    state_set = MagicMock()
    state_set.get_states.return_value = []
    mock.get_state_set.return_value = state_set
    mock.get_child_count.return_value = 0
    mock.get_child_at_index.side_effect = lambda i: None
    return mock


class TestGetElementsByIds:
    """Batch resolution of multiple element IDs."""

    def test_resolves_multiple_ids(self) -> None:
        btn = _make_accessible("OK", "push button")
        label = _make_accessible("Title", "label")

        def mock_resolve(eid: str) -> MagicMock:
            if eid == "0/1":
                return btn
            if eid == "0/2":
                return label
            msg = f"Element not found: {eid}"
            raise ValueError(msg)

        with patch.object(accessibility, "_resolve_element", side_effect=mock_resolve):
            result = accessibility.get_elements_by_ids(["0/1", "0/2"])

        assert result["success"] is True
        assert len(result["elements"]) == 2
        assert result["elements"][0]["name"] == "OK"
        assert result["elements"][1]["name"] == "Title"
        assert result["missing"] == []

    def test_tracks_missing_ids(self) -> None:
        btn = _make_accessible("OK", "push button")

        def mock_resolve(eid: str) -> MagicMock:
            if eid == "0/1":
                return btn
            msg = f"Element not found: {eid}"
            raise ValueError(msg)

        with patch.object(accessibility, "_resolve_element", side_effect=mock_resolve):
            result = accessibility.get_elements_by_ids(["0/1", "99/99"])

        assert result["success"] is True
        assert len(result["elements"]) == 1
        assert result["missing"] == ["99/99"]

    def test_empty_list(self) -> None:
        result = accessibility.get_elements_by_ids([])

        assert result["success"] is True
        assert result["elements"] == []
        assert result["missing"] == []

    def test_all_missing(self) -> None:
        def mock_resolve(eid: str) -> MagicMock:
            msg = f"Element not found: {eid}"
            raise ValueError(msg)

        with patch.object(accessibility, "_resolve_element", side_effect=mock_resolve):
            result = accessibility.get_elements_by_ids(["99/1", "99/2"])

        assert result["success"] is True
        assert result["elements"] == []
        assert len(result["missing"]) == 2
