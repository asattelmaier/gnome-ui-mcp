"""Tests for get_focused_element MCP tool.

Verifies that the tool wraps current_focus_metadata() and returns properly
structured results via the desktop and server layers.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import accessibility

JsonDict = dict[str, Any]


def _make_state_set(*, focused: bool = False, active: bool = False) -> MagicMock:
    ss = MagicMock()

    def contains(state_type: Any) -> bool:
        from gi.repository import Atspi

        if state_type == Atspi.StateType.FOCUSED:
            return focused
        if state_type == Atspi.StateType.ACTIVE:
            return active
        return False

    ss.contains.side_effect = contains
    ss.get_states.return_value = []
    return ss


def _make_accessible(
    name: str,
    role: str,
    *,
    focused: bool = False,
    active: bool = False,
    children: list[MagicMock] | None = None,
) -> MagicMock:
    mock = MagicMock()
    mock.get_name.return_value = name
    mock.get_role_name.return_value = role
    mock.get_description.return_value = ""
    mock.get_state_set.return_value = _make_state_set(focused=focused, active=active)
    kids = children or []
    mock.get_child_count.return_value = len(kids)
    mock.get_child_at_index.side_effect = lambda i: kids[i] if i < len(kids) else None
    mock.get_component_iface.return_value = None
    mock.get_text_iface.return_value = None
    mock.get_editable_text_iface.return_value = None
    mock.get_n_actions.return_value = 0
    return mock


class TestGetFocusedElementReturnsMetadata:
    """get_focused_element should wrap current_focus_metadata in a success envelope."""

    def test_returns_success_with_element(self) -> None:
        focused_btn = _make_accessible("Save", "push button", focused=True)
        window = _make_accessible("Editor", "frame", active=True, children=[focused_btn])
        app = _make_accessible("gedit", "application", children=[window])
        desktop = _make_accessible("desktop", "desktop", children=[app])

        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.get_focused_element()

        assert result["success"] is True
        assert result["element"]["name"] == "Save"
        assert result["element"]["application"] == "gedit"


class TestGetFocusedElementNoFocus:
    """When nothing is focused, the tool should return success=True with element=None."""

    def test_returns_none_element_when_no_focus(self) -> None:
        window = _make_accessible("SomeWindow", "frame", focused=False, active=False)
        app = _make_accessible("idle-app", "application", children=[window])
        desktop = _make_accessible("desktop", "desktop", children=[app])

        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.get_focused_element()

        assert result["success"] is True
        assert result["element"] is None


class TestGetFocusedElementFields:
    """The returned element should contain all expected fields."""

    def test_element_has_expected_keys(self) -> None:
        focused_entry = _make_accessible("Search", "entry", focused=True)
        window = _make_accessible("Browser", "frame", active=True, children=[focused_entry])
        app = _make_accessible("firefox", "application", children=[window])
        desktop = _make_accessible("desktop", "desktop", children=[app])

        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.get_focused_element()

        assert result["success"] is True
        element = result["element"]
        expected_keys = {"id", "name", "role", "states", "bounds", "application", "editable"}
        assert expected_keys.issubset(set(element.keys()))

    def test_editable_field_present(self) -> None:
        focused_entry = _make_accessible("Input", "entry", focused=True)
        focused_entry.get_editable_text_iface.return_value = MagicMock()
        window = _make_accessible("App", "frame", active=True, children=[focused_entry])
        app = _make_accessible("myapp", "application", children=[window])
        desktop = _make_accessible("desktop", "desktop", children=[app])

        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.get_focused_element()

        assert result["success"] is True
        assert result["element"]["editable"] is True
