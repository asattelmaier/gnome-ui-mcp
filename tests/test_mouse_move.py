"""Tests for mouse_move tool (move cursor without clicking)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import input as input_mod
from gnome_ui_mcp.desktop.input import _StageArea


def _mock_ensure_session(stage: _StageArea | None = None) -> MagicMock:
    """Return a mock _ensure_session that yields a fake stream + stage area."""
    if stage is None:
        stage = _StageArea(origin_x=0, origin_y=0, width=1920, height=1080)
    return MagicMock(return_value=("/stream/0", stage))


class TestMutterMoveToCallsCorrectDbus:
    """move_to must call NotifyPointerMotionAbsolute WITHOUT NotifyPointerButton."""

    def test_calls_motion_not_button(self) -> None:
        remote = input_mod._REMOTE_INPUT
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_call_session") as mock_call,
        ):
            result = remote.move_to(500, 300)

        call_names = [c.args[0] for c in mock_call.call_args_list]
        assert "NotifyPointerMotionAbsolute" in call_names
        assert "NotifyPointerButton" not in call_names
        assert result["success"] is True
        assert result["x"] == 500
        assert result["y"] == 300
        assert result["backend"] == "mutter-remote-desktop"

    def test_out_of_bounds_raises(self) -> None:
        import pytest

        remote = input_mod._REMOTE_INPUT
        stage = _StageArea(origin_x=0, origin_y=0, width=1920, height=1080)
        with patch.object(remote, "_ensure_session", MagicMock(return_value=("/s", stage))):
            with pytest.raises(ValueError, match="outside"):
                remote.move_to(2000, 500)


class TestPerformMouseMove:
    """perform_mouse_move tries Mutter, falls back to AT-SPI."""

    def test_mutter_success(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "move_to",
            return_value={"success": True, "x": 100, "y": 200, "backend": "mutter-remote-desktop"},
        ):
            result = input_mod.perform_mouse_move(100, 200)

        assert result["success"] is True
        assert result["backend"] == "mutter-remote-desktop"

    def test_atspi_fallback(self) -> None:
        with (
            patch.object(
                input_mod._REMOTE_INPUT, "move_to", side_effect=RuntimeError("no session")
            ),
            patch.object(input_mod, "Atspi") as mock_atspi,
        ):
            mock_atspi.generate_mouse_event.return_value = True
            result = input_mod.perform_mouse_move(100, 200)

        assert result["success"] is True
        assert result["backend"] == "atspi"
        assert "no session" in result["fallback_error"]
        mock_atspi.generate_mouse_event.assert_called_once_with(100, 200, "abs")
