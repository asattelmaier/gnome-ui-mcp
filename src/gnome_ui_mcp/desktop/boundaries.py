"""Application boundary enforcement (Item 14)."""

from __future__ import annotations

from typing import Any

from . import accessibility

JsonDict = dict[str, Any]

# Module-level boundary state
_boundaries: JsonDict = {
    "app_name": None,
    "allow_global_keys": [],
}


def set_boundaries(
    app_name: str | None = None,
    allow_global_keys: list[str] | None = None,
) -> JsonDict:
    """Set an application-level boundary for element operations.

    When a boundary is active, :func:`check_boundary` will reject any
    element that does not belong to *app_name*.
    """
    _boundaries["app_name"] = app_name
    _boundaries["allow_global_keys"] = list(allow_global_keys or [])
    return {
        "success": True,
        "app_name": app_name,
        "allow_global_keys": list(_boundaries["allow_global_keys"]),
    }


def clear_boundaries() -> JsonDict:
    """Remove all boundary restrictions."""
    _boundaries["app_name"] = None
    _boundaries["allow_global_keys"] = []
    return {"success": True}


def check_boundary(element_id: str) -> JsonDict:
    """Check whether *element_id* is within the configured boundary.

    Returns ``{"allowed": True}`` when no boundary is active or the
    element belongs to the permitted application.
    """
    bound_app = _boundaries.get("app_name")
    if bound_app is None:
        return {"allowed": True}

    actual_app = accessibility._application_name_for_element_id(element_id)
    if actual_app and bound_app.casefold() in actual_app.casefold():
        return {"allowed": True, "app_name": actual_app}

    return {
        "allowed": False,
        "error": (
            f"Boundary violation: element belongs to {actual_app!r}, "
            f"but boundary restricts to {bound_app!r}"
        ),
        "element_app": actual_app,
        "boundary_app": bound_app,
    }
