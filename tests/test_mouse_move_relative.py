"""Tests for mouse_move_relative (relative pointer movement)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import input as input_mod
from gnome_ui_mcp.desktop.input import _StageArea


def _mock_ensure_session(stage: _StageArea | None = None) -> MagicMock:
    if stage is None:
        stage = _StageArea(origin_x=0, origin_y=0, width=1920, height=1080)
    return MagicMock(return_value=("/stream/0", stage))


class TestMutterMoveRelative:
    def test_calls_notify_pointer_motion_relative(self) -> None:
        remote = input_mod._REMOTE_INPUT
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_call_session") as mock_call,
        ):
            result = remote.move_relative(10.0, -5.0)

        call_names = [c.args[0] for c in mock_call.call_args_list]
        assert "NotifyPointerMotionRelative" in call_names
        assert result["success"] is True
        assert result["dx"] == 10.0
        assert result["dy"] == -5.0
        assert result["backend"] == "mutter-remote-desktop"


class TestMouseMoveRelativeWrapper:
    def test_mutter_success(self) -> None:
        fake = {
            "success": True,
            "dx": 10.0,
            "dy": -5.0,
            "backend": "mutter-remote-desktop",
        }
        with patch.object(
            input_mod._REMOTE_INPUT,
            "move_relative",
            return_value=fake,
        ):
            result = input_mod.mouse_move_relative(10.0, -5.0)

        assert result["success"] is True
        assert result["backend"] == "mutter-remote-desktop"

    def test_atspi_fallback(self) -> None:
        with (
            patch.object(
                input_mod._REMOTE_INPUT, "move_relative", side_effect=RuntimeError("no session")
            ),
            patch.object(input_mod, "Atspi") as mock_atspi,
        ):
            mock_atspi.generate_mouse_event.return_value = True
            result = input_mod.mouse_move_relative(10.0, -5.0)

        assert result["success"] is True
        assert result["backend"] == "atspi"
        assert "no session" in result["fallback_error"]
        mock_atspi.generate_mouse_event.assert_called_once_with(10, -5, "rel")
