# gnome-ui-mcp: Parity & Roadmap

> Last updated: 2026-03-28
>
> See [IMPLEMENTATION_PLANS.md](IMPLEMENTATION_PLANS.md) for detailed TDD plans per item.

## Current State

**Total tools across all branches: ~33 | Tests: 87 across 20 branches**

### Branches & PRs

| # | Branch | Status | What |
|---|--------|--------|------|
| 1 | fix/relax-python-version-constraint | PR upstream | Python >=3.12 (remove <3.13) |
| 2 | fix/voidsymbol-key-validation | PR upstream | VoidSymbol key name validation |
| 3 | feat/modifier-key-support | PR upstream | key_combo tool |
| 4 | feat/scroll-support | PR upstream | scroll tool |
| 5 | feat/dbus-screenshot | PR upstream | D-Bus Shell.Screenshot |
| 6 | fix/empty-element-id | PR upstream | Empty element_id validation |
| 7 | fix/stale-element-crash | PR upstream | Harden grab_focus/set_text_contents |
| 8 | perf/is-showing-o1 | PR upstream | O(1) _is_showing |
| 9 | fix/settle-verification | PR upstream | Fix settle overwriting verified=True |
| 10 | perf/atspi-get-focus | Fork only | Optimize focus metadata |
| 11 | feat/double-click | Fork only | click_count param (1-3) |
| 12 | feat/mouse-move | Fork only | mouse_move tool |
| 13 | feat/clipboard | Fork only | clipboard_read/write via wl-copy/wl-paste |
| 14 | feat/launch-app | Fork only | list_desktop_apps/launch_app |
| 15 | fix/loosen-mcp-pin | Fork only | mcp >=1.26,<2 |
| 16 | feat/drag | Fork only | drag tool (press-move-release) |
| 17 | feat/screenshot-region-window | Fork only | screenshot_area/screenshot_window |
| 18 | feat/select-text | Fork only | select_element_text |
| 19 | feat/hover-element | Fork only | hover_element |
| 20 | chore/pytest-ci | Fork only | pytest in check.sh + CI |

---

## Part 1: Parity Comparison vs kwin-mcp (isac322/kwin-mcp)

kwin-mcp has 29 tools, full session isolation, EIS input, AT-SPI2, touch input.

### Where we are AHEAD

| Area | Our advantage |
|------|---------------|
| **Accessibility** | More tools (find_elements, element_at_point, resolve_click_target, locators, recovery) |
| **Wait/polling** | 4 tools (wait_for_element, wait_for_element_gone, wait_for_popup_count, wait_for_shell_settled) vs their 1 |
| **Popup awareness** | visible_shell_popups — they have nothing |
| **Activation** | Multi-strategy activate_element + find_and_activate with fallback chains |
| **Effect verification** | Before/after verification on all interactions — they have none |
| **Element recovery** | Locator-based re-find for stale AT-SPI elements — they have none |
| **App discovery** | list_desktop_apps + launch_app — they only have launch_app |

### Where we have PARITY

| Area | Status |
|------|--------|
| Screenshots (full/area/window) | Both have all three |
| Scroll | Both have scroll tool |
| Clipboard | Both have read/write |
| Window listing | Both have list_windows |
| Mouse click/move/drag | Both have these |
| Keyboard type/press | Both have these |
| Key combos | Both have modifier support |

### Gaps to Close (what kwin-mcp has that we don't)

| # | Feature | kwin-mcp tools | Priority | Status |
|---|---------|---------------|----------|--------|
| G1 | Touch input (tap/swipe/pinch/multi-swipe) | touch_tap, touch_swipe, touch_pinch, touch_multi_swipe | High | DONE |
| G2 | Key hold (press without release) | keyboard_key_down, keyboard_key_up | High | DONE |
| G3 | Mouse hold (press without release) | mouse_button_down, mouse_button_up | High | DONE |
| G4 | Unicode text input (CJK, emoji) | keyboard_type_unicode | High | DONE |
| G5 | Screenshot burst after action | `screenshot_after_ms` param on action tools | Medium | TODO |
| G6 | Generic D-Bus call | dbus_call | High | TODO |
| G7 | App log capture (stdout/stderr) | read_app_log | Medium | TODO |
| G8 | Session isolation (gnome-shell --headless) | session_start, session_stop, session_info | Low | DONE |
| G9 | Wayland protocol introspection | wayland_info | Low | TODO |

---

## Part 2: Novel Features (no Linux GUI MCP server has these)

Researched: kwin-mcp, hyprland-mcp (alderban107), wayland-mcp (someaka), hyprmcp (stefanoamorelli).

### High Impact — Differentiators

| # | Feature | Description | Priority | Status |
|---|---------|-------------|----------|--------|
| N1 | OCR + AT-SPI hybrid | Tesseract for apps with bad a11y (Electron, games), AT-SPI for everything else. hyprland-mcp has OCR-only, we have AT-SPI-only — combining both is best-in-class | High | TODO |
| N2 | Desktop notification monitoring | Read notifications via org.freedesktop.Notifications D-Bus. Essential for verifying "did the action trigger a notification?" | High | TODO |
| N3 | Workspace management | Switch workspaces, move windows between workspaces via GNOME Shell D-Bus. Only Hyprland MCPs have workspace control | High | TODO |
| N4 | Monitor/display info | List monitors, resolutions, positions, scaling factors. Only Hyprland MCPs expose this | High | TODO |
| N5 | Screen recording / GIF capture | Record action sequences as GIF/video via PipeWire screencast. No MCP server does this | High | TODO |

### Medium Impact

| # | Feature | Description | Priority | Status |
|---|---------|-------------|----------|--------|
| N6 | dconf/GSettings read/write | Read/write GNOME settings (dark mode, font size, etc.). Unique to GNOME | Medium | TODO |
| N7 | Color/pixel sampling | Get pixel color at (x,y) from screenshot buffer. Verify visual state changes | Medium | TODO |
| N8 | Visual diff | Compare two screenshots, return changed regions as bounding boxes | Medium | TODO |
| N9 | Conditional action chains | "click X, wait for Y, then do Z" as a single tool call with retry logic | Medium | TODO |
| N10 | File dialog helper | Specialized tool for GTK file chooser dialogs — navigate, type path, select file | Medium | TODO |

### Lower Impact / Niche

| # | Feature | Description | Priority | Status |
|---|---------|-------------|----------|--------|
| N11 | GNOME Extensions control | Enable/disable/configure extensions via D-Bus | Low | TODO |
| N12 | System tray interaction | Read/click status icons (SNI protocol via D-Bus) | Low | TODO |
| N13 | Element highlight/annotate | Draw colored rectangle around element on-screen for visual debugging | Low | TODO |
| N14 | Input method (IME) support | IBus/Fcitx integration for CJK input natively on GNOME | Low | TODO |
| N15 | Undo verification | Ctrl+Z with before/after verification | Low | TODO |

---

## Implementation Order (dependency-optimized to avoid rework)

### Phase 1: input.py consolidation (all touch same class, must be sequential)
| # | Item | Why this order | Status |
|---|------|---------------|--------|
| 1 | G2 — Key hold (key_down/key_up) | Establishes press/release pattern + held-state tracking in `_MutterRemoteDesktopInput` | DONE |
| 2 | G3 — Mouse hold (button_down/button_up) | Same pattern for buttons, same class | DONE |
| 3 | G4 — Unicode text input (clipboard approach) | Uses Ctrl+V key combo from same class | DONE |
| 4 | G1 — Touch input (tap/swipe/pinch/multi) | Biggest input.py addition, benefits from stable class | DONE |

### Phase 2: D-Bus tools (new files, G6 establishes Variant serialization pattern)
| # | Item | Why this order | Status |
|---|------|---------------|--------|
| 5 | G6 — Generic D-Bus call | Builds GLib.Variant↔JSON serialization reused by 6-9 | DONE |
| 6 | N4 — Monitor/display info | Simple D-Bus read, new file | DONE |
| 7 | N3 — Workspace management | D-Bus + key combos, new file | DONE |
| 8 | N2 — Notification monitoring | D-Bus eavesdrop, new file | DONE |
| 9 | N5 — Screen recording / GIF | D-Bus Shell.Screencast, new file | DONE |

### Phase 3: Independent capabilities (new files, Pillow-dependent grouped)
| # | Item | Why this order | Status |
|---|------|---------------|--------|
| 10 | N1 — OCR hybrid (Tesseract + AT-SPI) | New desktop/ocr.py, adds pytesseract dep | DONE |
| 11 | N6 — dconf/GSettings read/write | New file, Gio.Settings API | DONE |
| 12 | N7 — Color/pixel sampling | Pillow-based, same dep as OCR | DONE |
| 13 | N8 — Visual diff | Pillow + scipy, same dep chain | DONE |

### Phase 4: Misc (trivial, no conflicts)
| # | Item | Why this order | Status |
|---|------|---------------|--------|
| 14 | G9 — Wayland info | Shells out to wayland-info | DONE |
| 15 | G7 — App log capture | Modifies feat/launch-app branch only | DONE |

### Phase 5: Modify existing tools (MUST be last — touches interaction.py action functions)
| # | Item | Why this order | Status |
|---|------|---------------|--------|
| 16 | G5 — Screenshot burst on actions | Adds screenshot_after_ms helper. Must be last so all action tools exist first. | DONE |

---

## Ecosystem Reference

| Project | Target | Stars | Tools | Strengths |
|---------|--------|-------|-------|-----------|
| isac322/kwin-mcp | KDE Plasma 6 | 12 | 29 | Session isolation, EIS, touch, burst screenshots |
| alderban107/hyprland-mcp | Hyprland | 2 | 27 | OCR, click_text, window mgmt, coord mapping |
| someaka/wayland-mcp | Generic | 17 | 8 | VLM analysis, action chaining, compositor-agnostic |
| stefanoamorelli/hyprmcp | Hyprland | 29 | 13 | Hyprctl wrapper, workspace/monitor query |
| **asattelmaier/gnome-ui-mcp** | **GNOME** | **0** | **~33** | **AT-SPI, effect verification, element recovery, locators, multi-strategy activation** |
