"""Tests for find_elements click target resolution performance."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import accessibility as acc_mod
from gnome_ui_mcp.desktop.types import ElementFilter


class TestClickTargetResolutionCount:
    """_resolve_click_target_metadata must only be called for returned elements."""

    @patch.object(acc_mod, "_resolve_click_target_metadata")
    @patch.object(acc_mod, "_element_summary")
    @patch.object(acc_mod, "_element_bounds", return_value=None)
    @patch.object(acc_mod, "_element_states", return_value={"showing"})
    @patch.object(acc_mod, "_walk_tree")
    @patch.object(acc_mod, "_search_roots")
    def test_resolve_only_called_for_matching_elements(
        self,
        mock_roots: MagicMock,
        mock_walk: MagicMock,
        mock_states: MagicMock,
        mock_bounds: MagicMock,
        mock_summary: MagicMock,
        mock_resolve: MagicMock,
    ) -> None:
        """With a query filter, click target resolution skips non-matching elements."""
        # Build 5 fake elements: 2 match "Save", 3 do not.
        elements = []
        for i in range(5):
            elem = MagicMock()
            # Elements 0 and 3 have "Save" in name
            elem.get_name.return_value = "Save" if i in (0, 3) else "Open"
            elem.get_description.return_value = ""
            elem.get_role_name.return_value = "button"
            elements.append((elem, (0, i), i))

        mock_roots.return_value = [
            {
                "accessible": MagicMock(),
                "path": (0,),
                "application": "app",
                "scope": {},
            }
        ]
        mock_walk.return_value = iter(elements)
        mock_resolve.return_value = {
            "element_id": "0/0",
            "target_id": "0/0",
            "target_name": "Save",
            "target_role": "button",
            "target_bounds": {"x": 0, "y": 0, "width": 10, "height": 10},
            "strategy": "action",
            "distance": 0,
            "has_action": True,
            "focusable": True,
        }
        mock_summary.return_value = {
            "id": "0/0",
            "name": "Save",
            "role": "button",
            "states": ["showing"],
        }

        filt = ElementFilter(query="Save", showing_only=True)
        acc_mod.find_elements(filt=filt, max_results=10)

        # Only the 2 matching elements should trigger click target resolution
        assert mock_resolve.call_count == 2
