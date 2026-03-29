"""Tests for assert_element and assert_text (Item 11)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import assertions

_MOD = "gnome_ui_mcp.desktop.assertions"


def _patch(attr, return_value=None, side_effect=None):
    target = f"{_MOD}.accessibility.{attr}"
    kw = {}
    if side_effect is not None:
        kw["side_effect"] = side_effect
    else:
        kw["return_value"] = return_value
    return patch(target, **kw)


class TestAssertElement:
    def test_passes_when_found(self) -> None:
        found = {
            "success": True,
            "matches": [
                {
                    "id": "0/1",
                    "name": "OK",
                    "role": "push button",
                    "states": ["enabled", "focusable", "showing", "visible"],
                }
            ],
        }
        with _patch("find_elements", return_value=found):
            result = assertions.assert_element("OK")

        assert result["passed"] is True
        assert result["element"] is not None

    def test_fails_when_not_found(self) -> None:
        with _patch("find_elements", return_value={"success": True, "matches": []}):
            result = assertions.assert_element("missing", timeout_ms=100, poll_interval_ms=50)

        assert result["passed"] is False

    def test_expected_states_pass(self) -> None:
        found = {
            "success": True,
            "matches": [
                {
                    "id": "0/1",
                    "name": "Toggle",
                    "role": "toggle button",
                    "states": ["checked", "enabled", "showing"],
                }
            ],
        }
        with _patch("find_elements", return_value=found):
            result = assertions.assert_element("Toggle", expected_states=["checked", "enabled"])

        assert result["passed"] is True
        checks = {c["check"]: c["passed"] for c in result["checks"]}
        assert checks.get("expected_state:checked") is True

    def test_expected_states_fail(self) -> None:
        found = {
            "success": True,
            "matches": [
                {
                    "id": "0/1",
                    "name": "Toggle",
                    "role": "toggle button",
                    "states": ["enabled", "showing"],
                }
            ],
        }
        with _patch("find_elements", return_value=found):
            result = assertions.assert_element("Toggle", expected_states=["checked"])

        assert result["passed"] is False

    def test_unexpected_states_pass(self) -> None:
        found = {
            "success": True,
            "matches": [
                {
                    "id": "0/1",
                    "name": "Btn",
                    "role": "push button",
                    "states": ["enabled", "showing"],
                }
            ],
        }
        with _patch("find_elements", return_value=found):
            result = assertions.assert_element("Btn", unexpected_states=["disabled"])

        assert result["passed"] is True

    def test_unexpected_states_fail(self) -> None:
        found = {
            "success": True,
            "matches": [
                {
                    "id": "0/1",
                    "name": "Btn",
                    "role": "push button",
                    "states": ["enabled", "showing", "disabled"],
                }
            ],
        }
        with _patch("find_elements", return_value=found):
            result = assertions.assert_element("Btn", unexpected_states=["disabled"])

        assert result["passed"] is False

    def test_with_role(self) -> None:
        found = {
            "success": True,
            "matches": [{"id": "0/2", "name": "X", "role": "dialog", "states": ["showing"]}],
        }
        with _patch("find_elements", return_value=found) as mock_find:
            result = assertions.assert_element("X", role="dialog")

        assert result["passed"] is True
        call_kwargs = mock_find.call_args
        assert call_kwargs is not None


class TestAssertText:
    def test_contains_match(self) -> None:
        mock_acc = MagicMock()
        with (
            _patch("_resolve_element", return_value=mock_acc),
            _patch("_element_text_preview", return_value="Hello World"),
        ):
            result = assertions.assert_text("0/1", "World", match="contains")

        assert result["passed"] is True
        assert result["actual"] == "Hello World"

    def test_contains_no_match(self) -> None:
        mock_acc = MagicMock()
        with (
            _patch("_resolve_element", return_value=mock_acc),
            _patch("_element_text_preview", return_value="Hello World"),
        ):
            result = assertions.assert_text("0/1", "Goodbye", match="contains")

        assert result["passed"] is False

    def test_exact_match(self) -> None:
        mock_acc = MagicMock()
        with (
            _patch("_resolve_element", return_value=mock_acc),
            _patch("_element_text_preview", return_value="exact text"),
        ):
            result = assertions.assert_text("0/1", "exact text", match="exact")

        assert result["passed"] is True

    def test_startswith_match(self) -> None:
        mock_acc = MagicMock()
        with (
            _patch("_resolve_element", return_value=mock_acc),
            _patch("_element_text_preview", return_value="Hello World"),
        ):
            result = assertions.assert_text("0/1", "Hello", match="startswith")

        assert result["passed"] is True

    def test_regex_match(self) -> None:
        mock_acc = MagicMock()
        with (
            _patch("_resolve_element", return_value=mock_acc),
            _patch("_element_text_preview", return_value="Error code: 404"),
        ):
            result = assertions.assert_text("0/1", r"code:\s+\d+", match="regex")

        assert result["passed"] is True

    def test_null_text(self) -> None:
        mock_acc = MagicMock()
        with (
            _patch("_resolve_element", return_value=mock_acc),
            _patch("_element_text_preview", return_value=None),
        ):
            result = assertions.assert_text("0/1", "anything")

        assert result["passed"] is False

    def test_element_not_found(self) -> None:
        with _patch(
            "_resolve_element",
            side_effect=ValueError("Element not found: 99"),
        ):
            result = assertions.assert_text("99", "text")

        assert result["passed"] is False
        assert "error" in result

    def test_returns_expected_and_match(self) -> None:
        mock_acc = MagicMock()
        with (
            _patch("_resolve_element", return_value=mock_acc),
            _patch("_element_text_preview", return_value="foo"),
        ):
            result = assertions.assert_text("0/1", "foo", match="exact")

        assert result["expected"] == "foo"
        assert result["match"] == "exact"
