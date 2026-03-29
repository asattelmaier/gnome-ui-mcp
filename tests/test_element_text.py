"""Tests for get_element_text (Item 3).

Verifies caret offset, selections, and text attributes are extracted
from the AT-SPI Text interface.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import accessibility


def _mock_resolve(accessible: MagicMock) -> Any:
    return patch.object(accessibility, "_resolve_element", return_value=accessible)


def _make_text_accessible(
    text: str,
    *,
    has_text: bool = True,
    caret_offset: int = 0,
    n_selections: int = 0,
    selections: list[tuple[int, int]] | None = None,
    attributes: dict[str, str] | None = None,
    attr_start: int = 0,
    attr_end: int = 0,
) -> MagicMock:
    acc = MagicMock()
    if not has_text:
        acc.get_text_iface.return_value = None
        return acc

    text_iface = MagicMock()
    text_iface.get_character_count.return_value = len(text)
    text_iface.get_text.return_value = text
    text_iface.get_caret_offset.return_value = caret_offset
    text_iface.get_n_selections.return_value = n_selections

    sels = selections or []

    def get_selection(i: int) -> MagicMock:
        if i < len(sels):
            r = MagicMock()
            r.start_offset = sels[i][0]
            r.end_offset = sels[i][1]
            return r
        return MagicMock(start_offset=0, end_offset=0)

    text_iface.get_selection.side_effect = get_selection

    attrs = attributes or {}

    def get_text_attributes(offset: int) -> tuple[dict[str, str], int, int]:
        return (attrs, attr_start, attr_end)

    text_iface.get_text_attributes.side_effect = get_text_attributes

    acc.get_text_iface.return_value = text_iface
    return acc


class TestGetElementTextHappyPath:
    """Basic extraction of text content, caret, selections, attributes."""

    def test_returns_full_text(self) -> None:
        acc = _make_text_accessible("Hello World")
        with _mock_resolve(acc):
            result = accessibility.get_element_text("0/1")

        assert result["success"] is True
        assert result["text"] == "Hello World"
        assert result["character_count"] == 11

    def test_returns_caret_offset(self) -> None:
        acc = _make_text_accessible("Hello", caret_offset=3)
        with _mock_resolve(acc):
            result = accessibility.get_element_text("0/1")

        assert result["caret_offset"] == 3

    def test_returns_selections(self) -> None:
        acc = _make_text_accessible(
            "Hello World",
            n_selections=1,
            selections=[(2, 7)],
        )
        with _mock_resolve(acc):
            result = accessibility.get_element_text("0/1")

        assert result["n_selections"] == 1
        assert len(result["selections"]) == 1
        assert result["selections"][0]["start"] == 2
        assert result["selections"][0]["end"] == 7


class TestGetElementTextAttributes:
    """Text attributes at a given offset."""

    def test_returns_attributes_at_caret(self) -> None:
        acc = _make_text_accessible(
            "Bold text",
            caret_offset=0,
            attributes={"font-weight": "bold", "font-size": "12"},
            attr_start=0,
            attr_end=4,
        )
        with _mock_resolve(acc):
            result = accessibility.get_element_text("0/1")

        assert "attributes_at_caret" in result
        assert result["attributes_at_caret"]["attributes"]["font-weight"] == "bold"
        assert result["attributes_at_caret"]["start"] == 0
        assert result["attributes_at_caret"]["end"] == 4

    def test_empty_attributes(self) -> None:
        acc = _make_text_accessible("Plain text", attributes={}, attr_start=0, attr_end=10)
        with _mock_resolve(acc):
            result = accessibility.get_element_text("0/1")

        assert result["attributes_at_caret"]["attributes"] == {}


class TestGetElementTextNoInterface:
    """Element without text interface should return an error."""

    def test_no_text_interface(self) -> None:
        acc = _make_text_accessible("", has_text=False)
        with _mock_resolve(acc):
            result = accessibility.get_element_text("0/1")

        assert result["success"] is False
        assert "text" in result["error"].lower()

    def test_empty_text(self) -> None:
        acc = _make_text_accessible("")
        with _mock_resolve(acc):
            result = accessibility.get_element_text("0/1")

        assert result["success"] is True
        assert result["text"] == ""
        assert result["character_count"] == 0
