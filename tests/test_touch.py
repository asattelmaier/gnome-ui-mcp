"""Tests for touch input (tap, swipe, pinch, multi-finger swipe)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import input as input_mod


def _make_remote() -> input_mod._MutterRemoteDesktopInput:
    remote = input_mod._MutterRemoteDesktopInput()
    stage = MagicMock()
    stage.local_coordinates.side_effect = lambda x, y: (float(x), float(y))
    remote._ensure_session = MagicMock(return_value=("/stream", stage))
    remote._call_session = MagicMock()
    return remote


def _session_calls(remote: input_mod._MutterRemoteDesktopInput) -> list[tuple[str, tuple]]:
    """Extract (method_name, unpacked_args) from _call_session calls."""
    return [(c.args[0], c.args[1].unpack()) for c in remote._call_session.call_args_list]


class TestTouchTap:
    def test_calls_down_then_up(self) -> None:
        remote = _make_remote()
        remote.touch_tap(100, 200)

        calls = _session_calls(remote)
        down_calls = [c for c in calls if c[0] == "NotifyTouchDown"]
        up_calls = [c for c in calls if c[0] == "NotifyTouchUp"]
        assert len(down_calls) == 1
        assert len(up_calls) == 1

    def test_uses_slot_zero(self) -> None:
        remote = _make_remote()
        remote.touch_tap(50, 50)

        calls = _session_calls(remote)
        down = [c for c in calls if c[0] == "NotifyTouchDown"][0]
        # NotifyTouchDown(stream, slot, x, y)
        assert down[1][1] == 0  # slot

    def test_coordinates_passed_correctly(self) -> None:
        remote = _make_remote()
        remote.touch_tap(300, 400)

        calls = _session_calls(remote)
        down = [c for c in calls if c[0] == "NotifyTouchDown"][0]
        assert down[1][2] == 300.0  # x
        assert down[1][3] == 400.0  # y

    def test_hold_delays_release(self) -> None:
        remote = _make_remote()
        with patch("time.sleep") as mock_sleep:
            remote.touch_tap(100, 100, hold_ms=500)

        # Should sleep at least 500ms between down and up
        sleep_calls = [c.args[0] for c in mock_sleep.call_args_list]
        assert any(s >= 0.5 for s in sleep_calls)

    def test_returns_success(self) -> None:
        remote = _make_remote()
        result = remote.touch_tap(100, 100)
        assert result["success"] is True
        assert result["backend"] == "mutter-remote-desktop"


class TestTouchSwipe:
    def test_interpolates_motion(self) -> None:
        remote = _make_remote()
        with patch("time.sleep"):
            remote.touch_swipe(0, 0, 100, 100, duration_ms=300)

        calls = _session_calls(remote)
        motion_calls = [c for c in calls if c[0] == "NotifyTouchMotion"]
        assert len(motion_calls) >= 5  # should have multiple intermediate steps

    def test_endpoints_correct(self) -> None:
        remote = _make_remote()
        with patch("time.sleep"):
            remote.touch_swipe(10, 20, 300, 400, duration_ms=300)

        calls = _session_calls(remote)
        down = [c for c in calls if c[0] == "NotifyTouchDown"][0]
        # Down should be at start
        assert abs(down[1][2] - 10.0) < 1
        assert abs(down[1][3] - 20.0) < 1

        motions = [c for c in calls if c[0] == "NotifyTouchMotion"]
        # Last motion should be near end
        last_motion = motions[-1]
        assert abs(last_motion[1][2] - 300.0) < 15
        assert abs(last_motion[1][3] - 400.0) < 15

    def test_returns_success(self) -> None:
        remote = _make_remote()
        with patch("time.sleep"):
            result = remote.touch_swipe(0, 0, 100, 100, duration_ms=200)
        assert result["success"] is True


class TestTouchPinch:
    def test_uses_two_slots(self) -> None:
        remote = _make_remote()
        with patch("time.sleep"):
            remote.touch_pinch(500, 500, start_distance=50, end_distance=150, duration_ms=300)

        calls = _session_calls(remote)
        down_calls = [c for c in calls if c[0] == "NotifyTouchDown"]
        up_calls = [c for c in calls if c[0] == "NotifyTouchUp"]
        assert len(down_calls) == 2  # two fingers
        assert len(up_calls) == 2

        # Should use slots 0 and 1
        down_slots = {c[1][1] for c in down_calls}
        assert down_slots == {0, 1}

    def test_zoom_in_moves_apart(self) -> None:
        remote = _make_remote()
        with patch("time.sleep"):
            remote.touch_pinch(500, 500, start_distance=50, end_distance=150, duration_ms=300)

        calls = _session_calls(remote)
        down_calls = [c for c in calls if c[0] == "NotifyTouchDown"]

        # Fingers start close together (distance=50)
        x_coords = sorted([c[1][2] for c in down_calls])
        start_gap = x_coords[1] - x_coords[0]
        assert abs(start_gap - 100) < 5  # 2 * start_distance = 100

    def test_returns_success(self) -> None:
        remote = _make_remote()
        with patch("time.sleep"):
            result = remote.touch_pinch(
                500, 500, start_distance=50, end_distance=150, duration_ms=200
            )
        assert result["success"] is True


class TestTouchMultiSwipe:
    def test_uses_n_slots(self) -> None:
        remote = _make_remote()
        with patch("time.sleep"):
            remote.touch_multi_swipe(100, 500, 100, 200, fingers=3, duration_ms=300)

        calls = _session_calls(remote)
        down_calls = [c for c in calls if c[0] == "NotifyTouchDown"]
        up_calls = [c for c in calls if c[0] == "NotifyTouchUp"]
        assert len(down_calls) == 3
        assert len(up_calls) == 3

    def test_rejects_invalid_fingers(self) -> None:
        remote = _make_remote()
        try:
            remote.touch_multi_swipe(0, 0, 100, 100, fingers=0, duration_ms=200)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

        try:
            remote.touch_multi_swipe(0, 0, 100, 100, fingers=6, duration_ms=200)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_all_fingers_move(self) -> None:
        remote = _make_remote()
        with patch("time.sleep"):
            remote.touch_multi_swipe(100, 500, 100, 200, fingers=4, duration_ms=300)

        calls = _session_calls(remote)
        motion_calls = [c for c in calls if c[0] == "NotifyTouchMotion"]
        # Each finger should have multiple motion events
        slots_with_motion = {c[1][1] for c in motion_calls}
        assert len(slots_with_motion) == 4

    def test_returns_success(self) -> None:
        remote = _make_remote()
        with patch("time.sleep"):
            result = remote.touch_multi_swipe(0, 0, 100, 100, fingers=3, duration_ms=200)
        assert result["success"] is True


class TestModuleLevelTouch:
    def test_touch_tap_delegates(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "touch_tap",
            return_value={"success": True, "backend": "mutter-remote-desktop"},
        ) as mock:
            result = input_mod.touch_tap(50, 50)
        mock.assert_called_once_with(50, 50, hold_ms=0)
        assert result["success"] is True

    def test_touch_swipe_delegates(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "touch_swipe",
            return_value={"success": True, "backend": "mutter-remote-desktop"},
        ) as mock:
            result = input_mod.touch_swipe(0, 0, 100, 100, duration_ms=300)
        mock.assert_called_once_with(0, 0, 100, 100, duration_ms=300)
        assert result["success"] is True
