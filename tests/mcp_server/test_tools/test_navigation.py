"""Tests for the blessed navigation tools (snapshot-driven, uid-addressed)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.adapters.elements import ClickResult, FillResult
from gnome_ui_mcp.desktop.snapshot import Snapshot, SnapshotNode
from gnome_ui_mcp.mcp_context import McpContext
from gnome_ui_mcp.mcp_response import McpResponse
from gnome_ui_mcp.tools import navigation
from gnome_ui_mcp.tools.tool_definition import ToolRequest


@pytest.fixture()
def ctx() -> McpContext:
    return MagicMock(spec=McpContext)


class TestTakeSnapshot:
    def test_renders_snapshot(self, ctx) -> None:
        node = SnapshotNode(uid="2_0", path_id="3", role="frame", name="Files", depth=0)
        ctx.take_snapshot.return_value = Snapshot(
            id=2, scope="window 3", nodes=[node], id_to_node={"2_0": node}
        )
        response = McpResponse()
        navigation._take_snapshot(
            ToolRequest({"window": None, "app_name": None, "max_depth": None}), response, ctx
        )

        ctx.take_snapshot.assert_called_once_with(window_id=None, app_name=None, max_depth=None)
        structured = response.to_tool_result().structuredContent
        assert structured["snapshot_id"] == 2
        assert any("uid=2_0" in line for line in response.text_lines)

    def test_explicit_window_becomes_selected(self, ctx) -> None:
        ctx.take_snapshot.return_value = Snapshot(id=3, scope="window 3/0", nodes=[], id_to_node={})
        response = McpResponse()
        navigation._take_snapshot(
            ToolRequest({"window": "3/0", "app_name": None, "max_depth": None}), response, ctx
        )
        ctx.select_window.assert_called_once_with("3/0")


class TestClick:
    @patch("gnome_ui_mcp.adapters.elements.click_element")
    def test_resolves_uid_and_clicks_with_autowait(self, mock_click, ctx) -> None:
        ctx.resolve_uid.return_value = "3/0/2"
        mock_click.return_value = ClickResult(
            element_id="3/0/2", method="action", input_injected=True, effect_verified=True
        )
        response = McpResponse()
        navigation._click(
            ToolRequest({"uid": "2_0", "dbl_click": False, "include_snapshot": False}),
            response,
            ctx,
        )

        ctx.resolve_uid.assert_called_once_with("2_0")
        ctx.check_boundary.assert_called_once_with("3/0/2")
        mock_click.assert_called_once_with(element_id="3/0/2", click_count=1, settle=True)
        structured = response.to_tool_result().structuredContent
        assert structured["uid"] == "2_0"
        assert structured["effect_verified"] is True

    def test_stale_uid_is_rejected(self, ctx) -> None:
        ctx.resolve_uid.side_effect = ValueError("not in the current snapshot")
        response = McpResponse()
        with pytest.raises(ValueError, match="not in the current snapshot"):
            navigation._click(
                ToolRequest({"uid": "1_0", "dbl_click": False, "include_snapshot": False}),
                response,
                ctx,
            )


class TestFill:
    @patch("gnome_ui_mcp.adapters.elements.fill_element")
    def test_fill_dispatches_through_adapter(self, mock_fill, ctx) -> None:
        ctx.resolve_uid.return_value = "3/1"
        mock_fill.return_value = FillResult(
            element_id="3/1", method="text", value="hi", input_injected=True, effect_verified=True
        )
        response = McpResponse()
        navigation._fill(
            ToolRequest({"uid": "2_1", "value": "hi", "include_snapshot": False}), response, ctx
        )

        ctx.resolve_uid.assert_called_once_with("2_1")
        mock_fill.assert_called_once_with(element_id="3/1", value="hi")
        structured = response.to_tool_result().structuredContent
        assert structured["method"] == "text"


class TestFillForm:
    @patch("gnome_ui_mcp.adapters.elements.fill_element")
    def test_fills_each_field_in_order(self, mock_fill, ctx) -> None:
        ctx.resolve_uid.side_effect = ["3/1", "3/2"]
        mock_fill.return_value = FillResult(
            element_id="x", method="text", value="v", input_injected=True, effect_verified=True
        )
        response = McpResponse()
        navigation._fill_form(
            ToolRequest(
                {
                    "fields": [
                        {"uid": "2_1", "value": "alice"},
                        {"uid": "2_2", "value": "secret"},
                    ],
                    "include_snapshot": False,
                }
            ),
            response,
            ctx,
        )

        assert mock_fill.call_count == 2
        structured = response.to_tool_result().structuredContent
        assert len(structured["results"]) == 2

    def test_rejects_malformed_field(self, ctx) -> None:
        response = McpResponse()
        with pytest.raises(ValueError, match="uid' and 'value'"):
            navigation._fill_form(
                ToolRequest({"fields": [{"uid": "2_1"}], "include_snapshot": False}),
                response,
                ctx,
            )

    def test_rejects_empty_fields(self, ctx) -> None:
        response = McpResponse()
        with pytest.raises(ValueError, match="non-empty"):
            navigation._fill_form(
                ToolRequest({"fields": [], "include_snapshot": False}), response, ctx
            )


class TestSelectWindow:
    @patch("gnome_ui_mcp.adapters.elements.focus_element")
    def test_sets_scope_and_focuses(self, mock_focus, ctx) -> None:
        response = McpResponse()
        navigation._select_window(ToolRequest({"window": "3/0"}), response, ctx)

        ctx.select_window.assert_called_once_with("3/0")
        structured = response.to_tool_result().structuredContent
        assert structured["selected_window"] == "3/0"
        assert structured["focused"] is True

    @patch("gnome_ui_mcp.adapters.elements.focus_element")
    def test_focus_failure_is_best_effort(self, mock_focus, ctx) -> None:
        mock_focus.side_effect = ValueError("cannot focus frame")
        response = McpResponse()
        navigation._select_window(ToolRequest({"window": "3/0"}), response, ctx)

        ctx.select_window.assert_called_once_with("3/0")
        structured = response.to_tool_result().structuredContent
        assert structured["focused"] is False
        assert "cannot focus frame" in structured["focus_error"]
