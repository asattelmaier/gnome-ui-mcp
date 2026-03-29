"""Tests for subscribe_events / poll_events / unsubscribe (Item 12)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import events

_MOD = "gnome_ui_mcp.desktop.events"


class TestSubscribe:
    def test_subscribe_returns_id(self) -> None:
        mock_listener = MagicMock()
        with (
            patch(f"{_MOD}.Atspi") as mock_atspi,
            patch(f"{_MOD}._init_atspi"),
        ):
            mock_atspi.EventListener.new.return_value = mock_listener
            result = events.subscribe_events(["focus:"])

        assert result["success"] is True
        assert "subscription_id" in result
        mock_listener.register.assert_called_once_with("focus:")

    def test_subscribe_multiple_types(self) -> None:
        mock_listener = MagicMock()
        with (
            patch(f"{_MOD}.Atspi") as mock_atspi,
            patch(f"{_MOD}._init_atspi"),
        ):
            mock_atspi.EventListener.new.return_value = mock_listener
            result = events.subscribe_events(["focus:", "window:activate"])

        assert result["success"] is True
        assert mock_listener.register.call_count == 2

    def test_subscribe_empty_list(self) -> None:
        result = events.subscribe_events([])
        assert result["success"] is False


class TestPollEvents:
    def test_poll_returns_buffered(self) -> None:
        # Create a subscription and manually inject events
        sub = events.EventSubscription()
        sub.buffer.append(
            {
                "type": "focus:",
                "source_name": "btn",
                "source_role": "push button",
                "detail1": 0,
                "detail2": 0,
                "timestamp": 12345,
            }
        )
        events._subscriptions["test-id"] = sub

        try:
            with patch(f"{_MOD}.GLib"):
                result = events.poll_events("test-id", timeout_ms=50)

            assert result["success"] is True
            assert len(result["events"]) == 1
            assert result["events"][0]["source_name"] == "btn"
        finally:
            events._subscriptions.pop("test-id", None)

    def test_poll_unknown_subscription(self) -> None:
        result = events.poll_events("unknown-sub-id")
        assert result["success"] is False

    def test_poll_empty_buffer(self) -> None:
        sub = events.EventSubscription()
        events._subscriptions["empty-id"] = sub
        try:
            with patch(f"{_MOD}.GLib"):
                result = events.poll_events("empty-id", timeout_ms=50)
            assert result["success"] is True
            assert len(result["events"]) == 0
        finally:
            events._subscriptions.pop("empty-id", None)


class TestUnsubscribe:
    def test_unsubscribe_cleans_up(self) -> None:
        mock_listener = MagicMock()
        sub = events.EventSubscription()
        sub.listener = mock_listener
        sub.event_types = ["focus:"]
        events._subscriptions["unsub-id"] = sub

        try:
            result = events.unsubscribe("unsub-id")
            assert result["success"] is True
            mock_listener.deregister.assert_called_once_with("focus:")
            assert "unsub-id" not in events._subscriptions
        finally:
            events._subscriptions.pop("unsub-id", None)

    def test_unsubscribe_unknown(self) -> None:
        result = events.unsubscribe("bad-id")
        assert result["success"] is False
