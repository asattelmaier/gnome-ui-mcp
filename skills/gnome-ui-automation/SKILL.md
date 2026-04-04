---
name: gnome-ui-automation
description: Uses GNOME UI MCP for desktop automation via AT-SPI discovery and Mutter input. Use when automating GNOME desktop interactions, clicking buttons, filling forms, navigating menus, or controlling windows.
---

## Core Concepts

**Desktop lifecycle**: AT-SPI connects lazily on the first tool call. The server requires a running GNOME Wayland session with accessibility enabled (`gsettings set org.gnome.desktop.interface toolkit-accessibility true`).

**Element identification**: Use `find_elements` to search for UI elements by text, role, or application. Each element has a unique `id` (e.g. `0/1/2`) that represents its path in the AT-SPI tree. Element IDs can become stale after UI changes.

**Input backends**: The server tries Mutter Remote Desktop first for keyboard and mouse input, falling back to AT-SPI if unavailable. This is transparent to the caller.

## Workflow Patterns

### Before interacting with an element

1. Discover: `list_applications` to see running apps
2. Find: `find_elements` with a text query and optional role filter
3. Verify: Check the element's `id`, `role`, and `bounds` in the result
4. Act: Use `click_element`, `activate_element`, or `type_text`
5. Confirm: `wait_for_element` or `screenshot` to verify the action took effect

### Clicking elements

- Prefer `click_element` over `click_at` when you have an element ID
- Use `activate_element` when click doesn't work (tries action, keyboard, then mouse fallback)
- Use `find_and_activate` for a single find-then-activate step
- Check `input_injected` and `effect_verified` in the response to confirm success

### Typing text

- `type_text` types at the current keyboard focus
- `set_element_text` replaces the full text content of an editable element
- `type_into` combines OCR-based label finding with typing (for forms)

### Menu navigation

- `navigate_menu` walks a menu path like `["File", "Save As..."]`
- Each step finds and activates the menu item, waiting for submenus to appear

### Window management

- `list_windows` to find windows, `close_window` to close the focused one
- `move_window`, `resize_window`, `snap_window` for layout control
- `toggle_window_state` for fullscreen/maximize/minimize

### Efficient discovery

- Use `role` filter to narrow results: `find_elements(query="Save", role="push button")`
- Use `app_name` to scope to one application
- Use `within_element_id` to search within a subtree
- Use `showing_only=True` (default) to skip hidden elements
- Use `accessibility_tree` for a structural overview of an app

### Parallel execution

Multiple read-only tools (list, find, screenshot) can run in parallel. Mutating tools (click, type, key) should run sequentially to avoid race conditions.

## Troubleshooting

If elements cannot be found:

- Take a `screenshot` to see the current desktop state
- Use `accessibility_tree` to inspect the full element hierarchy
- Some elements may not be exposed via AT-SPI (e.g. web content inside Electron apps)

If clicks don't work:

- Try `activate_element` which uses multiple strategies
- Check if the element is behind another window
- Verify `effect_verified` in the response
