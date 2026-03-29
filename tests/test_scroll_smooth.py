"""Tests for scroll_smooth (non-discrete smooth scrolling)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.desktop import input as input_mod
from gnome_ui_mcp.desktop.input import _StageArea


def _mock_ensure_session(stage: _StageArea | None = None) -> MagicMock:
    if stage is None:
        stage = _StageArea(origin_x=0, origin_y=0, width=1920, height=1080)
    return MagicMock(return_value=("/stream/0", stage))


class TestMutterScrollSmooth:
    def test_vertical_scroll_calls_axis(self) -> None:
        remote = input_mod._REMOTE_INPUT
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_call_session") as mock_call,
        ):
            result = remote.scroll_smooth(500, 300, dy=10.0)

        call_names = [c.args[0] for c in mock_call.call_args_list]
        assert "NotifyPointerMotionAbsolute" in call_names
        assert "NotifyPointerAxis" in call_names
        assert "NotifyPointerAxisFinish" in call_names
        assert result["success"] is True
        assert result["dy"] == 10.0

    def test_horizontal_scroll(self) -> None:
        remote = input_mod._REMOTE_INPUT
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_call_session") as mock_call,
        ):
            result = remote.scroll_smooth(500, 300, dx=5.0)

        call_names = [c.args[0] for c in mock_call.call_args_list]
        assert "NotifyPointerAxis" in call_names
        assert result["dx"] == 5.0

    def test_out_of_bounds_raises(self) -> None:
        remote = input_mod._REMOTE_INPUT
        stage = _StageArea(origin_x=0, origin_y=0, width=1920, height=1080)
        with patch.object(remote, "_ensure_session", MagicMock(return_value=("/s", stage))):
            with pytest.raises(ValueError, match="outside"):
                remote.scroll_smooth(2000, 500, dy=10.0)


class TestScrollSmoothWrapper:
    def test_calls_remote_input(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "scroll_smooth",
            return_value={"success": True, "backend": "mutter-remote-desktop"},
        ) as mock_method:
            result = input_mod.scroll_smooth(100, 200, dy=5.0)

        assert result["success"] is True
        mock_method.assert_called_once_with(100, 200, dx=0.0, dy=5.0)
