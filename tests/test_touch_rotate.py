"""Tests for touch_rotate (two-finger rotation gesture)."""

from __future__ import annotations

import math
from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.desktop import input as input_mod
from gnome_ui_mcp.desktop.input import _StageArea


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
