"""Tests for drag tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.desktop import input as input_mod
from gnome_ui_mcp.desktop.input import _StageArea


def _mock_ensure_session(stage: _StageArea | None = None) -> MagicMock:
    if stage is None:
        stage = _StageArea(origin_x=0, origin_y=0, width=1920, height=1080)
    return MagicMock(return_value=("/stream/0", stage))


class TestDragMutterCallSequence:
    """Verify the D-Bus call sequence: move → press → intermediate moves → release."""

    def test_drag_calls_move_press_moves_release(self) -> None:
        remote = input_mod._REMOTE_INPUT
        mock_session = MagicMock()
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_rd_session", mock_session),
        ):
            result = remote.drag_to(100, 100, 300, 100, button="left", steps=3, duration_ms=0)

        call_names = [c.args[0] for c in mock_session.call_sync.call_args_list]
        # Should be: move-to-start, press, 3 intermediate moves, release
        assert call_names[0] == "NotifyPointerMotionAbsolute"
        assert call_names[1] == "NotifyPointerButton"  # press
        # 3 motion calls
        motion_calls = [n for n in call_names[2:-1] if n == "NotifyPointerMotionAbsolute"]
        assert len(motion_calls) == 3
        assert call_names[-1] == "NotifyPointerButton"  # release
        assert result["success"] is True
        assert result["click_count"] == 1

    def test_drag_sends_correct_button_code(self) -> None:
        remote = input_mod._REMOTE_INPUT
        mock_session = MagicMock()
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_rd_session", mock_session),
        ):
            remote.drag_to(100, 100, 200, 200, button="right", steps=1, duration_ms=0)

        # Find the press call (second call) and check button code
        press_call = mock_session.call_sync.call_args_list[1]
        variant = press_call.args[1]
        button_code, state = variant.unpack()
        assert button_code == 0x111  # right button
        assert state is True  # press


class TestDragButtonRelease:
    """Button release MUST happen even on error (try/finally)."""

    def test_release_on_motion_error(self) -> None:
        remote = input_mod._REMOTE_INPUT
        mock_session = MagicMock()
        call_count = [0]

        def side_effect(method, params, *args, **kwargs):
            call_count[0] += 1
            # Fail on 4th call (first intermediate motion)
            if call_count[0] == 4:
                from gi.repository import GLib

                raise GLib.Error("motion failed")
            return None

        mock_session.call_sync.side_effect = side_effect
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_rd_session", mock_session),
        ):
            with pytest.raises(Exception, match="motion failed"):
                remote.drag_to(100, 100, 300, 100, steps=5, duration_ms=0)

        # The LAST call should be a release (NotifyPointerButton with state=False)
        last_call = mock_session.call_sync.call_args_list[-1]
        assert last_call.args[0] == "NotifyPointerButton"
        _code, state = last_call.args[1].unpack()
        assert state is False


class TestDragValidation:
    def test_invalid_button_raises(self) -> None:
        with pytest.raises(ValueError, match="button"):
            input_mod._REMOTE_INPUT.drag_to(0, 0, 100, 100, button="invalid")

    def test_steps_zero_still_moves_to_end(self) -> None:
        remote = input_mod._REMOTE_INPUT
        mock_session = MagicMock()
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_rd_session", mock_session),
        ):
            result = remote.drag_to(100, 100, 300, 200, steps=0, duration_ms=0)

        call_names = [c.args[0] for c in mock_session.call_sync.call_args_list]
        # move-to-start, press, move-to-end, release (4 calls minimum)
        assert "NotifyPointerMotionAbsolute" in call_names
        assert result["success"] is True


class TestDragAtspi:
    def test_atspi_fallback_uses_press_move_release(self) -> None:
        with patch.object(input_mod, "Atspi") as mock_atspi:
            mock_atspi.generate_mouse_event.return_value = True
            result = input_mod._perform_drag_atspi(
                100, 100, 300, 200, button="left", steps=2, duration_ms=0
            )

        calls = mock_atspi.generate_mouse_event.call_args_list
        # abs move to start, b1p press, 2 abs intermediate, b1r release
        event_names = [c.args[2] for c in calls]
        assert event_names[0] == "abs"  # move to start
        assert event_names[1] == "b1p"  # press
        assert event_names[-1] == "b1r"  # release
        assert result["success"] is True


class TestPerformDrag:
    def test_tries_mutter_first(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "drag_to",
            return_value={"success": True, "backend": "mutter-remote-desktop"},
        ) as mock_drag:
            result = input_mod.perform_drag(100, 100, 200, 200)

        assert result["backend"] == "mutter-remote-desktop"
        mock_drag.assert_called_once()

    def test_falls_back_to_atspi(self) -> None:
        with (
            patch.object(input_mod._REMOTE_INPUT, "drag_to", side_effect=RuntimeError("fail")),
            patch.object(input_mod, "_perform_drag_atspi") as mock_atspi,
        ):
            mock_atspi.return_value = {"success": True, "backend": "atspi"}
            result = input_mod.perform_drag(100, 100, 200, 200)

        assert result["backend"] == "atspi"
        assert "fail" in result["fallback_error"]
