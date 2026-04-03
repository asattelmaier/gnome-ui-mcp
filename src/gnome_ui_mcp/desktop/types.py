from __future__ import annotations

from dataclasses import dataclass
from typing import Any

JsonDict = dict[str, object]


def unpack_variant(val: Any) -> Any:
    """Recursively unpack GLib.Variant values into plain Python objects."""
    from ..runtime.gi_env import GLib

    if isinstance(val, GLib.Variant):
        return unpack_variant(val.unpack())
    if isinstance(val, dict):
        return {k: unpack_variant(v) for k, v in val.items()}
    if isinstance(val, list | tuple):
        unpacked = [unpack_variant(item) for item in val]
        return tuple(unpacked) if isinstance(val, tuple) else unpacked
    return val


@dataclass(frozen=True)
class ElementFilter:
    """Groups the repeated search parameters used by find_elements and wait_for_element."""

    query: str = ""
    role: str | None = None
    app_name: str | None = None
    showing_only: bool = True
    clickable_only: bool = False
    bounds_only: bool = False
    within_element_id: str | None = None
    within_popup: bool = False


@dataclass(frozen=True)
class SettleOptions:
    """Groups the timing parameters for waiting for shell state to stabilise after an action."""

    settle_timeout_ms: int = 1_500
    stable_for_ms: int = 250
    poll_interval_ms: int = 50


@dataclass(frozen=True)
class TreeOptions:
    """Groups the accessibility tree serialisation parameters."""

    max_depth: int = 4
    include_actions: bool = False
    include_text: bool = False
    filter_roles: list[str] | None = None
    filter_states: list[str] | None = None
    showing_only: bool = False


@dataclass
class Locator:
    """Serialisable pointer that can be used to relocate an element after stale IDs."""

    query: str | None = None
    role: str | None = None
    app_name: str | None = None
    within_element_id: str | None = None
    within_popup: bool = False

    def to_dict(self) -> JsonDict:
        d: JsonDict = {}
        if self.query is not None:
            d["query"] = self.query
        if self.role is not None:
            d["role"] = self.role
        if self.app_name is not None:
            d["app_name"] = self.app_name
        if self.within_element_id is not None:
            d["within_element_id"] = self.within_element_id
        if self.within_popup:
            d["within_popup"] = True
        return d

    @classmethod
    def from_dict(cls, d: JsonDict) -> Locator:
        return cls(
            query=str(d["query"]) if "query" in d else None,
            role=str(d["role"]) if "role" in d else None,
            app_name=str(d["app_name"]) if "app_name" in d else None,
            within_element_id=str(d["within_element_id"]) if "within_element_id" in d else None,
            within_popup=bool(d.get("within_popup", False)),
        )


@dataclass
class EffectContext:
    """Snapshot of observable shell state before or after an interaction."""

    shell_popups: list[str]
    element: JsonDict | None = None
