"""Tests for session state in McpContext."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from gnome_ui_mcp.mcp_context import McpContext


class TestBoundaries:
    def test_set_boundary_stores_app_and_keys(self) -> None:
        context = McpContext()

        context.set_boundary("firefox", allow_keys=["Escape", "F5"])

        assert context.boundary_app == "firefox"
        assert context.boundary_allow_keys == ["Escape", "F5"]

    def test_clear_boundary_resets_state(self) -> None:
        context = McpContext()
        context.set_boundary("firefox", allow_keys=["Escape"])

        context.clear_boundary()

        assert context.boundary_app is None
        assert context.boundary_allow_keys == []

    def test_check_boundary_without_boundary_passes(self) -> None:
        context = McpContext()

        context.check_boundary("0/1/2")

    def test_check_boundary_with_matching_app_passes(self) -> None:
        context = McpContext()
        context.set_boundary("firefox")

        with patch(
            "gnome_ui_mcp.adapters.accessibility._get_app_name_for_element",
            return_value="Firefox",
        ):
            context.check_boundary("0/1/2")

    def test_check_boundary_with_wrong_app_raises(self) -> None:
        context = McpContext()
        context.set_boundary("firefox")

        with patch(
            "gnome_ui_mcp.adapters.accessibility._get_app_name_for_element",
            return_value="gedit",
        ):
            with pytest.raises(ValueError, match="Boundary violation"):
                context.check_boundary("0/1/2")


class TestHistory:
    def test_record_action_and_retrieve(self) -> None:
        context = McpContext()

        context.record_action("click_element", {"element_id": "0/1/2"})

        history = context.get_history(last_n=10)
        assert len(history) == 1
        assert history[0].tool == "click_element"
        assert history[0].params["element_id"] == "0/1/2"
        assert history[0].undo_hint == "Escape"

    def test_history_returns_most_recent_first(self) -> None:
        context = McpContext()
        for index in range(5):
            context.record_action(f"tool_{index}", {"index": index})

        history = context.get_history(last_n=3)

        assert [item.tool for item in history] == ["tool_4", "tool_3", "tool_2"]
        assert context.history_count == 5

    def test_history_maxlen_is_enforced(self) -> None:
        context = McpContext()
        for index in range(150):
            context.record_action(f"tool_{index}", {"index": index})

        assert context.history_count == 100

    def test_press_key_has_no_undo_hint(self) -> None:
        context = McpContext()

        context.record_action("press_key", {"key_name": "Return"})

        history = context.get_history(last_n=1)
        assert history[0].undo_hint is None
