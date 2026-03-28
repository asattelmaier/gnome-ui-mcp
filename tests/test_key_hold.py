"""Tests for key hold (key_down / key_up) support."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import input as input_mod


class TestMutterKeyDown:
    def test_calls_keysym_with_pressed_true(self) -> None:
        remote = input_mod._MutterRemoteDesktopInput()
        remote._ensure_session = MagicMock(return_value=("stream", MagicMock()))
        remote._call_session = MagicMock()

        result = remote.key_down("Control_L")

        calls = remote._call_session.call_args_list
        assert len(calls) == 1
        assert calls[0].args[0] == "NotifyKeyboardKeysym"
        variant = calls[0].args[1]
        keyval, pressed = variant.unpack()
        assert pressed is True
        assert result["success"] is True
        assert result["key_name"] == "Control_L"

    def test_tracks_held_key(self) -> None:
        remote = input_mod._MutterRemoteDesktopInput()
        remote._ensure_session = MagicMock(return_value=("stream", MagicMock()))
        remote._call_session = MagicMock()

        remote.key_down("Shift_L")

        assert "Shift_L" in remote._held_keys

    def test_invalid_key_name_raises(self) -> None:
        remote = input_mod._MutterRemoteDesktopInput()
        remote._ensure_session = MagicMock(return_value=("stream", MagicMock()))

        with patch(
            "gnome_ui_mcp.desktop.input._key_name_to_keyval", side_effect=ValueError("Unknown key")
        ):
            try:
                remote.key_down("NotARealKeyName_XYZ_999")
                assert False, "Should have raised ValueError"
            except ValueError:
                pass


class TestMutterKeyUp:
    def test_calls_keysym_with_pressed_false(self) -> None:
        remote = input_mod._MutterRemoteDesktopInput()
        remote._ensure_session = MagicMock(return_value=("stream", MagicMock()))
        remote._call_session = MagicMock()
        remote._held_keys = {"Return"}

        result = remote.key_up("Return")

        calls = remote._call_session.call_args_list
        assert len(calls) == 1
        assert calls[0].args[0] == "NotifyKeyboardKeysym"
        variant = calls[0].args[1]
        keyval, pressed = variant.unpack()
        assert pressed is False
        assert result["success"] is True

    def test_removes_from_held_keys(self) -> None:
        remote = input_mod._MutterRemoteDesktopInput()
        remote._ensure_session = MagicMock(return_value=("stream", MagicMock()))
        remote._call_session = MagicMock()
        remote._held_keys = {"Alt_L"}

        remote.key_up("Alt_L")

        assert "Alt_L" not in remote._held_keys

    def test_unheld_key_raises(self) -> None:
        remote = input_mod._MutterRemoteDesktopInput()
        remote._ensure_session = MagicMock(return_value=("stream", MagicMock()))
        remote._held_keys = set()

        try:
            remote.key_up("Control_L")
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "not currently held" in str(exc).lower()


class TestModuleLevelKeyHold:
    def test_key_down_delegates_to_remote_input(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "key_down",
            return_value={
                "success": True,
                "key_name": "Shift_L",
                "keyval": 65505,
                "backend": "mutter-remote-desktop",
            },
        ) as mock:
            result = input_mod.key_down("Shift_L")

        mock.assert_called_once_with("Shift_L")
        assert result["success"] is True

    def test_key_up_delegates_to_remote_input(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "key_up",
            return_value={
                "success": True,
                "key_name": "Shift_L",
                "keyval": 65505,
                "backend": "mutter-remote-desktop",
            },
        ) as mock:
            result = input_mod.key_up("Shift_L")

        mock.assert_called_once_with("Shift_L")
        assert result["success"] is True

    def test_key_down_atspi_fallback(self) -> None:
        with (
            patch.object(
                input_mod._REMOTE_INPUT, "key_down", side_effect=RuntimeError("no session")
            ),
            patch("gnome_ui_mcp.desktop.input.Atspi") as mock_atspi,
            patch("gnome_ui_mcp.desktop.input._key_name_to_keyval", return_value=65505),
        ):
            mock_atspi.KeySynthType.PRESS = 0
            mock_atspi.generate_keyboard_event.return_value = True

            result = input_mod.key_down("Shift_L")

        mock_atspi.generate_keyboard_event.assert_called_once_with(65505, "Shift_L", 0)
        assert result["success"] is True
        assert result["backend"] == "atspi"
        assert "fallback_error" in result

    def test_key_up_atspi_fallback(self) -> None:
        with (
            patch.object(input_mod._REMOTE_INPUT, "key_up", side_effect=RuntimeError("no session")),
            patch("gnome_ui_mcp.desktop.input.Atspi") as mock_atspi,
            patch("gnome_ui_mcp.desktop.input._key_name_to_keyval", return_value=65505),
        ):
            mock_atspi.KeySynthType.RELEASE = 1
            mock_atspi.generate_keyboard_event.return_value = True

            result = input_mod.key_up("Shift_L")

        mock_atspi.generate_keyboard_event.assert_called_once_with(65505, "Shift_L", 1)
        assert result["success"] is True
        assert result["backend"] == "atspi"


class TestCloseReleasesHeldKeys:
    def test_close_releases_all_held_keys(self) -> None:
        remote = input_mod._MutterRemoteDesktopInput()
        remote._rd_session = MagicMock()
        remote._started = True
        remote._held_keys = {"Control_L", "Shift_L"}
        remote._call_session = MagicMock()

        remote.close()

        # Should have called NotifyKeyboardKeysym with False for each held key
        release_calls = [
            c for c in remote._call_session.call_args_list if c.args[0] == "NotifyKeyboardKeysym"
        ]
        assert len(release_calls) == 2
        for call in release_calls:
            _keyval, pressed = call.args[1].unpack()
            assert pressed is False
