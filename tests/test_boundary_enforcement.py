"""Tests that boundary checks are actually enforced on element operations."""

from __future__ import annotations

from unittest.mock import patch

from gnome_ui_mcp import backend
from gnome_ui_mcp.desktop import boundaries


class TestBoundaryEnforcement:
    def setup_method(self) -> None:
        boundaries.clear_boundaries()

    def teardown_method(self) -> None:
        boundaries.clear_boundaries()

    def test_no_boundary_allows_all(self) -> None:
        with patch.object(
            backend.interaction,
            "click_element",
            return_value={"success": True},
        ):
            result = backend.click_element("0/5/1/2")
        assert result["success"] is True

    def test_boundary_blocks_wrong_app(self) -> None:
        boundaries.set_boundaries(app_name="Firefox")
        with patch.object(
            backend.accessibility,
            "_application_name_for_element_id",
            return_value="Nautilus",
        ):
            result = backend.click_element("0/3/1/2")
        assert result["success"] is False
        assert "Boundary violation" in result["error"]

    def test_boundary_allows_correct_app(self) -> None:
        boundaries.set_boundaries(app_name="Firefox")
        with (
            patch.object(
                backend.accessibility,
                "_application_name_for_element_id",
                return_value="Firefox",
            ),
            patch.object(
                backend.interaction,
                "click_element",
                return_value={"success": True},
            ),
        ):
            result = backend.click_element("0/5/1/2")
        assert result["success"] is True

    def test_boundary_enforced_on_focus(self) -> None:
        boundaries.set_boundaries(app_name="Firefox")
        with patch.object(
            backend.accessibility,
            "_application_name_for_element_id",
            return_value="Nautilus",
        ):
            result = backend.focus_element("0/3/1/2")
        assert result["success"] is False

    def test_boundary_enforced_on_set_text(self) -> None:
        boundaries.set_boundaries(app_name="Firefox")
        with patch.object(
            backend.accessibility,
            "_application_name_for_element_id",
            return_value="gedit",
        ):
            result = backend.set_element_text("0/2/1", "hello")
        assert result["success"] is False

    def test_boundary_enforced_on_set_value(self) -> None:
        boundaries.set_boundaries(app_name="Firefox")
        with patch.object(
            backend.accessibility,
            "_application_name_for_element_id",
            return_value="Settings",
        ):
            result = backend.set_element_value("0/4/1", 50.0)
        assert result["success"] is False
