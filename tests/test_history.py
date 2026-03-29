"""Tests for record_action and get_action_history (Item 15)."""

from __future__ import annotations

from gnome_ui_mcp.desktop import history


class TestRecordAction:
    def test_record_and_retrieve(self) -> None:
        history._history.clear()
        history.record_action("click_element", {"element_id": "0/1/2"})
        entries = history.get_action_history(last_n=10)
        assert len(entries) == 1
        assert entries[0]["tool"] == "click_element"
        assert entries[0]["params"]["element_id"] == "0/1/2"

    def test_timestamp_present(self) -> None:
        history._history.clear()
        history.record_action("press_key", {"key_name": "Return"})
        entries = history.get_action_history()
        assert "timestamp" in entries[0]
        assert isinstance(entries[0]["timestamp"], int | float)


class TestGetActionHistory:
    def test_last_n(self) -> None:
        history._history.clear()
        for i in range(5):
            history.record_action(f"tool_{i}", {"i": i})
        entries = history.get_action_history(last_n=3)
        assert len(entries) == 3
        # Most recent first
        assert entries[0]["tool"] == "tool_4"

    def test_empty_history(self) -> None:
        history._history.clear()
        entries = history.get_action_history()
        assert entries == []

    def test_maxlen_enforced(self) -> None:
        history._history.clear()
        for i in range(150):
            history.record_action(f"tool_{i}", {"i": i})
        # deque maxlen=100
        assert len(history._history) <= 100


class TestUndoHints:
    def test_click_element_hint(self) -> None:
        history._history.clear()
        history.record_action("click_element", {"element_id": "0/1"})
        entries = history.get_action_history()
        assert entries[0]["undo_hint"] == "Escape"

    def test_type_text_hint(self) -> None:
        history._history.clear()
        history.record_action("type_text", {"text": "hello"})
        entries = history.get_action_history()
        assert entries[0]["undo_hint"] == "ctrl+z"

    def test_press_key_no_hint(self) -> None:
        history._history.clear()
        history.record_action("press_key", {"key_name": "Return"})
        entries = history.get_action_history()
        assert entries[0]["undo_hint"] is None
