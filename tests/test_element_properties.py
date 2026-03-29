"""Tests for get_element_properties (Item 2).

Verifies that AT-SPI value, selection, relation, attribute, and image
interfaces are queried and returned in a structured dict.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import accessibility

JsonDict = dict[str, Any]


def _mock_resolve(accessible: MagicMock) -> Any:
    return patch.object(accessibility, "_resolve_element", return_value=accessible)


def _make_accessible() -> MagicMock:
    mock = MagicMock()
    mock.get_name.return_value = "widget"
    mock.get_role_name.return_value = "slider"
    mock.get_value_iface.return_value = None
    mock.get_selection_iface.return_value = None
    mock.get_relation_set.return_value = []
    mock.get_attributes.return_value = {}
    mock.get_image_iface.return_value = None
    return mock


class TestValueInterface:
    """Value interface should return current/min/max/step."""

    def test_returns_value_data(self) -> None:
        acc = _make_accessible()
        value_iface = MagicMock()
        value_iface.get_current_value.return_value = 50.0
        value_iface.get_minimum_value.return_value = 0.0
        value_iface.get_maximum_value.return_value = 100.0
        value_iface.get_minimum_increment.return_value = 1.0
        acc.get_value_iface.return_value = value_iface

        with _mock_resolve(acc):
            result = accessibility.get_element_properties("0/1")

        assert result["success"] is True
        assert result["value"]["current"] == 50.0
        assert result["value"]["minimum"] == 0.0
        assert result["value"]["maximum"] == 100.0
        assert result["value"]["step"] == 1.0

    def test_no_value_interface(self) -> None:
        acc = _make_accessible()
        acc.get_value_iface.return_value = None

        with _mock_resolve(acc):
            result = accessibility.get_element_properties("0/1")

        assert result["success"] is True
        assert result["value"] is None


class TestSelectionInterface:
    """Selection interface should return n_selected and selected children."""

    def test_returns_selection_data(self) -> None:
        acc = _make_accessible()
        sel_iface = MagicMock()
        sel_iface.get_n_selected_children.return_value = 2
        child0 = MagicMock()
        child0.get_name.return_value = "Option A"
        child0.get_role_name.return_value = "list item"
        child1 = MagicMock()
        child1.get_name.return_value = "Option B"
        child1.get_role_name.return_value = "list item"
        sel_iface.get_selected_child.side_effect = [child0, child1]
        acc.get_selection_iface.return_value = sel_iface

        with _mock_resolve(acc):
            result = accessibility.get_element_properties("0/1")

        assert result["success"] is True
        assert result["selection"]["n_selected"] == 2
        assert len(result["selection"]["selected_children"]) == 2
        assert result["selection"]["selected_children"][0]["name"] == "Option A"

    def test_no_selection_interface(self) -> None:
        acc = _make_accessible()
        acc.get_selection_iface.return_value = None

        with _mock_resolve(acc):
            result = accessibility.get_element_properties("0/1")

        assert result["success"] is True
        assert result["selection"] is None


class TestRelationSet:
    """Relation set should return list of {type, targets}."""

    def test_returns_relations(self) -> None:
        acc = _make_accessible()
        rel = MagicMock()
        rel.get_relation_type.return_value = MagicMock(value_nick="labelled-by")
        target = MagicMock()
        target.get_name.return_value = "Label"
        target.get_role_name.return_value = "label"
        rel.get_n_targets.return_value = 1
        rel.get_target.side_effect = [target]
        acc.get_relation_set.return_value = [rel]

        with _mock_resolve(acc):
            result = accessibility.get_element_properties("0/1")

        assert result["success"] is True
        assert len(result["relations"]) == 1
        assert result["relations"][0]["type"] == "labelled-by"
        assert result["relations"][0]["targets"][0]["name"] == "Label"

    def test_empty_relations(self) -> None:
        acc = _make_accessible()
        acc.get_relation_set.return_value = []

        with _mock_resolve(acc):
            result = accessibility.get_element_properties("0/1")

        assert result["relations"] == []


class TestAttributes:
    """Attributes should return a dict of key-value pairs."""

    def test_returns_attributes(self) -> None:
        acc = _make_accessible()
        acc.get_attributes.return_value = {"xml-roles": "slider", "level": "3"}

        with _mock_resolve(acc):
            result = accessibility.get_element_properties("0/1")

        assert result["success"] is True
        assert result["attributes"]["xml-roles"] == "slider"
        assert result["attributes"]["level"] == "3"


class TestImageInterface:
    """Image interface should return description and size."""

    def test_returns_image_data(self) -> None:
        acc = _make_accessible()
        img_iface = MagicMock()
        img_iface.get_image_description.return_value = "A photo"
        size = MagicMock()
        size.x = 640
        size.y = 480
        img_iface.get_image_size.return_value = size
        acc.get_image_iface.return_value = img_iface

        with _mock_resolve(acc):
            result = accessibility.get_element_properties("0/1")

        assert result["success"] is True
        assert result["image"]["description"] == "A photo"
        assert result["image"]["width"] == 640
        assert result["image"]["height"] == 480

    def test_no_image_interface(self) -> None:
        acc = _make_accessible()
        acc.get_image_iface.return_value = None

        with _mock_resolve(acc):
            result = accessibility.get_element_properties("0/1")

        assert result["success"] is True
        assert result["image"] is None
