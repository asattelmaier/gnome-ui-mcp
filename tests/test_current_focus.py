"""Tests for current_focus_metadata optimization (PERF-2).

Verifies that the optimized version:
1. Returns the same result as before (deepest focused element)
2. Skips apps without active/focused windows
3. Prefers non-gnome-shell apps when both have focused elements
4. Falls back to gnome-shell if no other app has focus
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


class TestCurrentFocusSkipsInactiveApps:
    """Apps without active/focused windows should be skipped entirely."""

    def test_skips_app_with_no_active_window(self) -> None:
        # App with a window that is neither active nor focused
        window = _make_accessible("SomeWindow", "frame", focused=False, active=False)
        app = _make_accessible("idle-app", "application", children=[window])
        desktop = _make_accessible("desktop", "desktop", children=[app])

        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.current_focus_metadata()

        assert result is None

    def test_finds_focused_element_in_active_app(self) -> None:
        focused_btn = _make_accessible("OK", "push button", focused=True)
        window = _make_accessible("Dialog", "frame", active=True, children=[focused_btn])
        app = _make_accessible("my-app", "application", children=[window])
        desktop = _make_accessible("desktop", "desktop", children=[app])

        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.current_focus_metadata()

        assert result is not None
        assert result["name"] == "OK"
        assert result["application"] == "my-app"


class TestCurrentFocusGnomeShellFallback:
    """gnome-shell should only be used when no other app has a focused element."""

    def test_prefers_non_shell_app(self) -> None:
        # gnome-shell has a focused panel
        shell_focused = _make_accessible("Panel", "panel", focused=True)
        shell_window = _make_accessible("", "window", focused=True, children=[shell_focused])
        shell_app = _make_accessible("gnome-shell", "application", children=[shell_window])

        # tilix has a focused terminal
        terminal = _make_accessible("Terminal", "terminal", focused=True)
        tilix_window = _make_accessible("Tilix", "frame", active=True, children=[terminal])
        tilix_app = _make_accessible("tilix", "application", children=[tilix_window])

        desktop = _make_accessible("desktop", "desktop", children=[shell_app, tilix_app])

        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.current_focus_metadata()

        assert result is not None
        assert result["application"] == "tilix"
        assert result["name"] == "Terminal"

    def test_falls_back_to_shell_when_no_other_focus(self) -> None:
        shell_focused = _make_accessible("Activities", "label", focused=True)
        shell_window = _make_accessible("", "window", focused=True, children=[shell_focused])
        shell_app = _make_accessible("gnome-shell", "application", children=[shell_window])

        # Another app with an inactive window
        idle_window = _make_accessible("Idle", "frame", active=False, focused=False)
        idle_app = _make_accessible("idle-app", "application", children=[idle_window])

        desktop = _make_accessible("desktop", "desktop", children=[shell_app, idle_app])

        with patch.object(accessibility, "_desktop", return_value=desktop):
            result = accessibility.current_focus_metadata()

        assert result is not None
        assert result["application"] == "gnome-shell"
        assert result["name"] == "Activities"
