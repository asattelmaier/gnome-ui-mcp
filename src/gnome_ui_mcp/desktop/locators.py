from __future__ import annotations

from .types import JsonDict, Locator

RECENT_LOCATORS: dict[str, Locator] = {}
_MAX_LOCATORS = 5000
_EVICT_COUNT = 1000


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
) -> Locator:
    query = _clean_locator_value(name) or _clean_locator_value(description)
    role_value = _clean_locator_value(role_name)
    app_value = _clean_locator_value(app_label)

    return Locator(
        query=query,
        role=role_value,
        app_name=app_value,
        within_element_id=within_element_id,
        within_popup=within_popup,
    )


def remember_locator(element_id: str, locator: Locator) -> None:
    if not (locator.query or locator.role):
        return
    RECENT_LOCATORS[element_id] = locator
    if len(RECENT_LOCATORS) > _MAX_LOCATORS:
        keys = list(RECENT_LOCATORS)[:_EVICT_COUNT]
        for k in keys:
            del RECENT_LOCATORS[k]


def locator_for_element_id(element_id: str) -> Locator | None:
    return RECENT_LOCATORS.get(element_id)


def relocate_from_locator(
    locator: Locator,
    *,
    max_results: int = 1,
) -> JsonDict:
    query = locator.query or ""
    role = locator.role
    app_name = locator.app_name
    within_element_id = locator.within_element_id
    within_popup = locator.within_popup

    if not query and role is None:
        return {
            "success": False,
            "error": "Locator must include at least a query or role",
            "locator": locator.to_dict(),
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
            "locator": locator.to_dict(),
        }

    return {
        "success": True,
        "locator": locator.to_dict(),
        "match": matches[0],
    }
