"""Tests for set_boundaries / clear_boundaries / check_boundary (Item 14)."""

from __future__ import annotations

from unittest.mock import patch

from gnome_ui_mcp.desktop import boundaries

_MOD = "gnome_ui_mcp.desktop.boundaries"


class TestSetBoundaries:
    def test_set_app_boundary(self) -> None:
        boundaries.clear_boundaries()
        result = boundaries.set_boundaries(app_name="firefox")
        assert result["success"] is True
        assert result["app_name"] == "firefox"

    def test_set_with_global_keys(self) -> None:
        boundaries.clear_boundaries()
        result = boundaries.set_boundaries(app_name="firefox", allow_global_keys=["Escape", "F5"])
        assert result["success"] is True
        assert "Escape" in result["allow_global_keys"]


class TestCheckBoundary:
    def test_no_boundary_passes(self) -> None:
        boundaries.clear_boundaries()
        result = boundaries.check_boundary("0/1/2")
        assert result["allowed"] is True

    def test_matching_app_passes(self) -> None:
        boundaries.clear_boundaries()
        boundaries.set_boundaries(app_name="firefox")
        with patch(
            f"{_MOD}.accessibility._application_name_for_element_id",
            return_value="firefox",
        ):
            result = boundaries.check_boundary("0/1/2")
        assert result["allowed"] is True

    def test_different_app_blocked(self) -> None:
        boundaries.clear_boundaries()
        boundaries.set_boundaries(app_name="firefox")
        with patch(
            f"{_MOD}.accessibility._application_name_for_element_id",
            return_value="gedit",
        ):
            result = boundaries.check_boundary("0/2/0")
        assert result["allowed"] is False
        assert "boundary" in result.get("error", "").lower()


class TestClearBoundaries:
    def test_clear(self) -> None:
        boundaries.set_boundaries(app_name="myapp")
        result = boundaries.clear_boundaries()
        assert result["success"] is True
        # After clearing, check_boundary should pass
        check = boundaries.check_boundary("0/0/0")
        assert check["allowed"] is True
