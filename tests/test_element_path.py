"""Tests for get_element_path (Item 5).

Verifies that the ancestry chain for a given element_id is resolved
and returned as a list of {id, name, role} dicts.
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
    return mock


def _make_desktop_tree() -> tuple[MagicMock, dict[str, MagicMock]]:
    """Build: desktop -> app(0) -> window(0/0) -> panel(0/0/1) -> button(0/0/1/2)"""
    button = _make_accessible("Save", "push button")
    button.get_child_count.return_value = 0
    button.get_child_at_index.side_effect = lambda i: None

    panel = _make_accessible("Toolbar", "panel")
    # panel has 3 children, button at index 2
    filler1 = _make_accessible("f1", "filler")
    filler1.get_child_count.return_value = 0
    filler1.get_child_at_index.side_effect = lambda i: None
    filler2 = _make_accessible("f2", "filler")
    filler2.get_child_count.return_value = 0
    filler2.get_child_at_index.side_effect = lambda i: None
    panel_kids = [filler1, filler2, button]
    panel.get_child_count.return_value = len(panel_kids)
    panel.get_child_at_index.side_effect = lambda i: panel_kids[i] if i < len(panel_kids) else None

    window = _make_accessible("Editor", "frame")
    window_kids = [panel]  # panel at index 0 -> need index 1 for path 0/0/1
    # Actually we need panel at index 1 for the path "0/0/1"
    filler_win = _make_accessible("sidebar", "panel")
    filler_win.get_child_count.return_value = 0
    filler_win.get_child_at_index.side_effect = lambda i: None
    window_kids = [filler_win, panel]
    window.get_child_count.return_value = len(window_kids)
    window.get_child_at_index.side_effect = (
        lambda i: window_kids[i] if i < len(window_kids) else None
    )

    app = _make_accessible("gedit", "application")
    app_kids = [window]
    app.get_child_count.return_value = len(app_kids)
    app.get_child_at_index.side_effect = lambda i: app_kids[i] if i < len(app_kids) else None

    desktop = _make_accessible("desktop", "desktop")
    desktop_kids = [app]
    desktop.get_child_count.return_value = len(desktop_kids)
    desktop.get_child_at_index.side_effect = (
        lambda i: desktop_kids[i] if i < len(desktop_kids) else None
    )

    nodes = {
        "desktop": desktop,
        "app": app,
        "window": window,
        "panel": panel,
        "button": button,
    }
    return desktop, nodes


class TestGetElementPath:
    """get_element_path should return the ancestry from root to element."""

    def test_returns_full_ancestry(self) -> None:
        desktop, nodes = _make_desktop_tree()
        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.get_element_path("0/0/1/2")

        assert result["success"] is True
        path = result["path"]
        assert len(path) == 4
        assert path[0]["id"] == "0"
        assert path[0]["name"] == "gedit"
        assert path[-1]["id"] == "0/0/1/2"
        assert path[-1]["name"] == "Save"

    def test_single_level_path(self) -> None:
        desktop, nodes = _make_desktop_tree()
        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.get_element_path("0")

        assert result["success"] is True
        assert len(result["path"]) == 1
        assert result["path"][0]["name"] == "gedit"

    def test_invalid_element_id(self) -> None:
        desktop, nodes = _make_desktop_tree()
        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.get_element_path("99/0/0")

        assert result["success"] is False

    def test_path_entries_have_expected_keys(self) -> None:
        desktop, nodes = _make_desktop_tree()
        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.get_element_path("0/0")

        assert result["success"] is True
        for entry in result["path"]:
            assert "id" in entry
            assert "name" in entry
            assert "role" in entry
