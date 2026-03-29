from __future__ import annotations

from typing import Any

from ..runtime.gi_env import Gio

JsonDict = dict[str, Any]


def _app_info_to_dict(info: Gio.DesktopAppInfo) -> JsonDict:
    icon = info.get_icon()
    return {
        "desktop_id": info.get_id(),
        "name": info.get_name(),
        "description": info.get_description() or "",
        "executable": info.get_executable(),
        "categories": info.get_categories() or "",
        "icon": icon.to_string() if icon is not None else None,
    }


def list_desktop_apps(
    query: str = "",
    include_hidden: bool = False,
    max_results: int = 50,
) -> JsonDict:
    if query:
        groups = Gio.DesktopAppInfo.search(query)
        desktop_ids = [did for group in groups for did in group]
        results: list[JsonDict] = []
        for desktop_id in desktop_ids:
            try:
                info = Gio.DesktopAppInfo.new(desktop_id)
            except TypeError:
                continue
            if not include_hidden and (info.get_is_hidden() or info.get_nodisplay()):
                continue
            results.append(_app_info_to_dict(info))
            if len(results) >= max_results:
                break
        return {"success": True, "apps": results, "count": len(results)}

    results = []
    for info in Gio.AppInfo.get_all():
        if not include_hidden and (info.get_is_hidden() or info.get_nodisplay()):
            continue
        results.append(_app_info_to_dict(info))
        if len(results) >= max_results:
            break
    return {"success": True, "apps": results, "count": len(results)}


def launch_app(desktop_id: str) -> JsonDict:
    if not desktop_id.endswith(".desktop"):
        desktop_id = f"{desktop_id}.desktop"

    try:
        info = Gio.DesktopAppInfo.new(desktop_id)
    except TypeError:
        return {"success": False, "error": f"Desktop application not found: {desktop_id}"}

    ctx = Gio.AppLaunchContext()
    try:
        launched = info.launch([], ctx)
    except Exception as exc:
        return {"success": False, "error": str(exc), "desktop_id": desktop_id}

    if not launched:
        return {"success": False, "error": f"Application launch failed for {desktop_id}"}

    return {
        "success": True,
        "desktop_id": desktop_id,
        "name": info.get_name(),
        "executable": info.get_executable(),
    }
