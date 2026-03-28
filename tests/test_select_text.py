"""Tests for select_element_text tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import accessibility


def _make_accessible_with_text(
    text: str,
    *,
    has_text_iface: bool = True,
    selectable: bool = True,
) -> MagicMock:
    mock = MagicMock()
    if has_text_iface:
        text_iface = MagicMock()
        text_iface.get_character_count.return_value = len(text)
        text_iface.get_text.return_value = text
        text_iface.get_n_selections.return_value = 0
        text_iface.add_selection.return_value = True
        sel_range = MagicMock()
        sel_range.start_offset = 0
        sel_range.end_offset = len(text)
        text_iface.get_selection.return_value = sel_range
        mock.get_text_iface.return_value = text_iface
    else:
        mock.get_text_iface.return_value = None

    # State set with selectable-text
    state_set = MagicMock()
    states_list = []
    if selectable:
        selectable_state = MagicMock()
        selectable_state.value_nick = "selectable-text"
        states_list.append(selectable_state)
    state_set.get_states.return_value = states_list
    mock.get_state_set.return_value = state_set
    return mock


def _mock_resolve(accessible: MagicMock) -> MagicMock:
    return patch.object(accessibility, "_resolve_element", return_value=accessible)


class TestSelectTextHappyPath:
    def test_select_range(self) -> None:
        acc = _make_accessible_with_text("hello world")
        with _mock_resolve(acc):
            result = accessibility.select_element_text("0/1", start_offset=0, end_offset=5)

        assert result["success"] is True
        assert result["selection_start"] == 0
        assert result["selection_end"] == 5

    def test_select_all_omit_offsets(self) -> None:
        acc = _make_accessible_with_text("hello world")
        with _mock_resolve(acc):
            accessibility.select_element_text("0/1")

        text_iface = acc.get_text_iface()
        # select-all should use char_count - 1 to avoid gnome-shell bug
        call_args = text_iface.add_selection.call_args
        assert call_args[0][1] == 10  # len("hello world") - 1 = 10

    def test_returns_selected_text(self) -> None:
        acc = _make_accessible_with_text("hello world")
        with _mock_resolve(acc):
            result = accessibility.select_element_text("0/1", start_offset=0, end_offset=5)

        assert "selected_text" in result


class TestSelectTextErrors:
    def test_no_text_interface(self) -> None:
        acc = _make_accessible_with_text("", has_text_iface=False)
        with _mock_resolve(acc):
            result = accessibility.select_element_text("0/1")

        assert result["success"] is False
        assert "Text interface" in result["error"]

    def test_not_selectable(self) -> None:
        acc = _make_accessible_with_text("hello", selectable=False)
        with _mock_resolve(acc):
            result = accessibility.select_element_text("0/1")

        assert result["success"] is False
        assert "selectable" in result["error"].lower()

    def test_empty_text(self) -> None:
        acc = _make_accessible_with_text("")
        with _mock_resolve(acc):
            result = accessibility.select_element_text("0/1")

        assert result["success"] is False
        assert "no text" in result["error"].lower()

    def test_only_start_offset_errors(self) -> None:
        acc = _make_accessible_with_text("hello")
        with _mock_resolve(acc):
            result = accessibility.select_element_text("0/1", start_offset=2)

        assert result["success"] is False

    def test_only_end_offset_errors(self) -> None:
        acc = _make_accessible_with_text("hello")
        with _mock_resolve(acc):
            result = accessibility.select_element_text("0/1", end_offset=3)

        assert result["success"] is False


class TestSelectTextEdgeCases:
    def test_clamps_negative_start(self) -> None:
        acc = _make_accessible_with_text("hello")
        with _mock_resolve(acc):
            accessibility.select_element_text("0/1", start_offset=-5, end_offset=3)

        text_iface = acc.get_text_iface()
        call_args = text_iface.add_selection.call_args
        assert call_args[0][0] == 0  # clamped to 0

    def test_clamps_end_past_length(self) -> None:
        acc = _make_accessible_with_text("hello")
        with _mock_resolve(acc):
            accessibility.select_element_text("0/1", start_offset=0, end_offset=999)

        text_iface = acc.get_text_iface()
        call_args = text_iface.add_selection.call_args
        assert call_args[0][1] == 4  # len("hello") - 1 = 4

    def test_swaps_start_greater_than_end(self) -> None:
        acc = _make_accessible_with_text("hello world")
        with _mock_resolve(acc):
            accessibility.select_element_text("0/1", start_offset=8, end_offset=2)

        text_iface = acc.get_text_iface()
        call_args = text_iface.add_selection.call_args
        assert call_args[0][0] == 2
        assert call_args[0][1] == 8

    def test_clears_existing_selections(self) -> None:
        acc = _make_accessible_with_text("hello")
        text_iface = acc.get_text_iface()
        text_iface.get_n_selections.return_value = 2

        with _mock_resolve(acc):
            accessibility.select_element_text("0/1", start_offset=0, end_offset=3)

        assert text_iface.remove_selection.call_count == 2

    def test_add_selection_fails(self) -> None:
        acc = _make_accessible_with_text("hello")
        text_iface = acc.get_text_iface()
        text_iface.add_selection.return_value = False

        with _mock_resolve(acc):
            result = accessibility.select_element_text("0/1", start_offset=0, end_offset=3)

        assert result["success"] is False
        assert "failed" in result["error"].lower()
