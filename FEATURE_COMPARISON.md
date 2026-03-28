# Linux Desktop Automation MCP Servers — Deep Feature Comparison

> Last updated: 2026-03-28

| Feature | **gnome-ui-mcp** (ours) | **kwin-mcp** | **hyprland-mcp** | **wayland-mcp** | **hyprmcp** |
|---|---|---|---|---|---|
| **Repository** | asattelmaier + mlugo-apx | isac322/kwin-mcp | alderban107/hyprland-mcp | someaka/wayland-mcp | stefanoamorelli/hyprmcp |
| **Target** | GNOME Wayland (Mutter) | KDE Plasma 6 (KWin) | Hyprland | Any Wayland | Hyprland |
| **Total tools** | **~69** | 29 | 27 | 9 | 13 |
| **Input method** | Mutter RemoteDesktop D-Bus | KWin EIS/libei | hyprctl + ydotool + wtype | evemu (raw kernel) | hyprctl only |
| | | | | | |
| **MOUSE INPUT** | | | | | |
| Click (single) | ✅ | ✅ | ✅ | ✅ | ❌ |
| Click (double/triple) | ✅ | ✅ | ⚡ double only | ❌ | ❌ |
| Move/hover | ✅ mouse_move + hover_element | ✅ | ✅ | ✅ | ❌ |
| Drag | ✅ | ✅ (waypoints) | ✅ | ✅ | ❌ |
| Scroll | ✅ | ✅ (horiz + smooth) | ✅ | ✅ | ❌ |
| Button hold (down/up) | ✅ | ✅ | ❌ | ❌ | ❌ |
| | | | | | |
| **KEYBOARD INPUT** | | | | | |
| Type text | ✅ | ✅ | ✅ | ✅ | ❌ |
| Press key | ✅ | ✅ | ✅ | ✅ | ❌ |
| Key combos | ✅ key_combo | ✅ | ✅ send_shortcut | ✅ | ❌ |
| Key hold (down/up) | ✅ | ✅ | ❌ | ❌ | ❌ |
| Unicode/CJK/emoji | ✅ type_unicode | ✅ keyboard_type_unicode | ⚡ wtype partial | ❌ | ❌ |
| | | | | | |
| **TOUCH INPUT** | | | | | |
| Tap | ✅ | ✅ | ❌ | ❌ | ❌ |
| Swipe | ✅ | ✅ | ❌ | ❌ | ❌ |
| Pinch | ✅ | ✅ | ❌ | ❌ | ❌ |
| Multi-finger | ✅ | ✅ | ❌ | ❌ | ❌ |
| | | | | | |
| **ACCESSIBILITY (AT-SPI)** | | | | | |
| AT-SPI tree | ✅ | ✅ | ❌ | ❌ | ❌ |
| Find elements (name/role) | ✅ | ✅ (+ state filter) | ❌ | ❌ | ❌ |
| Element at point | ✅ | ❌ | ❌ | ❌ | ❌ |
| Wait for element | ✅ | ✅ | ❌ | ❌ | ❌ |
| Wait for element gone | ✅ | ❌ | ❌ | ❌ | ❌ |
| Popup detection | ✅ | ❌ | ❌ | ❌ | ❌ |
| Shell settle verification | ✅ | ❌ | ❌ | ❌ | ❌ |
| Effect verification | ✅ | ❌ | ❌ | ❌ | ❌ |
| Element recovery/relocate | ✅ | ❌ | ❌ | ❌ | ❌ |
| Activate element (multi-strategy) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Focus element | ✅ | ❌ | ❌ | ❌ | ❌ |
| Set element text | ✅ | ❌ | ❌ | ❌ | ❌ |
| Select element text | ✅ | ❌ | ❌ | ❌ | ❌ |
| | | | | | |
| **SCREENSHOTS & RECORDING** | | | | | |
| Full screen | ✅ D-Bus Shell.Screenshot | ✅ KWin ScreenShot2 | ✅ grim | ✅ multi-backend | ❌ |
| Region/area | ✅ | ❌ | ✅ | ⚡ | ❌ |
| Window | ✅ | ❌ | ✅ | ❌ | ❌ |
| Burst after action | ✅ | ✅ screenshot_after_ms | ❌ | ❌ | ❌ |
| Screen recording / GIF | ✅ Shell.Screencast + ffmpeg | ❌ | ❌ | ❌ | ❌ |
| | | | | | |
| **OCR & VISION** | | | | | |
| OCR text extraction | ✅ Tesseract + dark-theme | ❌ | ✅ Tesseract + dark-theme | ❌ | ❌ |
| OCR click-by-text | ✅ click_text_ocr | ❌ | ✅ click_text | ❌ | ❌ |
| OCR type-into by label | ❌ | ❌ | ✅ type_into | ❌ | ❌ |
| VLM/AI vision analysis | ❌ | ❌ | ❌ | ✅ OpenRouter VLM | ❌ |
| | | | | | |
| **CLIPBOARD** | | | | | |
| Read | ✅ wl-paste | ✅ wl-paste | ✅ wl-paste | ❌ | ❌ |
| Write | ✅ wl-copy | ✅ wl-copy | ✅ wl-copy | ❌ | ❌ |
| | | | | | |
| **WINDOW MANAGEMENT** | | | | | |
| List windows | ✅ AT-SPI | ✅ AT-SPI | ✅ hyprctl | ❌ | ✅ hyprctl |
| Focus window | ✅ | ✅ | ✅ | ❌ | ⚡ dispatch |
| Close window | ❌ | ❌ | ✅ | ❌ | ❌ |
| Move/resize window | ❌ | ❌ | ✅ | ❌ | ⚡ dispatch |
| Toggle fullscreen/float | ❌ | ❌ | ✅ | ❌ | ⚡ dispatch |
| | | | | | |
| **WORKSPACE & MONITOR** | | | | | |
| List workspaces | ✅ Shell.Introspect | ❌ | ✅ | ❌ | ✅ |
| Switch workspace | ✅ key combos | ❌ | ✅ | ❌ | ⚡ dispatch |
| Move window to workspace | ✅ key combos | ❌ | ✅ | ❌ | ⚡ dispatch |
| Toggle overview | ✅ | ❌ | ❌ | ❌ | ❌ |
| Monitor/display info | ✅ Mutter.DisplayConfig | ❌ | ✅ hyprctl | ❌ | ✅ hyprctl |
| | | | | | |
| **APP MANAGEMENT** | | | | | |
| Launch app | ✅ + list_desktop_apps | ✅ | ✅ | ❌ | ❌ |
| App log capture | ✅ | ✅ | ❌ | ❌ | ❌ |
| List running apps | ✅ AT-SPI | ❌ | ❌ | ❌ | ❌ |
| List .desktop entries | ✅ | ❌ | ❌ | ❌ | ❌ |
| | | | | | |
| **SYSTEM INTEGRATION** | | | | | |
| Desktop notifications | ✅ monitor start/read/stop | ❌ | ❌ | ❌ | ❌ |
| D-Bus generic call | ✅ | ✅ | ❌ | ❌ | ❌ |
| GSettings read/write | ✅ get/set/list/reset | ❌ | ❌ | ❌ | ⚡ set_keyword |
| Pixel color sampling | ✅ pixel + region | ❌ | ❌ | ❌ | ❌ |
| Visual diff | ✅ scipy regions | ❌ | ❌ | ❌ | ❌ |
| Wayland protocol info | ✅ | ✅ | ❌ | ❌ | ❌ |
| | | | | | |
| **ARCHITECTURE** | | | | | |
| Session isolation | ✅ gnome-shell --headless | ✅ (D-Bus + display + input + home) | ❌ | ❌ | ❌ |
| Action chaining | ❌ | ❌ | ❌ | ✅ chain: syntax | ❌ |
| Coordinate mapping | ❌ | ❌ | ✅ formula per screenshot | ❌ | ❌ |
| Screenshot auto-resize | ❌ | ❌ | ✅ JPEG + scale | ❌ | ❌ |
| Targeted shortcuts (per-window) | ❌ | ❌ | ✅ send_shortcut(target=) | ❌ | ❌ |

---

## Feature Count Summary

| Category | gnome-ui-mcp | kwin-mcp | hyprland-mcp | wayland-mcp | hyprmcp |
|----------|:---:|:---:|:---:|:---:|:---:|
| Mouse input | 6/6 | 6/6 | 4/6 | 4/6 | 0/6 |
| Keyboard input | 5/5 | 5/5 | 3/5 | 3/5 | 0/5 |
| Touch input | 4/4 | 4/4 | 0/4 | 0/4 | 0/4 |
| Accessibility | 12/12 | 3/12 | 0/12 | 0/12 | 0/12 |
| Screenshots | 5/5 | 2/5 | 3/5 | 2/5 | 0/5 |
| OCR/Vision | 2/4 | 0/4 | 3/4 | 1/4 | 0/4 |
| Clipboard | 2/2 | 2/2 | 2/2 | 0/2 | 0/2 |
| Window mgmt | 2/5 | 2/5 | 5/5 | 0/5 | 2/5 |
| Workspace/Monitor | 5/5 | 0/5 | 4/5 | 0/5 | 3/5 |
| App mgmt | 4/4 | 2/4 | 1/4 | 0/4 | 0/4 |
| System integration | 6/6 | 2/6 | 0/6 | 0/6 | 1/6 |
| **TOTAL** | **53/58** | **28/58** | **25/58** | **10/58** | **6/58** |

## Unique Strengths

| Project | What only it has |
|---------|-----------------|
| **gnome-ui-mcp** | Deepest AT-SPI integration (12 tools), effect verification, element recovery, popup detection, notification monitoring, screen recording, GSettings, pixel color, visual diff, GNOME overview toggle. Most tools (69). |
| **kwin-mcp** | Only project with full session isolation (D-Bus + display + input + home). EIS/libei for input. Waypoint-based drag. screenshot_after_ms built into every action. |
| **hyprland-mcp** | Best OCR (auto-scope to active window, dark theme). type_into by label. Coordinate mapping in screenshots. Best window management (move, resize, fullscreen, float). Per-window shortcuts. |
| **wayland-mcp** | Only VLM/AI vision analysis (OpenRouter). Action chaining. Compositor-agnostic. |
| **hyprmcp** | Lightest weight (single file). Direct hyprctl dispatch access. Hyprland config modification. |
