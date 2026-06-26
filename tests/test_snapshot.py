"""Tests for the snapshot layer: uid minting, scoping, and stale rejection."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.desktop import snapshot as snap
from gnome_ui_mcp.desktop.snapshot import Snapshot, SnapshotNode
from gnome_ui_mcp.formatters.snapshot_formatter import SnapshotFormatter
from gnome_ui_mcp.mcp_context import McpContext


def _tree(node_id, role, name, children=None, states=None):
    return {
        "id": node_id,
        "role": role,
        "name": name,
        "states": states or [],
        "bounds": None,
        "actions": [],
        "children": children or [],
    }


class TestCapture:
    @patch("gnome_ui_mcp.desktop.snapshot.accessibility")
    def test_mints_snapshot_scoped_uids_in_dfs_order(self, mock_acc) -> None:
        mock_acc._select_applications.return_value = [(MagicMock(), (3,))]
        mock_acc._serialize_tree.return_value = _tree(
            "3",
            "frame",
            "Files",
            [_tree("3/0", "push button", "Back"), _tree("3/1", "entry", "Search")],
        )

        snapshot = snap.capture(app_name="Files")

        uids = [n.uid for n in snapshot.nodes]
        assert len(uids) == 3
        prefix = uids[0].rsplit("_", 1)[0]
        # uid = "{snapshot_id}_{index}", same snapshot prefix, DFS index 0,1,2
        assert uids == [f"{prefix}_0", f"{prefix}_1", f"{prefix}_2"]
        assert snapshot.id_to_node[uids[0]].path_id == "3"
        assert snapshot.id_to_node[uids[0]].role == "frame"
        assert snapshot.id_to_node[uids[1]].path_id == "3/0"
        assert snapshot.scope == "application 'Files'"

    @patch("gnome_ui_mcp.desktop.snapshot.accessibility")
    def test_each_capture_gets_a_fresh_snapshot_id(self, mock_acc) -> None:
        mock_acc._select_applications.return_value = [(MagicMock(), (3,))]
        mock_acc._serialize_tree.return_value = _tree("3", "frame", "Files")

        first = snap.capture(app_name="Files")
        second = snap.capture(app_name="Files")

        assert second.id > first.id
        # uids from different snapshots never collide
        assert set(first.id_to_node).isdisjoint(second.id_to_node)


class TestValidateLive:
    @patch("gnome_ui_mcp.desktop.snapshot.accessibility")
    def test_returns_path_when_element_matches(self, mock_acc) -> None:
        node = SnapshotNode(uid="1_0", path_id="3/0", role="push button", name="Back", depth=0)
        mock_acc._resolve_element.return_value = MagicMock()
        mock_acc._safe_call.side_effect = ["push button", "Back"]

        assert snap.validate_live(node) == "3/0"

    @patch("gnome_ui_mcp.desktop.snapshot.accessibility")
    def test_rejects_when_element_gone(self, mock_acc) -> None:
        node = SnapshotNode(uid="1_0", path_id="3/0", role="push button", name="Back", depth=0)
        mock_acc._resolve_element.side_effect = ValueError("Element not found")

        with pytest.raises(ValueError, match="no longer exists"):
            snap.validate_live(node)

    @patch("gnome_ui_mcp.desktop.snapshot.accessibility")
    def test_rejects_when_element_drifted(self, mock_acc) -> None:
        node = SnapshotNode(uid="1_0", path_id="3/0", role="push button", name="Back", depth=0)
        mock_acc._resolve_element.return_value = MagicMock()
        # path now points at a different element (role/name mismatch)
        mock_acc._safe_call.side_effect = ["entry", "Search"]

        with pytest.raises(ValueError, match="has changed"):
            snap.validate_live(node)


class TestContextResolveUid:
    def test_no_snapshot_taken(self) -> None:
        ctx = McpContext()
        with pytest.raises(ValueError, match="No snapshot available"):
            ctx.resolve_uid("1_0")

    @patch("gnome_ui_mcp.desktop.snapshot.capture")
    def test_unknown_uid_is_rejected_as_stale(self, mock_capture) -> None:
        ctx = McpContext()
        mock_capture.return_value = Snapshot(id=1, scope="window 3", nodes=[], id_to_node={})
        ctx.take_snapshot(app_name="X")

        with pytest.raises(ValueError, match="not in the current snapshot"):
            ctx.resolve_uid("1_99")

    @patch("gnome_ui_mcp.desktop.snapshot.validate_live")
    @patch("gnome_ui_mcp.desktop.snapshot.capture")
    def test_valid_uid_resolves_to_path(self, mock_capture, mock_validate) -> None:
        ctx = McpContext()
        node = SnapshotNode(uid="1_0", path_id="3/0", role="push button", name="Back", depth=0)
        mock_capture.return_value = Snapshot(
            id=1, scope="window 3", nodes=[node], id_to_node={"1_0": node}
        )
        mock_validate.return_value = "3/0"
        ctx.take_snapshot(app_name="X")

        assert ctx.resolve_uid("1_0") == "3/0"

    @patch("gnome_ui_mcp.desktop.snapshot.capture")
    def test_new_snapshot_invalidates_old_uids(self, mock_capture) -> None:
        ctx = McpContext()
        old = SnapshotNode(uid="1_0", path_id="3/0", role="push button", name="Back", depth=0)
        mock_capture.return_value = Snapshot(
            id=1, scope="window 3", nodes=[old], id_to_node={"1_0": old}
        )
        ctx.take_snapshot(app_name="X")

        # second snapshot has different uids; the old uid must now be rejected
        mock_capture.return_value = Snapshot(id=2, scope="window 3", nodes=[], id_to_node={})
        ctx.take_snapshot(app_name="X")

        with pytest.raises(ValueError, match="not in the current snapshot"):
            ctx.resolve_uid("1_0")


class TestSnapshotFormatter:
    def test_renders_uids_with_indent_and_flags(self) -> None:
        n0 = SnapshotNode(uid="1_0", path_id="3", role="frame", name="Files", depth=0)
        n1 = SnapshotNode(
            uid="1_1",
            path_id="3/0",
            role="push button",
            name="Back",
            depth=1,
            states=["disabled"],
        )
        snapshot = Snapshot(id=1, scope="window 3", nodes=[n0, n1], id_to_node={})

        text = SnapshotFormatter(snapshot).to_string()
        assert 'uid=1_0 frame "Files"' in text
        assert '  uid=1_1 push button "Back" [disabled]' in text

        payload = SnapshotFormatter(snapshot).to_json()
        assert payload[1]["uid"] == "1_1"
        assert payload[1]["states"] == ["disabled"]

    def test_empty_scope_message(self) -> None:
        snapshot = Snapshot(id=5, scope="window 3", nodes=[], id_to_node={})
        text = SnapshotFormatter(snapshot).to_string()
        assert "No elements found" in text
