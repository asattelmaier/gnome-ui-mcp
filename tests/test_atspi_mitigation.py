"""Tests for the AT-SPI use-after-free mitigation in desktop/accessibility.py.

Background: GNOME/at-spi2-core#178 — iterating the AT-SPI accessible-object
cache can hand back freed GObjects when queries overlap with UI churn (e.g.
Chrome tabs opening/closing). The mitigation serialises tree walks with a
global lock, enforces a minimum interval between application-list walks,
and verifies each child is still alive (via get_role_name) before recursing.
"""

from __future__ import annotations

import inspect
import threading
from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.desktop import accessibility as acc

# ---------------------------------------------------------------------------
# _throttled_tree_walk
# ---------------------------------------------------------------------------


@pytest.fixture
def _reset_throttle():
    acc._last_tree_walk_time = 0.0
    yield
    acc._last_tree_walk_time = 0.0


class TestThrottle:
    """_throttled_tree_walk enforces _MIN_TREE_WALK_INTERVAL_S between calls."""

    def test_first_call_does_not_sleep(self, _reset_throttle: None) -> None:
        # _last_tree_walk_time is 0.0; elapsed is huge, no sleep expected.
        with patch.object(acc.time, "sleep") as mock_sleep:
            acc._throttled_tree_walk()
        mock_sleep.assert_not_called()

    def test_immediate_second_call_sleeps_remaining_interval(self, _reset_throttle: None) -> None:
        interval = acc._MIN_TREE_WALK_INTERVAL_S
        # Pretend the first call just happened.
        with patch.object(acc.time, "monotonic", side_effect=[100.0, 100.0]):
            acc._last_tree_walk_time = 100.0 - interval / 2  # half-interval elapsed
            with patch.object(acc.time, "sleep") as mock_sleep:
                acc._throttled_tree_walk()

        mock_sleep.assert_called_once()
        slept = mock_sleep.call_args.args[0]
        # Should sleep approximately the remaining half of the interval.
        assert slept == pytest.approx(interval / 2, abs=1e-9)

    def test_call_after_interval_does_not_sleep(self, _reset_throttle: None) -> None:
        interval = acc._MIN_TREE_WALK_INTERVAL_S
        # Pretend more than the interval has elapsed.
        with patch.object(acc.time, "monotonic", side_effect=[100.0, 100.0]):
            acc._last_tree_walk_time = 100.0 - (interval * 2)
            with patch.object(acc.time, "sleep") as mock_sleep:
                acc._throttled_tree_walk()
        mock_sleep.assert_not_called()

    def test_updates_last_walk_time(self, _reset_throttle: None) -> None:
        with patch.object(acc.time, "sleep"):
            with patch.object(acc.time, "monotonic", side_effect=[200.0, 200.5]):
                acc._throttled_tree_walk()
        assert acc._last_tree_walk_time == 200.5


# ---------------------------------------------------------------------------
# _iter_applications calls _throttled_tree_walk before touching AT-SPI
# ---------------------------------------------------------------------------


class TestIterApplicationsThrottled:
    def test_throttle_called_before_desktop_query(self) -> None:
        order: list[str] = []

        def fake_throttle() -> None:
            order.append("throttle")

        fake_desktop = MagicMock()
        fake_desktop.get_child_count.return_value = 0

        def fake_desktop_fn() -> object:
            order.append("desktop")
            return fake_desktop

        with (
            patch.object(acc, "_throttled_tree_walk", fake_throttle),
            patch.object(acc, "_desktop", fake_desktop_fn),
        ):
            list(acc._iter_applications())

        assert order == ["throttle", "desktop"]


# ---------------------------------------------------------------------------
# Child liveness check in _walk_tree
# ---------------------------------------------------------------------------


def _make_accessible(
    *, children: list[MagicMock] | None = None, role_name: str | None = "frame"
) -> MagicMock:
    """Build a mock Atspi.Accessible with a given child list and role."""
    children = children or []
    m = MagicMock()
    m.get_child_count.return_value = len(children)
    m.get_child_at_index.side_effect = lambda idx: children[idx]
    if role_name is None:
        m.get_role_name.side_effect = Exception("freed gobject")
    else:
        m.get_role_name.return_value = role_name
    return m


class TestWalkTreeLivenessGuard:
    """_walk_tree must skip children whose get_role_name fails (use-after-free)."""

    def test_dead_child_skipped(self) -> None:
        live = _make_accessible(role_name="button")
        dead = _make_accessible(role_name=None)  # raises in get_role_name
        parent = _make_accessible(children=[dead, live])

        walked = list(acc._walk_tree(parent, (), depth=0, max_depth=5))
        walked_objects = [w[0] for w in walked]

        assert parent in walked_objects
        assert live in walked_objects
        assert dead not in walked_objects
        # The dead child's get_child_at_index must never be called.
        dead.get_child_count.assert_not_called()

    def test_all_live_children_walked(self) -> None:
        c1 = _make_accessible(role_name="label")
        c2 = _make_accessible(role_name="button")
        parent = _make_accessible(children=[c1, c2])

        walked = [w[0] for w in acc._walk_tree(parent, (), depth=0, max_depth=5)]
        assert c1 in walked
        assert c2 in walked

    def test_paths_unaffected_by_dead_index(self) -> None:
        """The walk must still report the original index path (index 1) for
        the surviving sibling, not collapse the indices after skipping."""
        dead = _make_accessible(role_name=None)
        live = _make_accessible(role_name="button")
        parent = _make_accessible(children=[dead, live])

        walked = list(acc._walk_tree(parent, (), depth=0, max_depth=5))
        live_entry = next(w for w in walked if w[0] is live)
        # live is at index 1 in the parent
        assert live_entry[1] == (1,)


# ---------------------------------------------------------------------------
# Child liveness check in _serialize_tree
# ---------------------------------------------------------------------------


class TestSerializeTreeLivenessGuard:
    """_serialize_tree must skip dead children just like _walk_tree."""

    def test_dead_child_not_serialized(self) -> None:
        from gnome_ui_mcp.desktop.types import TreeOptions

        # _serialize_tree builds an element summary from the accessible;
        # only the live one should reach that path.
        live = _make_accessible(role_name="button")
        dead = _make_accessible(role_name=None)
        parent = _make_accessible(role_name="frame", children=[dead, live])

        with patch.object(acc, "_element_summary") as mock_summary:
            mock_summary.return_value = {"role_name": "frame", "states": ["showing"]}
            acc._serialize_tree(parent, (), depth=0, opts=TreeOptions(max_depth=3))

        # _element_summary called for each accessible we serialise -- never
        # for the dead one.
        summarised = [c.args[0] for c in mock_summary.call_args_list]
        assert dead not in summarised


# ---------------------------------------------------------------------------
# Tree-walk lock serialises top-level entry points
# ---------------------------------------------------------------------------


class TestTreeWalkLock:
    """_visible_shell_popup_state, accessibility_tree, find_elements must
    acquire _TREE_WALK_LOCK so concurrent callers serialise on the AT-SPI
    cache iteration (mitigates the libatk-bridge race)."""

    def test_visible_shell_popup_state_holds_lock_during_query(self) -> None:
        # When the inner query runs, the lock must be held.
        def assert_lock_held(*_args, **_kwargs):
            assert acc._TREE_WALK_LOCK.locked()
            return []

        with patch.object(acc, "_visible_shell_popup_matches", side_effect=assert_lock_held):
            acc._visible_shell_popup_state(max_depth=3)

        # Lock released after.
        assert not acc._TREE_WALK_LOCK.locked()

    def test_concurrent_popup_state_serialised(self) -> None:
        """Two threads calling _visible_shell_popup_state must not have their
        inner queries overlap."""
        active = 0
        max_concurrent = 0
        gate = threading.Lock()

        def slow_query(*_args, **_kwargs):
            nonlocal active, max_concurrent
            with gate:
                active += 1
                max_concurrent = max(max_concurrent, active)
            # Hold long enough that a second thread would catch us if not
            # serialised.
            import time as _t

            _t.sleep(0.05)
            with gate:
                active -= 1
            return []

        with patch.object(acc, "_visible_shell_popup_matches", side_effect=slow_query):
            t1 = threading.Thread(target=acc._visible_shell_popup_state)
            t2 = threading.Thread(target=acc._visible_shell_popup_state)
            t1.start()
            t2.start()
            t1.join()
            t2.join()

        assert max_concurrent == 1


# ---------------------------------------------------------------------------
# wait_for_shell_settled default poll interval (50 → 150 ms)
# ---------------------------------------------------------------------------


class TestSettlePollInterval:
    def test_default_poll_interval_is_150ms(self) -> None:
        sig = inspect.signature(acc.wait_for_shell_settled)
        assert sig.parameters["poll_interval_ms"].default == 150
