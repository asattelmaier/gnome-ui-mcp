"""Tests for double-click support (click_count parameter)."""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from gnome_ui_mcp.desktop import input as input_mod
from gnome_ui_mcp.desktop.input import _StageArea


def _mock_ensure_session(stage: _StageArea | None = None) -> MagicMock:
    if stage is None:
        stage = _StageArea(origin_x=0, origin_y=0, width=1920, height=1080)
    return MagicMock(return_value=("/stream/0", stage))


class TestAtspiDoubleClick:
    """AT-SPI backend uses b1d for double-click."""

    def test_single_click_uses_b1c(self) -> None:
        with patch.object(input_mod, "Atspi") as mock_atspi:
            mock_atspi.generate_mouse_event.return_value = True
            result = input_mod._perform_mouse_click_atspi(100, 200, button="left", click_count=1)

        # Second call is the click (first is "abs" move)
        click_call = mock_atspi.generate_mouse_event.call_args_list[-1]
        assert click_call == call(100, 200, "b1c")
        assert result["click_count"] == 1

    def test_double_click_uses_b1d(self) -> None:
        with patch.object(input_mod, "Atspi") as mock_atspi:
            mock_atspi.generate_mouse_event.return_value = True
            result = input_mod._perform_mouse_click_atspi(100, 200, button="left", click_count=2)

        click_call = mock_atspi.generate_mouse_event.call_args_list[-1]
        assert click_call == call(100, 200, "b1d")
        assert result["click_count"] == 2

    def test_right_double_click_uses_b3d(self) -> None:
        with patch.object(input_mod, "Atspi") as mock_atspi:
            mock_atspi.generate_mouse_event.return_value = True
            input_mod._perform_mouse_click_atspi(100, 200, button="right", click_count=2)

        click_call = mock_atspi.generate_mouse_event.call_args_list[-1]
        assert click_call == call(100, 200, "b3d")


class TestMutterDoubleClick:
    """Mutter backend sends multiple press/release cycles."""

    def test_single_click_sends_two_button_calls(self) -> None:
        remote = input_mod._REMOTE_INPUT
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_call_session") as mock_call,
        ):
            remote.click_at(100, 200, button="left", click_count=1)

        button_calls = [c for c in mock_call.call_args_list if c.args[0] == "NotifyPointerButton"]
        assert len(button_calls) == 2  # press + release

    def test_double_click_sends_four_button_calls(self) -> None:
        remote = input_mod._REMOTE_INPUT
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_call_session") as mock_call,
        ):
            result = remote.click_at(100, 200, button="left", click_count=2)

        button_calls = [c for c in mock_call.call_args_list if c.args[0] == "NotifyPointerButton"]
        assert len(button_calls) == 4  # press, release, press, release
        assert result["click_count"] == 2

    def test_triple_click_sends_six_button_calls(self) -> None:
        remote = input_mod._REMOTE_INPUT
        with (
            patch.object(remote, "_ensure_session", _mock_ensure_session()),
            patch.object(remote, "_call_session") as mock_call,
        ):
            remote.click_at(100, 200, button="left", click_count=3)

        button_calls = [c for c in mock_call.call_args_list if c.args[0] == "NotifyPointerButton"]
        assert len(button_calls) == 6


class TestClickCountValidation:
    """Invalid click_count values must raise ValueError."""

    def test_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="click_count"):
            input_mod.perform_mouse_click(100, 200, click_count=0)

    def test_four_raises(self) -> None:
        with pytest.raises(ValueError, match="click_count"):
            input_mod.perform_mouse_click(100, 200, click_count=4)

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="click_count"):
            input_mod.perform_mouse_click(100, 200, click_count=-1)


class TestClickCountPassthrough:
    """perform_mouse_click passes click_count through to backends."""

    def test_passes_to_mutter(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "click_at",
            return_value={"success": True, "click_count": 2},
        ) as mock_click:
            input_mod.perform_mouse_click(100, 200, click_count=2)

        mock_click.assert_called_once_with(100, 200, button="left", click_count=2)

    def test_passes_to_atspi_fallback(self) -> None:
        with (
            patch.object(input_mod._REMOTE_INPUT, "click_at", side_effect=RuntimeError("fail")),
            patch.object(input_mod, "_perform_mouse_click_atspi") as mock_atspi,
        ):
            mock_atspi.return_value = {"success": True, "click_count": 2}
            input_mod.perform_mouse_click(100, 200, click_count=2)

        mock_atspi.assert_called_once_with(100, 200, button="left", click_count=2)
