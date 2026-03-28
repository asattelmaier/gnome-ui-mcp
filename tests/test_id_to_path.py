"""Tests for _id_to_path validation (BUG-4: empty element_id)."""

from __future__ import annotations

import pytest

from gnome_ui_mcp.desktop.accessibility import _id_to_path


class TestIdToPathValidation:
    """Empty or whitespace-only element_id must raise ValueError."""

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid element_id"):
            _id_to_path("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid element_id"):
            _id_to_path("   ")

    def test_only_slashes_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid element_id"):
            _id_to_path("///")


class TestIdToPathValidInputs:
    """Valid element_id strings must continue to work."""

    def test_single_index(self) -> None:
        assert _id_to_path("0") == [0]

    def test_multi_level_path(self) -> None:
        assert _id_to_path("1/2/3") == [1, 2, 3]

    def test_leading_trailing_slashes_valid(self) -> None:
        # "0/1/" splits to ["0", "1", ""] -> filter empty -> [0, 1]
        assert _id_to_path("0/1/") == [0, 1]

    def test_non_numeric_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid element_id"):
            _id_to_path("abc")
