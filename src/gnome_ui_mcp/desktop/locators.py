from __future__ import annotations

from typing import Any

JsonDict = dict[str, Any]

RECENT_LOCATORS: dict[str, JsonDict] = {}


def _clean_locator_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def build_locator(
    *,
    name: str,
    description: str,
    role_name: str,
    app_label: str,
    within_element_id: str | None = None,
    within_popup: bool = False,
) -> JsonDict:
    locator: JsonDict = {}
    query = _clean_locator_value(name) or _clean_locator_value(description)
    role_value = _clean_locator_value(role_name)
    app_value = _clean_locator_value(app_label)

    if query is not None:
        locator["query"] = query
    if role_value is not None:
        locator["role"] = role_value
    if app_value is not None:
        locator["app_name"] = app_value
    if within_element_id is not None:
        locator["within_element_id"] = within_element_id
    if within_popup:
        locator["within_popup"] = True

    return locator


def remember_locator(element_id: str, locator: JsonDict) -> None:
    if not locator:
        return
    RECENT_LOCATORS[element_id] = dict(locator)


def locator_for_element_id(element_id: str) -> JsonDict | None:
    locator = RECENT_LOCATORS.get(element_id)
    return dict(locator) if locator is not None else None


def relocate_from_locator(
    locator: JsonDict,
    *,
    max_results: int = 1,
) -> JsonDict:
    query = str(locator.get("query", "")).strip()
    role = str(locator.get("role", "")).strip() or None
    app_name = str(locator.get("app_name", "")).strip() or None
    within_element_id = str(locator.get("within_element_id", "")).strip() or None
    within_popup = bool(locator.get("within_popup"))

    if query == "" and role is None:
        return {
            "success": False,
            "error": "Locator must include at least a query or role",
            "locator": locator,
        }

    from . import accessibility

    result = accessibility.find_elements(
        query=query,
        app_name=app_name,
        role=role,
        max_results=max_results,
        showing_only=True,
        within_element_id=within_element_id,
        within_popup=within_popup,
    )
    matches = result.get("matches", [])
    if not matches:
        return {
            "success": False,
            "error": "No element matched locator",
            "locator": locator,
        }

    return {
        "success": True,
        "locator": locator,
        "match": matches[0],
    }
