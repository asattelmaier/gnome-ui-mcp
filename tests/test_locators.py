"""Tests for locator building and caching."""

from __future__ import annotations

from gnome_ui_mcp.desktop.locators import (
    build_locator,
    locator_for_element_id,
    remember_locator,
)
from gnome_ui_mcp.desktop.types import Locator


class TestBuildLocator:
    """build_locator must construct a Locator from element metadata."""

    def test_uses_name_as_query(self) -> None:
        loc = build_locator(
            name="Save",
            description="",
            role_name="push button",
            app_label="gedit",
        )
        assert loc.query == "Save"
        assert loc.role == "push button"
        assert loc.app_name == "gedit"

    def test_falls_back_to_description(self) -> None:
        loc = build_locator(
            name="",
            description="Save document",
            role_name="button",
            app_label="app",
        )
        assert loc.query == "Save document"

    def test_omits_empty_fields(self) -> None:
        loc = build_locator(
            name="",
            description="",
            role_name="",
            app_label="",
        )
        assert loc.query is None
        assert loc.role is None
        assert loc.app_name is None

    def test_whitespace_only_treated_as_empty(self) -> None:
        loc = build_locator(
            name="   ",
            description="  ",
            role_name="  ",
            app_label="  ",
        )
        assert loc.query is None

    def test_within_element_id_included(self) -> None:
        loc = build_locator(
            name="OK",
            description="",
            role_name="button",
            app_label="app",
            within_element_id="0/1/2",
        )
        assert loc.within_element_id == "0/1/2"

    def test_within_popup_included_when_true(self) -> None:
        loc = build_locator(
            name="Cut",
            description="",
            role_name="menu item",
            app_label="app",
            within_popup=True,
        )
        assert loc.within_popup is True

    def test_within_popup_omitted_when_false(self) -> None:
        loc = build_locator(
            name="Cut",
            description="",
            role_name="menu item",
            app_label="app",
            within_popup=False,
        )
        assert loc.within_popup is False


class TestLocatorCache:
    """remember_locator / locator_for_element_id must store and retrieve."""

    def test_remember_and_retrieve(self) -> None:
        locator = Locator(query="Open", role="button")
        remember_locator("0/1", locator)
        assert locator_for_element_id("0/1") == locator

    def test_missing_returns_none(self) -> None:
        assert locator_for_element_id("99/99/99") is None

    def test_returns_same_instance(self) -> None:
        locator = Locator(query="Open", role="button")
        remember_locator("0/2", locator)
        retrieved = locator_for_element_id("0/2")
        assert retrieved is locator

    def test_empty_locator_not_stored(self) -> None:
        remember_locator("0/3", Locator())
        assert locator_for_element_id("0/3") is None

    def test_cache_bounded_after_many_inserts(self) -> None:
        """RECENT_LOCATORS must not grow without limit."""
        from gnome_ui_mcp.desktop import locators as loc_mod

        loc_mod.RECENT_LOCATORS.clear()
        for i in range(6000):
            remember_locator(f"elem/{i}", Locator(query=f"q{i}", role="button"))
        assert len(loc_mod.RECENT_LOCATORS) <= 5000
