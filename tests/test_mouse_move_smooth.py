"""Tests for mouse_move_smooth (interpolated cursor movement)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import input as input_mod
from gnome_ui_mcp.desktop.input import _StageArea


def _mock_ensure_session(stage: _StageArea | None = None) -> MagicMock:
    if stage is None:
        stage = _StageArea(origin_x=0, origin_y=0, width=1920, height=1080)
    return MagicMock(return_value=("/stream/0", stage))


class TestMutterMoveToSmooth:
    def test_interpolates_positions(self) -> None:
        remote = input_mod._REMOTE_INPUT
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_call_session") as mock_call,
            patch("time.sleep"),
            patch("time.monotonic", side_effect=[0.0] + [i * 0.01 for i in range(100)]),
        ):
            result = remote.move_to_smooth(0, 0, 100, 100, duration_ms=200, steps=5)

        # 1 initial position + 5 interpolated steps = 6 calls
        assert mock_call.call_count == 6
        call_names = [c.args[0] for c in mock_call.call_args_list]
        assert all(name == "NotifyPointerMotionAbsolute" for name in call_names)
        assert result["success"] is True
        assert result["start_x"] == 0
        assert result["end_x"] == 100
        assert result["backend"] == "mutter-remote-desktop"

    def test_out_of_bounds_raises(self) -> None:
        import pytest

        remote = input_mod._REMOTE_INPUT
        stage = _StageArea(origin_x=0, origin_y=0, width=1920, height=1080)
        with patch.object(remote, "_ensure_session", MagicMock(return_value=("/s", stage))):
            with pytest.raises(ValueError, match="outside"):
                remote.move_to_smooth(0, 0, 2000, 500)


class TestMouseMoveSmoothWrapper:
    def test_atspi_fallback(self) -> None:
        with (
            patch.object(
                input_mod._REMOTE_INPUT, "move_to_smooth", side_effect=RuntimeError("no session")
            ),
            patch.object(input_mod, "Atspi") as mock_atspi,
            patch("time.sleep"),
            patch("time.monotonic", side_effect=[0.0] + [i * 0.01 for i in range(100)]),
        ):
            mock_atspi.generate_mouse_event.return_value = True
            result = input_mod.mouse_move_smooth(0, 0, 100, 100, duration_ms=200)

        assert result["success"] is True
        assert result["backend"] == "atspi"
        assert "no session" in result["fallback_error"]
        assert mock_atspi.generate_mouse_event.call_count > 1
