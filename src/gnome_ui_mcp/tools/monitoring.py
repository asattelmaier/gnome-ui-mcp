"""Event monitoring and notification tools."""

from __future__ import annotations

from ..adapters import monitoring
from ..formatters.monitoring_formatter import (
    NotificationListFormatter,
    PollResultFormatter,
    PopupListFormatter,
)
from ..mcp_context import McpContext
from ..mcp_response import McpResponse
from .categories import ToolCategory
from .tool_definition import ToolRequest, define_tool

# -- subscribe_events --


def _subscribe_events(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    event_types = request.params.get("event_types", None)
    app_name = request.params.get("app_name", None)
    if event_types is None:
        event_types = []
    result = monitoring.subscribe_events(event_types=event_types, app_name=app_name)
    response.set_data("subscription_id", result.subscription_id)
    response.set_data("event_types", result.event_types)
    response.append_text(f"Subscribed to events. ID: {result.subscription_id}")


subscribe_events = define_tool(
    name="subscribe_events",
    description="Subscribe to AT-SPI events. Returns subscription ID.",
    handler=_subscribe_events,
    category=ToolCategory.MONITORING,
    read_only=False,
    parameters={
        "event_types": {
            "type": "array",
            "items_type": "string",
            "description": "List of AT-SPI event types to subscribe to.",
        },
        "app_name": {
            "type": "string",
            "default": None,
            "description": "Filter events to this application.",
        },
    },
)


# -- poll_events --


def _poll_events(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    subscription_id = request.params.get("subscription_id", "")
    timeout_ms = request.params.get("timeout_ms", 5000)
    max_events = request.params.get("max_events", 100)
    result = monitoring.poll_events(
        subscription_id=subscription_id,
        timeout_ms=timeout_ms,
        max_events=max_events,
    )
    fmt = PollResultFormatter(result)
    response.set_items("events", fmt.to_json())
    response.set_data("count", result.count)
    response.append_text(fmt.to_string())


poll_events = define_tool(
    name="poll_events",
    description="Poll for captured AT-SPI events.",
    handler=_poll_events,
    category=ToolCategory.MONITORING,
    parameters={
        "subscription_id": {
            "type": "string",
            "description": "Subscription ID from subscribe_events.",
        },
        "timeout_ms": {
            "type": "integer",
            "default": 5000,
            "description": "Maximum time to wait for events.",
        },
        "max_events": {
            "type": "integer",
            "default": 100,
            "description": "Maximum number of events to return.",
        },
    },
)


# -- unsubscribe_events --


def _unsubscribe_events(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    subscription_id = request.params.get("subscription_id", "")
    monitoring.unsubscribe_events(subscription_id=subscription_id)
    response.append_text(f"Unsubscribed from events: {subscription_id}")


unsubscribe_events = define_tool(
    name="unsubscribe_events",
    description="Unsubscribe from AT-SPI events.",
    handler=_unsubscribe_events,
    category=ToolCategory.MONITORING,
    read_only=False,
    parameters={
        "subscription_id": {
            "type": "string",
            "description": "Subscription ID to unsubscribe.",
        },
    },
)


# -- notification_monitor_start --


def _notification_monitor_start(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    monitoring.notification_monitor_start()
    response.append_text("Notification monitor started.")


notification_monitor_start = define_tool(
    name="notification_monitor_start",
    description="Start monitoring desktop notifications.",
    handler=_notification_monitor_start,
    category=ToolCategory.MONITORING,
    read_only=False,
)


# -- notification_monitor_read --


def _notification_monitor_read(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    clear = request.params.get("clear", True)
    result = monitoring.notification_monitor_read(clear=clear)
    fmt = NotificationListFormatter(result)
    response.set_items("notifications", fmt.to_json())
    response.set_data("count", result.count)
    response.append_text(fmt.to_string())


notification_monitor_read = define_tool(
    name="notification_monitor_read",
    description="Read captured notifications since monitoring started.",
    handler=_notification_monitor_read,
    category=ToolCategory.MONITORING,
    parameters={
        "clear": {
            "type": "boolean",
            "default": True,
            "description": "Clear notifications after reading.",
        },
    },
)


# -- notification_monitor_stop --


def _notification_monitor_stop(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    monitoring.notification_monitor_stop()
    response.append_text("Notification monitor stopped.")


notification_monitor_stop = define_tool(
    name="notification_monitor_stop",
    description="Stop monitoring desktop notifications.",
    handler=_notification_monitor_stop,
    category=ToolCategory.MONITORING,
    read_only=False,
)


# -- dismiss_notification --


def _dismiss_notification(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    notification_id = request.params.get("notification_id", 0)
    monitoring.dismiss_notification(notification_id=notification_id)
    response.append_text(f"Dismissed notification {notification_id}.")


dismiss_notification = define_tool(
    name="dismiss_notification",
    description="Dismiss a desktop notification by its ID via D-Bus CloseNotification.",
    handler=_dismiss_notification,
    category=ToolCategory.MONITORING,
    read_only=False,
    parameters={
        "notification_id": {
            "type": "integer",
            "description": "Notification ID to dismiss.",
        },
    },
)


# -- click_notification_action --


def _click_notification_action(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    notification_id = request.params.get("notification_id", 0)
    action_key = request.params.get("action_key", "")
    monitoring.click_notification_action(
        notification_id=notification_id,
        action_key=action_key,
    )
    response.append_text(f"Invoked action '{action_key}' on notification {notification_id}.")


click_notification_action = define_tool(
    name="click_notification_action",
    description="Invoke an action on a desktop notification by its ID and action key.",
    handler=_click_notification_action,
    category=ToolCategory.MONITORING,
    read_only=False,
    parameters={
        "notification_id": {
            "type": "integer",
            "description": "Notification ID.",
        },
        "action_key": {
            "type": "string",
            "description": "Action key to invoke.",
        },
    },
)


# -- visible_shell_popups --


def _visible_shell_popups(
    request: ToolRequest,
    response: McpResponse,
    context: McpContext,
) -> None:
    popups = monitoring.visible_shell_popups()
    fmt = PopupListFormatter(popups)
    response.set_items("popups", fmt.to_json())
    response.set_data("count", len(popups))
    response.append_text(fmt.to_string())


visible_shell_popups = define_tool(
    name="visible_shell_popups",
    description="Return visible GNOME Shell popup or menu containers.",
    handler=_visible_shell_popups,
    category=ToolCategory.MONITORING,
)
