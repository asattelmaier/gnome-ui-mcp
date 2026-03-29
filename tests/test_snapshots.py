"""Tests for snapshot_state and compare_state (Item 13)."""

from __future__ import annotations

from unittest.mock import patch

from gnome_ui_mcp.desktop import snapshots

_MOD = "gnome_ui_mcp.desktop.snapshots"


def _patch(attr, return_value=None):
    return patch(f"{_MOD}.accessibility.{attr}", return_value=return_value)


class TestSnapshotState:
    def test_creates_snapshot(self) -> None:
        apps = {"success": True, "applications": [{"id": "0", "name": "firefox"}]}
        windows = {"success": True, "windows": [{"id": "0/0", "name": "Mozilla Firefox"}]}
        focus = {"id": "0/0/1", "name": "url bar", "role": "text"}
        popups = {"popups": [], "popup_count": 0, "signature": []}

        with (
            _patch("list_applications", return_value=apps),
            _patch("list_windows", return_value=windows),
            _patch("current_focus_metadata", return_value=focus),
            _patch("_visible_shell_popup_state", return_value=popups),
        ):
            result = snapshots.snapshot_state()

        assert result["success"] is True
        assert "snapshot_id" in result
        assert result["applications"] == apps
        assert result["windows"] == windows
        assert result["focus"] == focus

    def test_snapshot_stored_by_id(self) -> None:
        apps = {"success": True, "applications": []}
        windows = {"success": True, "windows": []}

        with (
            _patch("list_applications", return_value=apps),
            _patch("list_windows", return_value=windows),
            _patch("current_focus_metadata", return_value=None),
            _patch(
                "_visible_shell_popup_state",
                return_value={"popups": [], "popup_count": 0, "signature": []},
            ),
        ):
            result = snapshots.snapshot_state()

        snap_id = result["snapshot_id"]
        assert snap_id in snapshots._snapshots


class TestCompareState:
    def test_apps_added(self) -> None:
        snapshots._snapshots["before"] = {
            "applications": {"success": True, "applications": [{"name": "firefox"}]},
            "windows": {"success": True, "windows": []},
            "focus": None,
            "popups": {"popups": [], "popup_count": 0, "signature": []},
        }
        snapshots._snapshots["after"] = {
            "applications": {
                "success": True,
                "applications": [{"name": "firefox"}, {"name": "gedit"}],
            },
            "windows": {"success": True, "windows": []},
            "focus": None,
            "popups": {"popups": [], "popup_count": 0, "signature": []},
        }

        result = snapshots.compare_state("before", "after")
        assert result["success"] is True
        assert "gedit" in [a["name"] for a in result["apps_added"]]

    def test_apps_removed(self) -> None:
        snapshots._snapshots["before"] = {
            "applications": {
                "success": True,
                "applications": [{"name": "firefox"}, {"name": "gedit"}],
            },
            "windows": {"success": True, "windows": []},
            "focus": None,
            "popups": {"popups": [], "popup_count": 0, "signature": []},
        }
        snapshots._snapshots["after"] = {
            "applications": {"success": True, "applications": [{"name": "firefox"}]},
            "windows": {"success": True, "windows": []},
            "focus": None,
            "popups": {"popups": [], "popup_count": 0, "signature": []},
        }

        result = snapshots.compare_state("before", "after")
        assert "gedit" in [a["name"] for a in result["apps_removed"]]

    def test_focus_changed(self) -> None:
        snapshots._snapshots["before"] = {
            "applications": {"success": True, "applications": []},
            "windows": {"success": True, "windows": []},
            "focus": {"id": "0/0/1", "name": "url bar"},
            "popups": {"popups": [], "popup_count": 0, "signature": []},
        }
        snapshots._snapshots["after"] = {
            "applications": {"success": True, "applications": []},
            "windows": {"success": True, "windows": []},
            "focus": {"id": "0/0/5", "name": "search box"},
            "popups": {"popups": [], "popup_count": 0, "signature": []},
        }

        result = snapshots.compare_state("before", "after")
        assert result["focus_changed"] is True

    def test_no_changes(self) -> None:
        snap = {
            "applications": {"success": True, "applications": [{"name": "firefox"}]},
            "windows": {"success": True, "windows": [{"id": "0/0"}]},
            "focus": {"id": "0/0/1", "name": "url bar"},
            "popups": {"popups": [], "popup_count": 0, "signature": []},
        }
        snapshots._snapshots["same1"] = dict(snap)
        snapshots._snapshots["same2"] = dict(snap)

        result = snapshots.compare_state("same1", "same2")
        assert result["success"] is True
        assert result["apps_added"] == []
        assert result["apps_removed"] == []
        assert result["focus_changed"] is False

    def test_unknown_snapshot_id(self) -> None:
        result = snapshots.compare_state("nonexistent-1", "nonexistent-2")
        assert result["success"] is False

    def test_popups_changed(self) -> None:
        snapshots._snapshots["pop-before"] = {
            "applications": {"success": True, "applications": []},
            "windows": {"success": True, "windows": []},
            "focus": None,
            "popups": {"popups": [], "popup_count": 0, "signature": []},
        }
        snapshots._snapshots["pop-after"] = {
            "applications": {"success": True, "applications": []},
            "windows": {"success": True, "windows": []},
            "focus": None,
            "popups": {"popups": [{"id": "0/0"}], "popup_count": 1, "signature": ["0/0"]},
        }

        result = snapshots.compare_state("pop-before", "pop-after")
        assert result["popups_changed"] is True
