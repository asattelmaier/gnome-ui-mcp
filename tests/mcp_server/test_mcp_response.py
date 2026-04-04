"""Tests for McpResponse builder."""

from __future__ import annotations

import json

from gnome_ui_mcp.mcp_response import McpResponse


class TestMcpResponseSuccess:
    def test_default_is_not_error(self) -> None:
        r = McpResponse()
        assert r.is_error is False
        assert r.error is None

    def test_set_data(self) -> None:
        r = McpResponse()
        r.set_data("key", "value")
        result = r.to_tool_result()
        assert result.isError is False
        assert result.structuredContent["key"] == "value"

    def test_set_items(self) -> None:
        r = McpResponse()
        r.set_items("things", [{"a": 1}, {"a": 2}])
        structured = r.to_tool_result().structuredContent
        assert structured["things"] == [{"a": 1}, {"a": 2}]

    def test_set_matches(self) -> None:
        r = McpResponse()
        r.set_matches([{"id": "0/1", "name": "Button"}])
        structured = r.to_tool_result().structuredContent
        assert len(structured["matches"]) == 1

    def test_set_trees(self) -> None:
        r = McpResponse()
        r.set_trees([{"name": "app", "children": []}])
        structured = r.to_tool_result().structuredContent
        assert len(structured["trees"]) == 1

    def test_set_screenshot(self) -> None:
        r = McpResponse()
        r.set_screenshot(path="/tmp/s.png", scale_factor=2, pixel_size=[200, 100])
        structured = r.to_tool_result().structuredContent
        assert structured["path"] == "/tmp/s.png"
        assert structured["scale_factor"] == 2
        assert "image_base64" not in structured


class TestMcpResponseError:
    def test_set_error(self) -> None:
        r = McpResponse()
        r.set_error("something broke")
        assert r.is_error is True
        assert r.error == "something broke"

    def test_error_result_has_no_structured_content(self) -> None:
        r = McpResponse()
        r.set_data("key", "value")
        r.set_error("fail")
        result = r.to_tool_result()
        assert result.isError is True
        assert result.content[0].text == "fail"
        # Error responses have no structuredContent
        assert result.structuredContent is None

    def test_fail_factory(self) -> None:
        r = McpResponse.fail("bad")
        result = r.to_tool_result()
        assert result.isError is True
        assert result.content[0].text == "bad"
        assert result.structuredContent is None


class TestDualContent:
    def test_text_lines_used_as_content(self) -> None:
        r = McpResponse()
        r.append_text("Line 1.")
        r.append_text("Line 2.")
        result = r.to_tool_result()
        assert result.content[0].text == "Line 1.\nLine 2."

    def test_text_lines_in_structured_content_as_message(self) -> None:
        r = McpResponse()
        r.append_text("Hello.")
        r.set_data("x", 42)
        structured = r.to_tool_result().structuredContent
        assert structured["message"] == "Hello."
        assert structured["x"] == 42

    def test_no_text_falls_back_to_json(self) -> None:
        r = McpResponse()
        r.set_data("x", 42)
        result = r.to_tool_result()
        text = result.content[0].text
        parsed = json.loads(text)
        assert parsed["x"] == 42

    def test_error_text_is_error_message(self) -> None:
        r = McpResponse()
        r.set_error("bad")
        result = r.to_tool_result()
        assert result.content[0].text == "bad"


class TestImageContent:
    def test_attach_image_adds_to_content(self) -> None:
        r = McpResponse()
        r.append_text("Screenshot taken.")
        r.attach_image("iVBOR...", mime_type="image/png")
        result = r.to_tool_result()
        # Text first, then image
        assert len(result.content) == 2
        assert result.content[0].type == "text"
        assert result.content[1].type == "image"
        assert result.content[1].data == "iVBOR..."
        assert result.content[1].mimeType == "image/png"

    def test_image_not_in_structured_content(self) -> None:
        r = McpResponse()
        r.attach_image("abc123")
        structured = r.to_tool_result().structuredContent
        assert "image_base64" not in structured

    def test_multiple_images(self) -> None:
        r = McpResponse()
        r.attach_image("img1")
        r.attach_image("img2")
        result = r.to_tool_result()
        assert len(result.content) == 3  # text + 2 images
