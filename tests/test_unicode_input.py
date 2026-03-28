"""Tests for Unicode text input via clipboard approach."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import input as input_mod


class TestMutterTypeUnicode:
    def test_ascii_uses_direct_keyval(self) -> None:
        """ASCII text that fits in keymap should use direct keysym injection, not clipboard."""
        remote = input_mod._MutterRemoteDesktopInput()
        remote._ensure_session = MagicMock(return_value=("stream", MagicMock()))
        remote._call_session = MagicMock()

        result = remote.type_text("hello")

        # Should use NotifyKeyboardKeysym directly, not clipboard
        keysym_calls = [
            c for c in remote._call_session.call_args_list if c.args[0] == "NotifyKeyboardKeysym"
        ]
        assert len(keysym_calls) == 10  # 5 chars * 2 (press+release each)
        assert result["success"] is True
        assert result["backend"] == "mutter-remote-desktop"

    def test_cjk_uses_clipboard_approach(self) -> None:
        with (
            patch("subprocess.run") as mock_run,
            patch.object(
                input_mod._REMOTE_INPUT, "_ensure_session", return_value=("stream", MagicMock())
            ),
            patch.object(input_mod._REMOTE_INPUT, "_call_session"),
            patch("time.sleep"),
        ):
            # Mock wl-paste to return empty clipboard
            paste_result = MagicMock()
            paste_result.returncode = 0
            paste_result.stdout = b""
            # Mock wl-copy to succeed
            copy_result = MagicMock()
            copy_result.returncode = 0
            mock_run.side_effect = [paste_result, copy_result, copy_result]

            result = input_mod.type_unicode("测试中文")

        assert result["success"] is True
        assert result["method"] == "clipboard"
        # Should have called wl-copy with the Chinese text
        wl_copy_calls = [c for c in mock_run.call_args_list if "wl-copy" in str(c)]
        assert len(wl_copy_calls) >= 1

    def test_emoji_uses_clipboard_approach(self) -> None:
        with (
            patch("subprocess.run") as mock_run,
            patch.object(
                input_mod._REMOTE_INPUT, "_ensure_session", return_value=("stream", MagicMock())
            ),
            patch.object(input_mod._REMOTE_INPUT, "_call_session"),
            patch("time.sleep"),
        ):
            paste_result = MagicMock()
            paste_result.returncode = 0
            paste_result.stdout = b""
            copy_result = MagicMock()
            copy_result.returncode = 0
            mock_run.side_effect = [paste_result, copy_result, copy_result]

            result = input_mod.type_unicode("\U0001f600")

        assert result["success"] is True
        assert result["method"] == "clipboard"

    def test_clipboard_saved_and_restored(self) -> None:
        with (
            patch("subprocess.run") as mock_run,
            patch.object(
                input_mod._REMOTE_INPUT, "_ensure_session", return_value=("stream", MagicMock())
            ),
            patch.object(input_mod._REMOTE_INPUT, "_call_session"),
            patch("time.sleep"),
        ):
            paste_result = MagicMock()
            paste_result.returncode = 0
            paste_result.stdout = b"original clipboard"
            copy_result = MagicMock()
            copy_result.returncode = 0
            mock_run.side_effect = [paste_result, copy_result, copy_result]

            input_mod.type_unicode("测试")

        # First call: wl-paste (save)
        assert mock_run.call_args_list[0].args[0][0] == "wl-paste"
        # Last call: wl-copy to restore
        last_copy_call = mock_run.call_args_list[-1]
        assert "wl-copy" in str(last_copy_call)
        assert last_copy_call.kwargs.get("input") == b"original clipboard"

    def test_empty_string_returns_immediately(self) -> None:
        result = input_mod.type_unicode("")
        assert result["success"] is True
        assert result["text_length"] == 0

    def test_mixed_ascii_cjk_uses_clipboard(self) -> None:
        """Any non-keymap char triggers clipboard for the whole string."""
        with (
            patch("subprocess.run") as mock_run,
            patch.object(
                input_mod._REMOTE_INPUT, "_ensure_session", return_value=("stream", MagicMock())
            ),
            patch.object(input_mod._REMOTE_INPUT, "_call_session"),
            patch("time.sleep"),
        ):
            paste_result = MagicMock()
            paste_result.returncode = 0
            paste_result.stdout = b""
            copy_result = MagicMock()
            copy_result.returncode = 0
            mock_run.side_effect = [paste_result, copy_result, copy_result]

            result = input_mod.type_unicode("hello世界")

        assert result["success"] is True
        assert result["method"] == "clipboard"

    def test_wl_copy_not_found_returns_error(self) -> None:
        with patch("subprocess.run", side_effect=FileNotFoundError("wl-paste not found")):
            result = input_mod.type_unicode("测试")

        assert result["success"] is False
        assert (
            "wl-paste" in result.get("error", "").lower()
            or "not found" in result.get("error", "").lower()
        )
