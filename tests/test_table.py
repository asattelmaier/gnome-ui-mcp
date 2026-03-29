"""Tests for get_table_info and get_table_cell (Item 4).

Verifies that AT-SPI Table interface is queried for row/column counts,
headers, caption, and individual cell access.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import accessibility


def _mock_resolve(accessible: MagicMock) -> Any:
    return patch.object(accessibility, "_resolve_element", return_value=accessible)


def _make_table_accessible(
    n_rows: int = 3,
    n_cols: int = 4,
    *,
    has_table: bool = True,
    caption_name: str | None = "My Table",
    headers: list[str] | None = None,
) -> MagicMock:
    acc = MagicMock()
    if not has_table:
        acc.get_table_iface.return_value = None
        return acc

    table_iface = MagicMock()
    table_iface.get_n_rows.return_value = n_rows
    table_iface.get_n_columns.return_value = n_cols

    if caption_name is not None:
        caption = MagicMock()
        caption.get_name.return_value = caption_name
        table_iface.get_caption.return_value = caption
    else:
        table_iface.get_caption.return_value = None

    col_headers = headers or [f"Col{i}" for i in range(n_cols)]

    def get_column_header(col: int) -> MagicMock | None:
        if col < len(col_headers):
            h = MagicMock()
            h.get_name.return_value = col_headers[col]
            return h
        return None

    table_iface.get_column_header.side_effect = get_column_header

    def get_accessible_at(row: int, col: int) -> MagicMock:
        cell = MagicMock()
        cell.get_name.return_value = f"R{row}C{col}"
        cell.get_role_name.return_value = "table cell"
        return cell

    table_iface.get_accessible_at.side_effect = get_accessible_at

    acc.get_table_iface.return_value = table_iface
    return acc


class TestGetTableInfo:
    """get_table_info should return row/col counts, headers, and caption."""

    def test_returns_table_dimensions(self) -> None:
        acc = _make_table_accessible(n_rows=5, n_cols=3)
        with _mock_resolve(acc):
            result = accessibility.get_table_info("0/1")

        assert result["success"] is True
        assert result["n_rows"] == 5
        assert result["n_columns"] == 3

    def test_returns_column_headers(self) -> None:
        acc = _make_table_accessible(n_cols=3, headers=["Name", "Age", "City"])
        with _mock_resolve(acc):
            result = accessibility.get_table_info("0/1")

        assert result["headers"] == ["Name", "Age", "City"]

    def test_returns_caption(self) -> None:
        acc = _make_table_accessible(caption_name="Employee List")
        with _mock_resolve(acc):
            result = accessibility.get_table_info("0/1")

        assert result["caption"] == "Employee List"

    def test_no_table_interface(self) -> None:
        acc = _make_table_accessible(has_table=False)
        with _mock_resolve(acc):
            result = accessibility.get_table_info("0/1")

        assert result["success"] is False
        assert "table" in result["error"].lower()


class TestGetTableCell:
    """get_table_cell should return cell info at row, col."""

    def test_returns_cell_info(self) -> None:
        acc = _make_table_accessible(n_rows=3, n_cols=4)
        with _mock_resolve(acc):
            result = accessibility.get_table_cell("0/1", row=1, col=2)

        assert result["success"] is True
        assert result["cell"]["name"] == "R1C2"
        assert result["cell"]["role"] == "table cell"

    def test_out_of_bounds(self) -> None:
        acc = _make_table_accessible(n_rows=3, n_cols=4)
        with _mock_resolve(acc):
            result = accessibility.get_table_cell("0/1", row=10, col=0)

        assert result["success"] is False
        assert "out of range" in result["error"].lower() or "bounds" in result["error"].lower()
