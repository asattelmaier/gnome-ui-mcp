"""Tests for scroll_to_element (Item 10)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import scroll

_MOD = "gnome_ui_mcp.desktop.scroll"


class TestScrollToElementAlreadyShowing:
    def test_element_already_showing(self) -> None:
        mock_acc = MagicMock()
        state_set = MagicMock()
        state_set.contains.return_value = True
        mock_acc.get_state_set.return_value = state_set

        bounds = {"x": 100, "y": 200, "width": 50, "height": 30}

        with (
            patch(f"{_MOD}.accessibility._resolve_element", return_value=mock_acc),
            patch(f"{_MOD}.accessibility._is_showing", return_value=True),
            patch(f"{_MOD}.accessibility._element_bounds", return_value=bounds),
        ):
            result = scroll.scroll_to_element("0/1/2")

        assert result["success"] is True
        assert result["scrolls_performed"] == 0
        assert result["now_showing"] is True

    def test_returns_element_bounds(self) -> None:
        mock_acc = MagicMock()
        bounds = {"x": 10, "y": 20, "width": 100, "height": 40}

        with (
            patch(f"{_MOD}.accessibility._resolve_element", return_value=mock_acc),
            patch(f"{_MOD}.accessibility._is_showing", return_value=True),
            patch(f"{_MOD}.accessibility._element_bounds", return_value=bounds),
        ):
            result = scroll.scroll_to_element("0/0/0")

        assert result["element_bounds"] == bounds


class TestScrollToElementViaScrollTo:
    def test_atspi_scroll_to_succeeds(self) -> None:
        mock_acc = MagicMock()
        mock_comp = MagicMock()
        mock_comp.scroll_to.return_value = True
        mock_acc.get_component_iface.return_value = mock_comp
        bounds = {"x": 50, "y": 60, "width": 80, "height": 30}

        showing_calls = {"n": 0}

        def is_showing_side_effect(acc):
            showing_calls["n"] += 1
            return showing_calls["n"] > 1

        with (
            patch(f"{_MOD}.accessibility._resolve_element", return_value=mock_acc),
            patch(f"{_MOD}.accessibility._is_showing", side_effect=is_showing_side_effect),
            patch(f"{_MOD}.accessibility._element_bounds", return_value=bounds),
        ):
            result = scroll.scroll_to_element("0/1/0")

        assert result["success"] is True
        assert result["scrolls_performed"] == 0


class TestScrollToElementFallback:
    def test_fallback_scroll_by_parent(self) -> None:
        """When scroll_to API fails, fall back to scrolling in parent container."""
        mock_element = MagicMock()
        mock_comp = MagicMock()
        mock_comp.scroll_to.return_value = False
        mock_element.get_component_iface.return_value = mock_comp
        mock_element.get_role_name.return_value = "label"
        mock_element.get_parent.return_value = None

        scroll_call_count = {"n": 0}
        showing_calls = {"n": 0}

        def is_showing_side_effect(acc):
            showing_calls["n"] += 1
            return showing_calls["n"] > 3

        scroll_parent = MagicMock()
        scroll_parent.get_role_name.return_value = "scroll pane"
        scroll_parent_bounds = {"x": 0, "y": 0, "width": 400, "height": 600}
        mock_element.get_parent.return_value = scroll_parent
        element_bounds = {"x": 50, "y": 700, "width": 80, "height": 30}

        def perform_scroll_side_effect(*args, **kwargs):
            scroll_call_count["n"] += 1
            return {"success": True}

        with (
            patch(f"{_MOD}.accessibility._resolve_element", return_value=mock_element),
            patch(f"{_MOD}.accessibility._is_showing", side_effect=is_showing_side_effect),
            patch(
                f"{_MOD}.accessibility._element_bounds",
                side_effect=[element_bounds, scroll_parent_bounds, element_bounds, element_bounds],
            ),
            patch(f"{_MOD}.input.perform_scroll", side_effect=perform_scroll_side_effect),
        ):
            result = scroll.scroll_to_element("0/1/2", max_scrolls=5)

        assert result["success"] is True
        assert result["scrolls_performed"] > 0

    def test_max_scrolls_exceeded(self) -> None:
        mock_element = MagicMock()
        mock_comp = MagicMock()
        mock_comp.scroll_to.return_value = False
        mock_element.get_component_iface.return_value = mock_comp
        mock_element.get_role_name.return_value = "label"
        mock_element.get_parent.return_value = None
        bounds = {"x": 50, "y": 700, "width": 80, "height": 30}

        with (
            patch(f"{_MOD}.accessibility._resolve_element", return_value=mock_element),
            patch(f"{_MOD}.accessibility._is_showing", return_value=False),
            patch(f"{_MOD}.accessibility._element_bounds", return_value=bounds),
        ):
            result = scroll.scroll_to_element("0/1/2", max_scrolls=3)

        assert result["success"] is False
        assert result["now_showing"] is False


class TestScrollToElementEdgeCases:
    def test_element_not_found(self) -> None:
        with patch(
            f"{_MOD}.accessibility._resolve_element",
            side_effect=ValueError("Element not found: 99/99"),
        ):
            result = scroll.scroll_to_element("99/99")

        assert result["success"] is False
        assert "error" in result

    def test_no_bounds(self) -> None:
        mock_acc = MagicMock()
        mock_comp = MagicMock()
        mock_comp.scroll_to.return_value = False
        mock_acc.get_component_iface.return_value = mock_comp
        mock_acc.get_role_name.return_value = "label"
        mock_acc.get_parent.return_value = None

        with (
            patch(f"{_MOD}.accessibility._resolve_element", return_value=mock_acc),
            patch(f"{_MOD}.accessibility._is_showing", return_value=False),
            patch(f"{_MOD}.accessibility._element_bounds", return_value=None),
        ):
            result = scroll.scroll_to_element("0/1/2", max_scrolls=2)

        assert result["success"] is False
