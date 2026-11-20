"""Tests for touch_rotate (two-finger rotation gesture)."""

from __future__ import annotations

import math
from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.desktop import input as input_mod
from gnome_ui_mcp.desktop.input import _StageArea

_real_seat_has_touch = input_mod._seat_has_touch


@pytest.fixture(autouse=True)
def seat_has_touch():
    """Run each test as if the seat already had a touch device, unless it says otherwise."""
    with patch.object(input_mod, "_seat_has_touch", return_value=True) as mock_seat:
        yield mock_seat


def _mock_ensure_session(stage: _StageArea | None = None) -> MagicMock:
    if stage is None:
        stage = _StageArea(origin_x=0, origin_y=0, width=1920, height=1080)
    return MagicMock(return_value=("/stream/0", stage))


class TestMutterTouchRotate:
    def test_emits_touch_down_motion_up(self) -> None:
        remote = input_mod._REMOTE_INPUT
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_call_session") as mock_call,
            patch("time.sleep"),
            patch(
                "time.monotonic",
                side_effect=[0.0] + [i * 0.01 for i in range(200)],
            ),
        ):
            result = remote.touch_rotate(
                960, 540, 0.0, math.pi / 2, 100.0, duration_ms=400, steps=5
            )

        call_names = [c.args[0] for c in mock_call.call_args_list]
        # 2 TouchDown + 10 TouchMotion (2 per step x 5 steps) + 2 TouchUp = 14
        assert call_names.count("NotifyTouchDown") == 2
        assert call_names.count("NotifyTouchUp") == 2
        assert call_names.count("NotifyTouchMotion") == 10
        assert result["success"] is True
        assert result["start_angle"] == 0.0
        assert result["end_angle"] == math.pi / 2
        assert result["backend"] == "mutter-remote-desktop"

    def test_out_of_bounds_raises(self) -> None:
        remote = input_mod._REMOTE_INPUT
        stage = _StageArea(origin_x=0, origin_y=0, width=1920, height=1080)
        with patch.object(remote, "_ensure_session", MagicMock(return_value=("/s", stage))):
            with pytest.raises(ValueError, match="outside"):
                remote.touch_rotate(2000, 540, 0.0, 1.0, 100.0)


class TestTouchWake:
    def _rotate(self, remote) -> None:
        remote.touch_rotate(960, 540, 0.0, math.pi / 2, 100.0, duration_ms=0, steps=1)

    def _events(self, mock_call) -> list[tuple[str, tuple]]:
        return [(c.args[0], c.args[1].unpack()) for c in mock_call.call_args_list]

    def test_no_extra_touch_when_the_seat_has_touch(self, seat_has_touch) -> None:
        remote = input_mod._REMOTE_INPUT
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_call_session") as mock_call,
            patch("time.sleep"),
        ):
            self._rotate(remote)

        names = [name for name, _ in self._events(mock_call)]
        assert names == ["NotifyTouchDown"] * 2 + ["NotifyTouchMotion"] * 2 + ["NotifyTouchUp"] * 2

    def test_no_extra_touch_when_the_seat_cannot_be_read(self, seat_has_touch) -> None:
        seat_has_touch.return_value = None
        remote = input_mod._REMOTE_INPUT
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_call_session") as mock_call,
            patch("time.sleep"),
        ):
            self._rotate(remote)

        assert [name for name, _ in self._events(mock_call)].count("NotifyTouchDown") == 2

    def test_a_throwaway_touch_comes_first_when_the_seat_has_no_touch(self, seat_has_touch) -> None:
        seat_has_touch.side_effect = [False, False, True]
        remote = input_mod._REMOTE_INPUT
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_call_session") as mock_call,
            patch("time.sleep") as mock_sleep,
            patch("time.monotonic", return_value=0.0),
        ):
            self._rotate(remote)

        events = self._events(mock_call)
        assert events[0] == ("NotifyTouchDown", ("/stream/0", 0, 1060.0, 540.0))
        assert events[1] == ("NotifyTouchUp", (0,))
        assert [name for name, _ in events[2:]] == (
            ["NotifyTouchDown"] * 2 + ["NotifyTouchMotion"] * 2 + ["NotifyTouchUp"] * 2
        )
        assert events[2] == ("NotifyTouchDown", ("/stream/0", 0, 1060.0, 540.0))
        assert mock_sleep.call_count == 1

    def test_the_wait_for_touch_gives_up_after_the_timeout(self, seat_has_touch) -> None:
        seat_has_touch.return_value = False
        clock = iter([0.0, 0.1, 0.3, 0.6])
        remote = input_mod._REMOTE_INPUT
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_call_session") as mock_call,
            patch("time.sleep") as mock_sleep,
            patch("time.monotonic", side_effect=lambda: next(clock, 1.0)),
        ):
            self._rotate(remote)

        assert mock_sleep.call_count == 2
        assert [name for name, _ in self._events(mock_call)].count("NotifyTouchDown") == 3


class TestSeatHasTouch:
    def _display(self, name: str, capabilities) -> MagicMock:
        display = MagicMock()
        type(display).__name__ = name
        display.get_default_seat.return_value.get_capabilities.return_value = capabilities
        return display

    def test_none_without_a_display(self) -> None:
        with patch.object(input_mod.Gdk.Display, "get_default", return_value=None):
            assert _real_seat_has_touch() is None

    def test_none_on_a_display_that_is_not_wayland(self) -> None:
        display = self._display("GdkX11Display", input_mod.Gdk.SeatCapabilities.TOUCH)
        with patch.object(input_mod.Gdk.Display, "get_default", return_value=display):
            assert _real_seat_has_touch() is None

    def test_reads_the_touch_capability_of_a_wayland_seat(self) -> None:
        caps = input_mod.Gdk.SeatCapabilities
        with_touch = self._display("GdkWaylandDisplay", caps.POINTER | caps.TOUCH)
        without_touch = self._display("GdkWaylandDisplay", caps.POINTER | caps.KEYBOARD)
        with patch.object(input_mod.Gdk.Display, "get_default", return_value=with_touch):
            assert _real_seat_has_touch() is True
        with patch.object(input_mod.Gdk.Display, "get_default", return_value=without_touch):
            assert _real_seat_has_touch() is False

    def test_none_when_the_seat_cannot_be_read(self) -> None:
        display = self._display("GdkWaylandDisplay", None)
        display.get_default_seat.side_effect = RuntimeError("no seat")
        with patch.object(input_mod.Gdk.Display, "get_default", return_value=display):
            assert _real_seat_has_touch() is None


class TestTouchRotateWrapper:
    def test_delegates_to_remote_input(self) -> None:
        fake = {
            "success": True,
            "center_x": 500,
            "center_y": 500,
            "backend": "mutter-remote-desktop",
        }
        with patch.object(
            input_mod._REMOTE_INPUT, "touch_rotate", return_value=fake
        ) as mock_method:
            result = input_mod.touch_rotate(500, 500, 0.0, 1.57, 100.0)

        assert result["success"] is True
        mock_method.assert_called_once_with(500, 500, 0.0, 1.57, 100.0, duration_ms=400)
