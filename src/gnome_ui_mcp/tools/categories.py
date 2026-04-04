"""Tool categories for grouping and feature gating."""

from __future__ import annotations

from enum import Enum


class ToolCategory(Enum):
    ACCESSIBILITY = "accessibility"
    APPS = "apps"
    INPUT = "input"
    MONITORING = "monitoring"
    RECORDING = "recording"
    SESSION = "session"
    SETTINGS = "settings"
    STATE = "state"
    SYSTEM = "system"
    VISUAL = "visual"
    WAITING = "waiting"
    WINDOW = "window"
    WORKSPACE = "workspace"

    @property
    def label(self) -> str:
        return TOOL_CATEGORY_LABELS[self]


TOOL_CATEGORY_LABELS: dict[ToolCategory, str] = {
    ToolCategory.ACCESSIBILITY: "Accessibility",
    ToolCategory.APPS: "Applications",
    ToolCategory.INPUT: "Input Automation",
    ToolCategory.MONITORING: "Monitoring",
    ToolCategory.RECORDING: "Recording",
    ToolCategory.SESSION: "Session",
    ToolCategory.SETTINGS: "Settings",
    ToolCategory.STATE: "State",
    ToolCategory.SYSTEM: "System",
    ToolCategory.VISUAL: "Visual",
    ToolCategory.WAITING: "Waiting",
    ToolCategory.WINDOW: "Window Management",
    ToolCategory.WORKSPACE: "Workspace",
}
