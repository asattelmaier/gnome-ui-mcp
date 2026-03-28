"""Tests for _is_showing O(1) optimization (PERF-3).

Verifies that _is_showing uses state_set.contains() directly instead of
the expensive _element_states path, and that behavior is preserved.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop.accessibility import _is_showing


def _make_accessible(*, showing: bool) -> MagicMock:
    """Create a mock Atspi.Accessible with a controllable state set."""
    mock = MagicMock()
    state_set = MagicMock()
    state_set.contains.return_value = showing
    mock.get_state_set.return_value = state_set
    return mock


class TestIsShowing:
    def test_returns_true_when_showing(self) -> None:
        acc = _make_accessible(showing=True)
        assert _is_showing(acc) is True

    def test_returns_false_when_not_showing(self) -> None:
        acc = _make_accessible(showing=False)
        assert _is_showing(acc) is False

    def test_returns_false_when_state_set_is_none(self) -> None:
        mock = MagicMock()
        mock.get_state_set.return_value = None
        assert _is_showing(mock) is False

    def test_returns_false_when_get_state_set_raises(self) -> None:
        mock = MagicMock()
        mock.get_state_set.side_effect = Exception("D-Bus error")
        assert _is_showing(mock) is False

    def test_does_not_call_element_states(self) -> None:
        """The optimization must bypass _element_states entirely."""
        acc = _make_accessible(showing=True)
        with patch("gnome_ui_mcp.desktop.accessibility._element_states") as mock_element_states:
            _is_showing(acc)
            mock_element_states.assert_not_called()
