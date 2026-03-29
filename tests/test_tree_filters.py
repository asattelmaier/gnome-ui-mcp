"""Tests for accessibility_tree filter parameters (Item 7).

Verifies that filter_roles, filter_states, and showing_only parameters
cause _serialize_tree to skip non-matching nodes.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import accessibility


def _make_state_set(states: list[str]) -> MagicMock:
    ss = MagicMock()
    state_mocks = []
    for s in states:
        m = MagicMock()
        m.value_nick = s
        state_mocks.append(m)
    ss.get_states.return_value = state_mocks

    from gi.repository import Atspi

    state_map = {
        "showing": Atspi.StateType.SHOWING,
        "focused": Atspi.StateType.FOCUSED,
        "active": Atspi.StateType.ACTIVE,
    }

    def contains(st: Any) -> bool:
        for name, typ in state_map.items():
            if st == typ and name in states:
                return True
        return False

    ss.contains.side_effect = contains
    return ss


def _make_accessible(
    name: str,
    role: str,
    *,
    states: list[str] | None = None,
    children: list[MagicMock] | None = None,
) -> MagicMock:
    mock = MagicMock()
    mock.get_name.return_value = name
    mock.get_role_name.return_value = role
    mock.get_description.return_value = ""
    mock.get_state_set.return_value = _make_state_set(states or [])
    kids = children or []
    mock.get_child_count.return_value = len(kids)
    mock.get_child_at_index.side_effect = lambda i: kids[i] if i < len(kids) else None
    mock.get_component_iface.return_value = None
    mock.get_text_iface.return_value = None
    mock.get_editable_text_iface.return_value = None
    mock.get_n_actions.return_value = 0
    return mock


def _collect_names(tree: dict[str, Any]) -> list[str]:
    """Recursively collect all node names from a serialized tree."""
    names = [tree["name"]]
    for child in tree.get("children", []):
        names.extend(_collect_names(child))
    return names


class TestFilterRoles:
    """filter_roles should include only nodes with matching roles."""

    def test_filters_by_role(self) -> None:
        button = _make_accessible("Save", "push button", states=["showing"])
        label = _make_accessible("Title", "label", states=["showing"])
        panel = _make_accessible("Main", "panel", states=["showing"], children=[button, label])
        app = _make_accessible("app", "application", states=["showing"], children=[panel])
        desktop = _make_accessible("desktop", "desktop", children=[app])

        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.accessibility_tree(max_depth=4, filter_roles=["push button"])

        assert result["success"] is True
        names = _collect_names(result["trees"][0])
        assert "Save" in names
        assert "Title" not in names

    def test_empty_filter_roles_includes_all(self) -> None:
        button = _make_accessible("Save", "push button", states=["showing"])
        label = _make_accessible("Title", "label", states=["showing"])
        app = _make_accessible("app", "application", states=["showing"], children=[button, label])
        desktop = _make_accessible("desktop", "desktop", children=[app])

        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.accessibility_tree(max_depth=4, filter_roles=[])

        names = _collect_names(result["trees"][0])
        assert "Save" in names
        assert "Title" in names


class TestFilterStates:
    """filter_states should include only nodes that have all specified states."""

    def test_filters_by_state(self) -> None:
        focused = _make_accessible("Input", "entry", states=["showing", "focused"])
        unfocused = _make_accessible("Label", "label", states=["showing"])
        app = _make_accessible(
            "app", "application", states=["showing"], children=[focused, unfocused]
        )
        desktop = _make_accessible("desktop", "desktop", children=[app])

        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.accessibility_tree(max_depth=4, filter_states=["focused"])

        names = _collect_names(result["trees"][0])
        assert "Input" in names
        assert "Label" not in names


class TestShowingOnly:
    """showing_only=True should skip elements without 'showing' state."""

    def test_showing_only_filters_hidden(self) -> None:
        visible = _make_accessible("Visible", "push button", states=["showing"])
        hidden = _make_accessible("Hidden", "push button", states=[])
        app = _make_accessible("app", "application", states=["showing"], children=[visible, hidden])
        desktop = _make_accessible("desktop", "desktop", children=[app])

        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.accessibility_tree(max_depth=4, showing_only=True)

        names = _collect_names(result["trees"][0])
        assert "Visible" in names
        assert "Hidden" not in names

    def test_showing_only_false_includes_all(self) -> None:
        visible = _make_accessible("Visible", "push button", states=["showing"])
        hidden = _make_accessible("Hidden", "push button", states=[])
        app = _make_accessible("app", "application", states=["showing"], children=[visible, hidden])
        desktop = _make_accessible("desktop", "desktop", children=[app])

        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.accessibility_tree(max_depth=4, showing_only=False)

        names = _collect_names(result["trees"][0])
        assert "Visible" in names
        assert "Hidden" in names
