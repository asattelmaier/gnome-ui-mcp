"""Tests for mouse button hold (button_down / button_up) support."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import input as input_mod


class TestMutterButtonDown:
    def test_calls_motion_then_press(self) -> None:
        remote = input_mod._MutterRemoteDesktopInput()
        stage = MagicMock()
        stage.local_coordinates.return_value = (100.0, 200.0)
        remote._ensure_session = MagicMock(return_value=("/stream", stage))
        remote._call_session = MagicMock()

        result = remote.button_down(100, 200)

        calls = remote._call_session.call_args_list
        assert calls[0].args[0] == "NotifyPointerMotionAbsolute"
        assert calls[1].args[0] == "NotifyPointerButton"
        variant = calls[1].args[1]
        button_code, pressed = variant.unpack()
        assert button_code == 0x110  # left
        assert pressed is True
        assert result["success"] is True

    def test_right_button_uses_correct_code(self) -> None:
        remote = input_mod._MutterRemoteDesktopInput()
        stage = MagicMock()
        stage.local_coordinates.return_value = (50.0, 50.0)
        remote._ensure_session = MagicMock(return_value=("/stream", stage))
        remote._call_session = MagicMock()

        remote.button_down(50, 50, button="right")

        press_call = remote._call_session.call_args_list[1]
        button_code, _pressed = press_call.args[1].unpack()
        assert button_code == 0x111  # right

    def test_tracks_held_button(self) -> None:
        remote = input_mod._MutterRemoteDesktopInput()
        stage = MagicMock()
        stage.local_coordinates.return_value = (0.0, 0.0)
        remote._ensure_session = MagicMock(return_value=("/stream", stage))
        remote._call_session = MagicMock()

        remote.button_down(0, 0, button="middle")

        assert "middle" in remote._held_buttons

    def test_invalid_button_raises(self) -> None:
        remote = input_mod._MutterRemoteDesktopInput()
        remote._ensure_session = MagicMock(return_value=("/stream", MagicMock()))

        try:
            remote.button_down(0, 0, button="invalid")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestMutterButtonUp:
    def test_calls_motion_then_release(self) -> None:
        remote = input_mod._MutterRemoteDesktopInput()
        stage = MagicMock()
        stage.local_coordinates.return_value = (300.0, 400.0)
        remote._ensure_session = MagicMock(return_value=("/stream", stage))
        remote._call_session = MagicMock()
        remote._held_buttons = {"left"}

        result = remote.button_up(300, 400)

        calls = remote._call_session.call_args_list
        assert calls[0].args[0] == "NotifyPointerMotionAbsolute"
        assert calls[1].args[0] == "NotifyPointerButton"
        variant = calls[1].args[1]
        button_code, pressed = variant.unpack()
        assert button_code == 0x110
        assert pressed is False
        assert result["success"] is True

    def test_removes_from_held_buttons(self) -> None:
        remote = input_mod._MutterRemoteDesktopInput()
        stage = MagicMock()
        stage.local_coordinates.return_value = (0.0, 0.0)
        remote._ensure_session = MagicMock(return_value=("/stream", stage))
        remote._call_session = MagicMock()
        remote._held_buttons = {"left"}

        remote.button_up(0, 0, button="left")

        assert "left" not in remote._held_buttons

    def test_unheld_button_raises(self) -> None:
        remote = input_mod._MutterRemoteDesktopInput()
        remote._ensure_session = MagicMock(return_value=("/stream", MagicMock()))
        remote._held_buttons = set()

        try:
            remote.button_up(0, 0, button="left")
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "not currently held" in str(exc).lower()


class TestModuleLevelButtonHold:
    def test_button_down_delegates_to_remote_input(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "button_down",
            return_value={
                "success": True,
                "x": 10,
                "y": 20,
                "button": "left",
                "backend": "mutter-remote-desktop",
            },
        ) as mock:
            result = input_mod.mouse_button_down(10, 20)

        mock.assert_called_once_with(10, 20, button="left")
        assert result["success"] is True

    def test_button_up_delegates_to_remote_input(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "button_up",
            return_value={
                "success": True,
                "x": 10,
                "y": 20,
                "button": "left",
                "backend": "mutter-remote-desktop",
            },
        ) as mock:
            result = input_mod.mouse_button_up(10, 20)

        mock.assert_called_once_with(10, 20, button="left")
        assert result["success"] is True

    def test_button_down_atspi_fallback(self) -> None:
        with (
            patch.object(
                input_mod._REMOTE_INPUT, "button_down", side_effect=RuntimeError("no session")
            ),
            patch("gnome_ui_mcp.desktop.input.Atspi") as mock_atspi,
        ):
            mock_atspi.generate_mouse_event.return_value = True

            result = input_mod.mouse_button_down(100, 200, button="left")

        mock_atspi.generate_mouse_event.assert_called_once_with(100, 200, "b1p")
        assert result["success"] is True
        assert result["backend"] == "atspi"
        assert "fallback_error" in result

    def test_button_up_atspi_fallback(self) -> None:
        with (
            patch.object(
                input_mod._REMOTE_INPUT, "button_up", side_effect=RuntimeError("no session")
            ),
            patch("gnome_ui_mcp.desktop.input.Atspi") as mock_atspi,
        ):
            mock_atspi.generate_mouse_event.return_value = True

            result = input_mod.mouse_button_up(100, 200, button="right")

        mock_atspi.generate_mouse_event.assert_called_once_with(100, 200, "b3r")
        assert result["success"] is True
        assert result["backend"] == "atspi"


class TestCloseReleasesHeldButtons:
    def test_close_releases_all_held_buttons(self) -> None:
        remote = input_mod._MutterRemoteDesktopInput()
        remote._rd_session = MagicMock()
        remote._stream_path = "/stream"
        remote._stage_area = MagicMock()
        remote._stage_area.local_coordinates.return_value = (0.0, 0.0)
        remote._started = True
        remote._held_buttons = {"left", "right"}
        remote._held_keys = set()
        remote._call_session = MagicMock()

        remote.close()

        release_calls = [
            c for c in remote._call_session.call_args_list if c.args[0] == "NotifyPointerButton"
        ]
        assert len(release_calls) == 2
        for call in release_calls:
            _button_code, pressed = call.args[1].unpack()
            assert pressed is False
