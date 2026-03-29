"""Tests for wait_and_act (Item 9)."""

from __future__ import annotations

from unittest.mock import patch

from gnome_ui_mcp.desktop import wait_act

_MOD = "gnome_ui_mcp.desktop.wait_act"


def _patch(attr: str, return_value=None, side_effect=None):
    target = f"{_MOD}.accessibility.{attr}"
    kwargs = {}
    if side_effect is not None:
        kwargs["side_effect"] = side_effect
    else:
        kwargs["return_value"] = return_value
    return patch(target, **kwargs)


def _patch_interaction(attr: str, return_value=None, side_effect=None):
    target = f"{_MOD}.interaction.{attr}"
    kwargs = {}
    if side_effect is not None:
        kwargs["side_effect"] = side_effect
    else:
        kwargs["return_value"] = return_value
    return patch(target, **kwargs)


class TestWaitAndActActivate:
    def test_immediate_find_activate(self) -> None:
        found = {
            "success": True,
            "matches": [{"id": "0/1/2", "name": "OK", "role": "push button"}],
        }
        act_result = {"success": True, "element_id": "0/1/2"}
        with (
            _patch("find_elements", return_value=found),
            _patch_interaction("activate_element", return_value=act_result),
        ):
            result = wait_act.wait_and_act(
                "OK", then_action="activate", timeout_ms=200, poll_interval_ms=50
            )

        assert result["success"] is True
        assert result["wait_match"]["id"] == "0/1/2"

    def test_timeout(self) -> None:
        empty = {"success": True, "matches": []}
        with _patch("find_elements", return_value=empty):
            result = wait_act.wait_and_act("nonexistent", timeout_ms=100, poll_interval_ms=50)

        assert result["success"] is False
        assert "timeout" in result.get("error", "").lower()


class TestWaitAndActClick:
    def test_click_action(self) -> None:
        found = {
            "success": True,
            "matches": [{"id": "0/1/3", "name": "Btn", "role": "push button"}],
        }
        click_result = {"success": True, "element_id": "0/1/3"}
        with (
            _patch("find_elements", return_value=found),
            _patch_interaction("click_element", return_value=click_result),
        ):
            result = wait_act.wait_and_act(
                "Btn", then_action="click", timeout_ms=200, poll_interval_ms=50
            )

        assert result["success"] is True


class TestWaitAndActFocus:
    def test_focus_action(self) -> None:
        found = {
            "success": True,
            "matches": [{"id": "0/2/0", "name": "Input", "role": "text"}],
        }
        focus_result = {"success": True, "element_id": "0/2/0"}
        with (
            _patch("find_elements", return_value=found),
            _patch("focus_element", return_value=focus_result),
        ):
            result = wait_act.wait_and_act(
                "Input", then_action="focus", timeout_ms=200, poll_interval_ms=50
            )

        assert result["success"] is True


class TestWaitAndActSetText:
    def test_set_text_action(self) -> None:
        found = {
            "success": True,
            "matches": [{"id": "0/2/1", "name": "Field", "role": "text"}],
        }
        text_result = {"success": True, "element_id": "0/2/1", "text_length": 5}
        with (
            _patch("find_elements", return_value=found),
            _patch("set_element_text", return_value=text_result),
        ):
            result = wait_act.wait_and_act(
                "Field",
                then_action="set_text",
                then_text="hello",
                timeout_ms=200,
                poll_interval_ms=50,
            )

        assert result["success"] is True


class TestWaitAndActThenQuery:
    def test_then_query_finds_sibling(self) -> None:
        """When then_query is provided, use it to find the action target."""
        wait_matches = {
            "success": True,
            "matches": [{"id": "0/1/0", "name": "Label", "role": "label"}],
        }
        then_matches = {
            "success": True,
            "matches": [{"id": "0/1/1", "name": "Submit", "role": "push button"}],
        }

        call_count = {"n": 0}

        def find_side_effect(**kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return wait_matches
            return then_matches

        act_result = {"success": True, "element_id": "0/1/1"}
        with (
            _patch("find_elements", side_effect=find_side_effect),
            _patch_interaction("activate_element", return_value=act_result),
        ):
            result = wait_act.wait_and_act(
                "Label",
                then_query="Submit",
                then_action="activate",
                timeout_ms=200,
                poll_interval_ms=50,
            )

        assert result["success"] is True


class TestWaitAndActDelayed:
    def test_delayed_find(self) -> None:
        call_count = {"n": 0}

        def find_side_effect(**kwargs):
            call_count["n"] += 1
            if call_count["n"] >= 3:
                return {
                    "success": True,
                    "matches": [{"id": "0/0/5", "name": "Late", "role": "push button"}],
                }
            return {"success": True, "matches": []}

        act_result = {"success": True, "element_id": "0/0/5"}
        with (
            _patch("find_elements", side_effect=find_side_effect),
            _patch_interaction("activate_element", return_value=act_result),
        ):
            result = wait_act.wait_and_act(
                "Late", then_action="activate", timeout_ms=5000, poll_interval_ms=50
            )

        assert result["success"] is True
        assert result["waited_ms"] > 0
