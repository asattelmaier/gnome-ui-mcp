# Implementation Plans

> Last updated: 2026-03-28
> All APIs verified against live GNOME 46 / Mutter 46.2 / Ubuntu 24.04

Each plan follows TDD: write failing tests first, then implement until tests pass.

---

## G2: Key Hold (key_down / key_up)

**Verified API:**
- Mutter RemoteDesktop: `NotifyKeyboardKeysym(u keysym, b state)` — `state=True` for press, `state=False` for release. No auto-release, no forced pairing. Session teardown auto-releases all held keys.
- AT-SPI fallback: `Atspi.KeySynthType.PRESS` (value 0), `Atspi.KeySynthType.RELEASE` (value 1) — separate enum values exist.

**Tool interface:**
```python
@mcp.tool(description="Press and hold a key without releasing it.")
def key_down(key_name: str) -> CallToolResult: ...

@mcp.tool(description="Release a previously held key.")
def key_up(key_name: str) -> CallToolResult: ...
```

**Implementation (input.py):**
- `key_down(key_name)`: Call `_REMOTE_INPUT._ensure_session()`, then `NotifyKeyboardKeysym(keyval, True)`. Track held keys in a `set()` on `_MutterRemoteDesktopInput`.
- `key_up(key_name)`: Call `NotifyKeyboardKeysym(keyval, False)`. Remove from held set.
- AT-SPI fallback: `Atspi.generate_keyboard_event(keyval, key_name, Atspi.KeySynthType.PRESS)` / `.RELEASE`
- Add `release_all_keys()` method, called on session close.

**TDD tests (tests/test_key_hold.py):**
1. `test_key_down_returns_success` — mock RemoteDesktop, verify `NotifyKeyboardKeysym` called with `(keyval, True)`
2. `test_key_up_returns_success` — verify called with `(keyval, False)`
3. `test_key_down_tracks_held_keys` — after key_down, key is in held set
4. `test_key_up_removes_from_held` — after key_up, key removed from held set
5. `test_key_up_unknown_key_returns_error` — key_up for unheld key returns error
6. `test_invalid_key_name_returns_error` — bad key name raises ValueError
7. `test_atspi_fallback_uses_press_type` — when RemoteDesktop fails, verify `KeySynthType.PRESS` used

**Dependencies:** None — uses existing RemoteDesktop session.

---

## G3: Mouse Button Hold (button_down / button_up)

**Verified API:**
- Mutter RemoteDesktop: `NotifyPointerButton(i button, b state)` — `state=True` press, `state=False` release. Same pattern as key hold.
- `NotifyPointerMotionAbsolute(s stream, d x, d y)` — for moving while button held (drag).
- AT-SPI fallback: `Atspi.generate_mouse_event(x, y, "b1p")` for press, `"b1r"` for release. Buttons 1-5 supported, actions: `p`=press, `r`=release, `c`=click, `d`=double-click.

**Tool interface:**
```python
@mcp.tool(description="Press and hold a mouse button at coordinates without releasing.")
def mouse_button_down(x: int, y: int, button: Literal["left", "middle", "right"] = "left") -> CallToolResult: ...

@mcp.tool(description="Release a previously held mouse button at coordinates.")
def mouse_button_up(x: int, y: int, button: Literal["left", "middle", "right"] = "left") -> CallToolResult: ...
```

**Implementation (input.py):**
- `mouse_button_down(x, y, button)`: Move to (x,y) via `NotifyPointerMotionAbsolute`, then `NotifyPointerButton(code, True)`. Track held buttons.
- `mouse_button_up(x, y, button)`: Move to (x,y), then `NotifyPointerButton(code, False)`. Remove from held set.
- AT-SPI fallback: `"b1p"` / `"b1r"` etc.
- Button codes already defined: `REMOTE_POINTER_BUTTONS = {"left": 0x110, "right": 0x111, "middle": 0x112}`

**TDD tests (tests/test_mouse_hold.py):**
1. `test_button_down_calls_motion_then_press` — verify motion absolute called before button press
2. `test_button_down_returns_success` — verify `NotifyPointerButton` called with `(0x110, True)` for left
3. `test_button_up_calls_release` — verify called with `(0x110, False)`
4. `test_button_up_includes_motion` — cursor moves to release position
5. `test_right_button_uses_correct_code` — `0x111` for right
6. `test_invalid_button_returns_error` — unknown button name errors
7. `test_atspi_fallback_uses_b1p_b1r` — verify press/release event strings

**Dependencies:** None — uses existing RemoteDesktop session.

---

## G4: Unicode Text Input

**Verified API:**
- `Gdk.unicode_to_keyval(ord(char))` covers ALL Unicode (CJK, emoji) — returns `0x01000000 + codepoint`.
- BUT `NotifyKeyboardKeysym` **silently drops** keysyms not in the current XKB keymap. CJK/emoji have no keycodes on US layouts.
- `Atspi.KeySynthType.STRING` handles Unicode but only works for **XWayland apps**, not native Wayland.
- `wtype` does NOT work on GNOME (requires `zwp_virtual_keyboard_v1` which Mutter doesn't expose).
- **Clipboard approach WORKS**: `wl-copy` + Ctrl+V reliably types CJK/emoji into native Wayland apps. Verified.
- Mutter RemoteDesktop also has `EnableClipboard`, `SetSelection`, `SelectionWrite` methods (D-Bus clipboard without external tools).

**Tool interface:**
```python
@mcp.tool(description="Type arbitrary Unicode text (CJK, emoji, special characters) into the focused element via clipboard.")
def type_unicode(text: str) -> CallToolResult: ...
```

**Implementation (input.py):**
1. Save current clipboard: `subprocess.run(["wl-paste", "--no-newline"], capture_output=True)`
2. Set clipboard to desired text: `subprocess.run(["wl-copy", "--"], input=text.encode(), ...)`
3. Send Ctrl+V via RemoteDesktop: `NotifyKeyboardKeysym(Control_L, True)`, `NotifyKeyboardKeysym(v, True)`, release both
4. Sleep 50ms for paste to complete
5. Restore original clipboard: `subprocess.run(["wl-copy", "--"], input=original, ...)`

**Optimization:** For ASCII/Latin text in keymap, detect and use direct keyval injection (faster). Only fall back to clipboard for characters outside keymap.

**TDD tests (tests/test_unicode_input.py):**
1. `test_ascii_uses_direct_keyval` — ASCII text uses `NotifyKeyboardKeysym` directly, not clipboard
2. `test_cjk_uses_clipboard_approach` — Chinese text triggers clipboard path
3. `test_emoji_uses_clipboard_approach` — emoji triggers clipboard path
4. `test_clipboard_saved_and_restored` — original clipboard content preserved
5. `test_clipboard_restore_on_error` — even if paste fails, clipboard is restored
6. `test_empty_string_returns_immediately` — no-op for empty text
7. `test_mixed_ascii_cjk_uses_clipboard` — any non-keymap char triggers clipboard for whole string
8. `test_wl_copy_not_found_returns_error` — graceful error if wl-clipboard not installed

**Dependencies:** `wl-clipboard` (wl-copy, wl-paste) — already installed on this system.

---

## G6: Generic D-Bus Call

**Verified API:**
- Pattern already used in codebase: `Gio.DBusProxy.new_for_bus_sync()` + `proxy.call_sync(method, GLib.Variant(...))`
- Alternative: `Gio.bus_get_sync()` + `bus.call_sync(bus_name, path, iface, method, params, ...)`

**Tool interface:**
```python
@mcp.tool(description="Call any D-Bus method on the session bus. Returns the unpacked result.")
def dbus_call(
    bus_name: str,
    object_path: str,
    interface: str,
    method: str,
    signature: str | None = None,
    args: list | None = None,
    timeout_ms: int = 5000,
) -> CallToolResult: ...
```

**Implementation (input.py or new dbus.py):**
1. Get session bus: `Gio.bus_get_sync(Gio.BusType.SESSION, None)`
2. Build params: `GLib.Variant(signature, tuple(args))` if signature provided, else `None`
3. Call: `bus.call_sync(bus_name, object_path, interface, method, params, None, Gio.DBusCallFlags.NONE, timeout_ms, None)`
4. Unpack result: `result.unpack()` and serialize to JSON-safe dict
5. Security: validate bus_name/object_path format, reject system bus by default

**GLib.Variant serialization challenge:** The args from MCP come as JSON. Need to convert JSON types to GLib.Variant based on the D-Bus signature string. Map: `s`->str, `i`->int, `u`->uint, `b`->bool, `d`->double, `as`->list[str], `a{sv}`->dict.

**TDD tests (tests/test_dbus_call.py):**
1. `test_call_with_no_args` — e.g., `GetServerInformation` on Notifications
2. `test_call_with_string_arg` — pass a string argument
3. `test_call_with_dict_arg` — pass `a{sv}` variant dict
4. `test_result_unpacked_to_json` — GLib.Variant result converted to JSON-serializable types
5. `test_invalid_bus_name_returns_error` — bad bus name handled
6. `test_timeout_returns_error` — timeout produces clean error
7. `test_invalid_signature_returns_error` — bad D-Bus signature handled
8. `test_nested_variant_serialized` — `a{sv}` with nested variants serialized correctly

**Dependencies:** None — uses existing Gio/GLib.

---

## G1: Touch Input (tap / swipe / pinch / multi-swipe)

**Verified API:**
- Mutter RemoteDesktop D-Bus has full touch support:
  - `NotifyTouchDown(s stream, u slot, d x, d y)` — start touch at coordinates
  - `NotifyTouchMotion(s stream, u slot, d x, d y)` — move existing touch
  - `NotifyTouchUp(u slot)` — lift touch
- Requires active ScreenCast session + stream path (already created by `_ensure_session()` in input.py)
- `SupportedDeviceTypes` property reports `7` (keyboard=1 + pointer=2 + touchscreen=4)
- Slots: 0-based index, max `CLUTTER_VIRTUAL_INPUT_DEVICE_MAX_TOUCH_SLOTS` (system-defined)
- AT-SPI has NO touch event generation — no fallback available
- kwin-mcp uses EIS/libei for touch (same underlying mechanism, different API surface)

**Tool interfaces:**
```python
@mcp.tool(description="Single-finger tap at screen coordinates.")
def touch_tap(x: int, y: int, hold_ms: int = 0) -> CallToolResult: ...

@mcp.tool(description="Single-finger swipe from start to end coordinates.")
def touch_swipe(start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 300) -> CallToolResult: ...

@mcp.tool(description="Two-finger pinch gesture (zoom in/out) around a center point.")
def touch_pinch(center_x: int, center_y: int, start_distance: int, end_distance: int, duration_ms: int = 400) -> CallToolResult: ...

@mcp.tool(description="Multi-finger swipe (2-5 fingers) for system gestures.")
def touch_multi_swipe(
    start_x: int, start_y: int, end_x: int, end_y: int,
    fingers: int = 3, duration_ms: int = 300,
) -> CallToolResult: ...
```

**Implementation (input.py):**
- Add touch methods to `_MutterRemoteDesktopInput`:
  - `touch_tap(x, y, hold_ms)`: `NotifyTouchDown(stream, 0, x, y)` → sleep → `NotifyTouchUp(0)`
  - `touch_swipe(sx, sy, ex, ey, duration)`: TouchDown → interpolate N motion steps → TouchUp
  - `touch_pinch(cx, cy, sd, ed, duration)`: Two slots (0,1), start at `(cx±sd, cy)`, move to `(cx±ed, cy)` with interpolation
  - `touch_multi_swipe(sx, sy, ex, ey, fingers, duration)`: N slots, all move in parallel with interpolation
- Coordinate conversion: use `stage_area.local_coordinates(x, y)` — same as pointer
- Interpolation: `steps = max(10, duration_ms // 16)` — ~60fps equivalent

**TDD tests (tests/test_touch.py):**
1. `test_touch_tap_calls_down_then_up` — verify NotifyTouchDown then NotifyTouchUp called
2. `test_touch_tap_uses_slot_zero` — slot=0 for single finger
3. `test_touch_tap_hold_delays_release` — hold_ms > 0 delays TouchUp
4. `test_touch_swipe_interpolates_motion` — multiple TouchMotion calls between down and up
5. `test_touch_swipe_endpoints_correct` — first motion near start, last near end
6. `test_touch_pinch_uses_two_slots` — slots 0 and 1
7. `test_touch_pinch_moves_apart_for_zoom_in` — start_distance < end_distance
8. `test_touch_multi_swipe_uses_n_slots` — fingers=3 uses slots 0,1,2
9. `test_touch_multi_swipe_rejects_invalid_fingers` — fingers < 1 or > 5 returns error
10. `test_touch_requires_active_session` — _ensure_session called before touch events
11. `test_touch_uses_local_coordinates` — coordinates converted via stage_area

**Dependencies:** None — uses existing RemoteDesktop session and ScreenCast stream.

---

## G5: Screenshot Burst After Action

**Verified performance:** Shell.Screenshot D-Bus takes ~88-120ms per call (cold: 121ms, warm: 88ms). 5 screenshots = ~483ms total.

**Design decision:** Add `screenshot_after_ms` parameter to action tools (click_element, activate_element, press_key, click_at). This captures frames at specified delays after the action completes.

**Tool interface change (server.py):**
```python
# Add optional param to existing tools:
def click_element(
    element_id: str,
    action_name: str | None = None,
    screenshot_after_ms: list[int] | None = None,  # e.g. [0, 100, 500]
) -> CallToolResult: ...
```

**Implementation (interaction.py):**
- After action execution, if `screenshot_after_ms` is provided:
  - For each delay in sorted list: `time.sleep(delay_ms / 1000)`, then `input.screenshot()`
  - Collect paths into `result["screenshots"]` list
- Screenshots are named with timestamp for ordering

**TDD tests (tests/test_screenshot_burst.py):**
1. `test_no_screenshots_by_default` — without param, no extra screenshots taken
2. `test_single_screenshot_at_zero` — `[0]` captures immediately after action
3. `test_multiple_screenshots_in_order` — `[0, 100, 500]` produces 3 paths in order
4. `test_screenshot_paths_included_in_result` — result has `"screenshots"` key with paths
5. `test_delays_are_cumulative` — verifies sleep calls between captures

**Dependencies:** None.

---

## G7: App Log Capture

**Verified approach:**
- `Gio.DesktopAppInfo.launch()` returns bool only — no process handle.
- Must use `subprocess.Popen` with stdout/stderr pipes for log capture.
- Parse .desktop file via `Gio.DesktopAppInfo` for metadata, then launch via Popen.
- kwin-mcp logs to files and reads via `read_app_log(pid, last_n_lines)`.

**Tool interface:**
```python
@mcp.tool(description="Read stdout/stderr of a launched application by PID.")
def read_app_log(pid: int, last_n_lines: int = 50) -> CallToolResult: ...
```

**Implementation changes:**
- Modify `launch_app` (feat/launch-app branch) to use `subprocess.Popen` instead of `Gio.DesktopAppInfo.launch()`
- Log stdout/stderr to files in `~/.cache/gnome-ui-mcp/app-logs/{pid}-stdout.log` / `{pid}-stderr.log`
- `read_app_log(pid)`: Read last N lines from log files
- Track launched processes in a dict: `{pid: {"command": ..., "stdout_path": ..., "stderr_path": ...}}`

**TDD tests (tests/test_app_log.py):**
1. `test_launch_app_creates_log_files` — launching creates stdout/stderr log files
2. `test_read_app_log_returns_output` — read_app_log returns content from log files
3. `test_read_app_log_last_n_lines` — last_n_lines=5 returns only last 5 lines
4. `test_read_app_log_unknown_pid_returns_error` — unknown PID handled
5. `test_read_app_log_zero_lines_returns_all` — last_n_lines=0 returns everything
6. `test_log_files_in_cache_dir` — files created under ~/.cache/gnome-ui-mcp/app-logs/

**Dependencies:** Changes to feat/launch-app branch.

---

## G9: Wayland Protocol Introspection

**Tool interface:**
```python
@mcp.tool(description="List Wayland protocols available in the session.")
def wayland_info(filter_protocol: str | None = None) -> CallToolResult: ...
```

**Implementation:** Shell out to `wayland-info` (if installed) or parse `$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY` socket info. Filter by protocol name substring.

**TDD tests (tests/test_wayland_info.py):**
1. `test_returns_protocol_list` — returns list of protocol dicts
2. `test_filter_by_name` — filtering narrows results
3. `test_wayland_info_not_installed` — graceful error if binary missing

**Dependencies:** `wayland-info` binary (optional).

---

## N1: OCR + AT-SPI Hybrid

**Verified API:**
- `pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)` — returns word-level bounding boxes with `{left, top, width, height, conf, text}` per word.
- Performance: 1.2s for full 2560x1440 (preprocessed), 0.55s for cropped region.
- Dark theme preprocessing: grayscale → check avg brightness → invert if dark → sharpen. Halves OCR time.
- PIL.Image.open(path) loads our D-Bus screenshot PNGs directly.
- `conf < 30` should be filtered as noise (per hyprland-mcp).

**Tool interfaces:**
```python
@mcp.tool(description="Extract text from the screen or a region using OCR. Use for apps with poor accessibility support.")
def ocr_screen(
    x: int | None = None, y: int | None = None,
    width: int | None = None, height: int | None = None,
) -> CallToolResult: ...
# Returns: {"text": "...", "words": [{"text": "word", "x": 10, "y": 20, "width": 50, "height": 12, "confidence": 95}]}

@mcp.tool(description="Find text on screen via OCR and return its coordinates.")
def find_text_ocr(target: str, region_x: int | None = None, region_y: int | None = None, region_width: int | None = None, region_height: int | None = None) -> CallToolResult: ...
# Returns: {"matches": [{"text": "...", "x": ..., "y": ..., "center_x": ..., "center_y": ...}]}

@mcp.tool(description="Find text on screen via OCR and click it.")
def click_text_ocr(target: str, button: str = "left") -> CallToolResult: ...
```

**Implementation (new file: desktop/ocr.py):**
1. Take screenshot (full or region via `screenshot_area`)
2. Load with PIL, preprocess: grayscale → brightness check → invert if dark → sharpen
3. Run `pytesseract.image_to_data(img, output_type=Output.DICT)`
4. Filter `conf >= 30`, build word list with absolute screen coordinates
5. For `find_text_ocr`: match target string across consecutive words on same line (multi-word matching like hyprland-mcp)
6. For `click_text_ocr`: find text → click center of bounding box

**TDD tests (tests/test_ocr.py):**
1. `test_preprocess_inverts_dark_image` — dark avg brightness triggers inversion
2. `test_preprocess_keeps_light_image` — light image not inverted
3. `test_filter_low_confidence` — words with conf < 30 excluded
4. `test_word_coordinates_absolute` — coordinates are screen-absolute (not image-relative)
5. `test_find_text_single_word` — finds exact single word match
6. `test_find_text_multi_word_phrase` — merges consecutive word boxes
7. `test_find_text_case_insensitive` — matching is case-insensitive
8. `test_find_text_no_match_returns_empty` — no matches returns empty list
9. `test_click_text_takes_screenshot_and_clicks` — integrated flow
10. `test_region_crop_reduces_ocr_area` — region params crop before OCR

**Dependencies:** `pytesseract`, `tesseract-ocr` (apt), `Pillow`. All installed.

---

## N2: Desktop Notification Monitoring

**Verified API:**
- `org.freedesktop.Notifications` on session bus, path `/org/freedesktop/Notifications`
- Signals: `NotificationClosed(u id, u reason)`, `ActionInvoked(u id, s action_key)`
- Monitoring incoming `Notify` calls: use D-Bus eavesdrop + message filter — **verified working**
- `Notify` signature: `(susssasa{sv}i)` — app_name, replaces_id, icon, summary, body, actions, hints, timeout
- `Gio.DBusConnection.signal_subscribe()` for signals
- `bus.call_sync("AddMatch", eavesdrop=true, ...)` + `bus.add_filter()` for method calls

**Tool interfaces:**
```python
@mcp.tool(description="Start monitoring desktop notifications. Returns a monitor ID.")
def notification_monitor_start() -> CallToolResult: ...

@mcp.tool(description="Read captured notifications since monitoring started.")
def notification_monitor_read(clear: bool = True) -> CallToolResult: ...
# Returns: {"notifications": [{"app_name": "...", "summary": "...", "body": "...", "timestamp": "...", "id": 123}]}

@mcp.tool(description="Stop monitoring desktop notifications.")
def notification_monitor_stop() -> CallToolResult: ...
```

**Implementation (new file: desktop/notifications.py):**
1. `start()`: Subscribe to D-Bus eavesdrop on `Notify` method calls + signal_subscribe for `NotificationClosed`
2. Filter callback: parse `Notify` params `(app_name, replaces_id, icon, summary, body, actions, hints, timeout)`, store in thread-safe deque
3. `read(clear)`: Return accumulated notifications, optionally clear buffer
4. `stop()`: Unsubscribe filter and signal
5. Need GLib MainLoop for signal delivery — run in background thread

**TDD tests (tests/test_notifications.py):**
1. `test_start_subscribes_to_dbus` — signal_subscribe called with correct interface
2. `test_read_returns_captured_notifications` — after simulating Notify, read returns it
3. `test_read_clear_empties_buffer` — clear=True empties, clear=False keeps
4. `test_stop_unsubscribes` — filter and signal removed
5. `test_notification_fields_parsed` — app_name, summary, body extracted correctly
6. `test_multiple_notifications_ordered` — FIFO order
7. `test_monitor_not_started_returns_error` — read without start errors

**Dependencies:** None — uses existing Gio/GLib. Requires GLib MainLoop for signal delivery.

---

## N3: Workspace Management

**Verified API:**
- `org.gnome.Shell.Eval` is **BLOCKED on GNOME 46** — returns `(false, '')` for all expressions.
- Available read-only: `org.gnome.Shell.Introspect.GetWindows()` — includes workspace index per window.
- Available: `org.gnome.Shell.OverviewActive` property (r/w) — toggle Activities overview.
- Available: `org.gnome.Shell.FocusSearch()`, `ShowApplications()`, `FocusApp(s id)`.
- **Recommended approach:** Keyboard shortcuts via existing `press_key` / `key_combo`:
  - `Ctrl+Alt+Up/Down` — switch workspace
  - `Ctrl+Shift+Alt+Up/Down` — move window to workspace
  - `Super+Home` — go to workspace 1
- GSettings: `org.gnome.desktop.wm.preferences.num-workspaces`, `org.gnome.mutter.dynamic-workspaces`

**Tool interfaces:**
```python
@mcp.tool(description="Switch to a workspace by direction or number.")
def switch_workspace(direction: Literal["up", "down"] | None = None, number: int | None = None) -> CallToolResult: ...

@mcp.tool(description="Move the focused window to another workspace.")
def move_window_to_workspace(direction: Literal["up", "down"]) -> CallToolResult: ...

@mcp.tool(description="List workspaces and their windows.")
def list_workspaces() -> CallToolResult: ...

@mcp.tool(description="Toggle the GNOME Activities overview.")
def toggle_overview(active: bool | None = None) -> CallToolResult: ...
```

**Implementation (new file: desktop/workspaces.py):**
- `switch_workspace(direction)`: Send `Ctrl+Alt+Up` or `Ctrl+Alt+Down` via `input.press_key` with modifier combo
- `switch_workspace(number=N)`: Send `Super+Home` then N-1 `Ctrl+Alt+Down` presses (or use D-Bus if available)
- `move_window_to_workspace`: Send `Ctrl+Shift+Alt+Up/Down`
- `list_workspaces()`: Call `Shell.Introspect.GetWindows()`, group by workspace index
- `toggle_overview(active)`: Set `org.gnome.Shell.OverviewActive` property via D-Bus

**TDD tests (tests/test_workspaces.py):**
1. `test_switch_workspace_down_sends_ctrl_alt_down` — verify correct key combo sent
2. `test_switch_workspace_up_sends_ctrl_alt_up` — verify correct key combo sent
3. `test_move_window_sends_ctrl_shift_alt` — verify modifier combo
4. `test_list_workspaces_groups_by_index` — windows grouped by workspace
5. `test_toggle_overview_sets_property` — D-Bus Properties.Set called
6. `test_list_workspaces_introspect_called` — Shell.Introspect.GetWindows invoked

**Dependencies:** None — uses existing key combo infrastructure + D-Bus.

---

## N4: Monitor/Display Info

**Verified API:**
- `org.gnome.Mutter.DisplayConfig.GetCurrentState()` — returns full monitor details:
  - Connector, manufacturer, model, serial, display-name
  - Current mode (resolution, refresh rate), available modes, available scales
  - Logical monitor position, scale, is-primary, transform
- GDK already used in codebase: `Gdk.Display.get_default()`, `display.get_n_monitors()`, `monitor.get_geometry()`
- Additional GDK properties: `get_scale_factor()`, `get_model()`, `get_manufacturer()`, `get_refresh_rate()` (millihertz), `get_width_mm()`, `get_height_mm()`
- `MonitorsChanged` D-Bus signal for live updates

**Tool interface:**
```python
@mcp.tool(description="List all connected monitors with resolution, position, scale, and hardware info.")
def list_monitors() -> CallToolResult: ...
# Returns: {"monitors": [{"connector": "HDMI-2", "manufacturer": "ACR", "model": "SB322QU A",
#   "display_name": "Acer Technologies 32\"", "resolution": "2560x1440", "refresh_rate_hz": 60.0,
#   "scale": 1.0, "position": {"x": 0, "y": 0}, "is_primary": true, "physical_size_mm": {"w": 697, "h": 392}}]}
```

**Implementation (new file: desktop/display.py):**
- Primary: Call `Mutter.DisplayConfig.GetCurrentState()`, parse the complex variant tuple
- Fallback: Use GDK `Gdk.Display.get_default()` for basic geometry
- Merge both sources for complete info

**TDD tests (tests/test_display.py):**
1. `test_returns_monitor_list` — at least one monitor returned
2. `test_monitor_has_required_fields` — connector, resolution, scale, position present
3. `test_resolution_format` — "WxH" string format
4. `test_refresh_rate_in_hz` — float, reasonable range (30-240)
5. `test_position_has_x_y` — position dict with x and y
6. `test_gdk_fallback_when_dbus_fails` — GDK used if Mutter.DisplayConfig unavailable
7. `test_physical_size_reasonable` — mm values make sense for a real monitor

**Dependencies:** None.

---

## N5: Screen Recording / GIF Capture

**Verified API:**
- `org.gnome.Shell.Screencast` D-Bus interface — **verified working on this system**:
  - `Screencast(s file_template, a{sv} options) -> (b success, s filename_used)` — full screen
  - `ScreencastArea(i x, i y, i w, i h, s file_template, a{sv} options) -> (b success, s filename_used)` — region
  - `StopScreencast() -> (b success)`
  - Options: `framerate` (uint32, default 30), `draw-cursor` (bool), `pipeline` (custom GStreamer)
- Output format: MP4 (H.264 via OpenH264) by default
- **CRITICAL**: Same D-Bus connection must be used for start and stop (session tracked by sender name)
- MP4 to GIF: `ffmpeg -i input.mp4 -vf "fps=10,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -loop 0 output.gif`
- Verified: 4s recording → 520KB MP4 → 179KB GIF

**Tool interfaces:**
```python
@mcp.tool(description="Start recording the screen or a region to video.")
def screen_record_start(
    x: int | None = None, y: int | None = None,
    width: int | None = None, height: int | None = None,
    framerate: int = 30,
    draw_cursor: bool = True,
) -> CallToolResult: ...
# Returns: {"recording": true, "path": "/path/to/recording.mp4"}

@mcp.tool(description="Stop recording and optionally convert to GIF.")
def screen_record_stop(to_gif: bool = False, gif_fps: int = 10, gif_width: int = 640) -> CallToolResult: ...
# Returns: {"path": "recording.mp4", "gif_path": "recording.gif" (if to_gif)}
```

**Implementation (new file: desktop/screencast.py):**
- Use a persistent `Gio.bus_get_sync()` connection stored as module-level singleton (same connection for start/stop)
- `start()`: Call `Screencast` or `ScreencastArea`, store filename
- `stop()`: Call `StopScreencast`, optionally convert to GIF via `subprocess.run(["ffmpeg", ...])`
- Cache dir: `~/.cache/gnome-ui-mcp/recordings/`

**TDD tests (tests/test_screencast.py):**
1. `test_start_calls_screencast_dbus` — Screencast method called with correct params
2. `test_start_area_calls_screencast_area` — ScreencastArea when region specified
3. `test_stop_calls_stop_screencast` — StopScreencast called
4. `test_stop_returns_path` — result includes file path
5. `test_same_connection_used` — start and stop use same D-Bus connection
6. `test_gif_conversion_runs_ffmpeg` — when to_gif=True, ffmpeg subprocess called
7. `test_gif_path_returned` — gif_path in result when converted
8. `test_stop_without_start_returns_error` — graceful error

**Dependencies:** `ffmpeg` (apt) — already installed. For GIF conversion only.

---

## N6: dconf/GSettings Read/Write

**Verified API:**
```python
from gi.repository import Gio, GLib
s = Gio.Settings(schema_id='org.gnome.desktop.interface')
s.get_string('color-scheme')  # 'prefer-dark'
s.set_string('color-scheme', 'default')
Gio.Settings.sync()
```
- All standard GSettings schemas available (interface, wm, mutter, background, sound, etc.)
- Schema listing: `Gio.SettingsSchemaSource.get_default().lookup(schema_id, True).list_keys()`

**Tool interfaces:**
```python
@mcp.tool(description="Read a GNOME setting value.")
def gsettings_get(schema: str, key: str) -> CallToolResult: ...

@mcp.tool(description="Write a GNOME setting value.")
def gsettings_set(schema: str, key: str, value: str | int | float | bool) -> CallToolResult: ...

@mcp.tool(description="List all keys in a GSettings schema.")
def gsettings_list_keys(schema: str) -> CallToolResult: ...

@mcp.tool(description="Reset a GNOME setting to its default value.")
def gsettings_reset(schema: str, key: str) -> CallToolResult: ...
```

**TDD tests (tests/test_gsettings.py):**
1. `test_get_returns_value` — read a known schema/key
2. `test_get_invalid_schema_returns_error` — bad schema handled
3. `test_get_invalid_key_returns_error` — bad key handled
4. `test_set_and_get_roundtrip` — write then read back
5. `test_list_keys_returns_list` — list of strings returned
6. `test_reset_restores_default` — value reverts to schema default

**Dependencies:** None — uses existing Gio.

---

## N7: Color/Pixel Sampling

**Verified performance:** `PIL.Image.getpixel((x,y))` is 0.5μs after image load. Screenshot is the bottleneck (~88ms).

**Tool interface:**
```python
@mcp.tool(description="Get the pixel color at screen coordinates. Takes a screenshot first.")
def get_pixel_color(x: int, y: int) -> CallToolResult: ...
# Returns: {"r": 255, "g": 128, "b": 0, "a": 255, "hex": "#FF8000"}

@mcp.tool(description="Get the average color of a screen region.")
def get_region_color(x: int, y: int, width: int, height: int) -> CallToolResult: ...
```

**TDD tests (tests/test_pixel_color.py):**
1. `test_returns_rgba_values` — r, g, b, a keys present
2. `test_returns_hex_string` — hex starts with #, 6 chars
3. `test_coordinates_out_of_bounds_returns_error` — negative or too large coords
4. `test_region_returns_average` — average of multiple pixels
5. `test_takes_screenshot_first` — screenshot function called

**Dependencies:** `Pillow` (already installed).

---

## N8: Visual Diff

**Verified API:**
- `PIL.ImageChops.difference(img1, img2).getbbox()` — 7.8ms for 1920x1080
- `scipy.ndimage.label(binary)` — 101ms for individual changed regions with connected components
- Both Pillow and scipy already installed

**Tool interface:**
```python
@mcp.tool(description="Compare two screenshots and return changed regions.")
def visual_diff(
    image_path_1: str,
    image_path_2: str,
    threshold: int = 30,
) -> CallToolResult: ...
# Returns: {"changed": true, "changed_percent": 5.2, "regions": [{"x": 10, "y": 20, "width": 100, "height": 50}]}
```

**TDD tests (tests/test_visual_diff.py):**
1. `test_identical_images_no_change` — changed=false, 0 regions
2. `test_different_images_detected` — changed=true, regions returned
3. `test_threshold_filters_noise` — small differences below threshold ignored
4. `test_changed_percent_reasonable` — between 0 and 100
5. `test_regions_have_bbox_format` — x, y, width, height keys
6. `test_invalid_path_returns_error` — bad file path handled

**Dependencies:** `Pillow`, `scipy` (both installed). `numpy` (installed).

---

## G8: Session Isolation (Nested Mutter) — DEFERRED

**Assessment:** GNOME does not have a `kwin_wayland --virtual` equivalent. Running a nested Mutter compositor is theoretically possible but undocumented, fragile, and not a standard workflow. This would require:
- `mutter --nested` (exists but primarily for debugging)
- Private D-Bus session (`dbus-run-session`)
- AT-SPI in nested session
- Significant testing overhead

**Recommendation:** Defer until GNOME provides better nested compositor support or until there's a clear user need. Mark as **DEFERRED** in roadmap.

---

## F1: Close Window

**Verified API:**
- AT-SPI window frames do NOT reliably expose a "close" action. The close button is a child widget, not an action on the frame.
- `Alt+F4` is the default GNOME keybinding for `close` (from `org.gnome.desktop.wm.keybindings`).
- `org.gnome.Shell.Introspect` is read-only — NO mutation methods.
- `wmctrl` does NOT work on Wayland.
- Optional: `window-calls` extension provides `Close(winid)` via `org.gnome.Shell.Extensions.Windows`.

**Tool interface:**
```python
@mcp.tool(description="Close the focused window.")
def close_window() -> CallToolResult: ...
```

**Implementation (desktop/window_management.py):**
- Primary: `key_combo("alt+F4")` via existing infrastructure
- Return effect verification result from `_verified_result_after_settle`

**TDD tests (tests/test_window_mgmt.py):**
1. `test_close_sends_alt_f4` — verify key_combo called with "alt+F4"
2. `test_close_returns_success` — result has success=True
3. `test_close_includes_verification` — effect verification present

**Dependencies:** None — uses existing key_combo.

---

## F2: Move/Resize Window

**Verified API:**
- `Atspi.Component.set_position()` / `set_size()` — do NOT work on Wayland (compositor controls geometry).
- Native D-Bus: NO mutation methods on `org.gnome.Shell.Introspect`.
- `org.gnome.Shell.Eval` — BLOCKED on GNOME 46.
- Keyboard shortcuts:
  - `Alt+F7` — begin keyboard move mode (arrow keys to move, Enter to confirm)
  - `Alt+F8` — begin keyboard resize mode (arrow keys to resize, Enter to confirm)
  - `Super+Up` — maximize
  - `Super+Down` — unmaximize/restore
  - `Super+Left/Right` — tile left/right half
- Optional: `window-calls` extension provides `Move(winid, x, y)`, `Resize(winid, w, h)`, `MoveResize(winid, x, y, w, h)`.

**Tool interfaces:**
```python
@mcp.tool(description="Move the focused window by pixel offset using keyboard move mode.")
def move_window(dx: int, dy: int) -> CallToolResult: ...

@mcp.tool(description="Resize the focused window by pixel offset using keyboard resize mode.")
def resize_window(dw: int, dh: int) -> CallToolResult: ...

@mcp.tool(description="Tile or snap the focused window to a position.")
def snap_window(position: Literal["maximize", "restore", "left", "right"]) -> CallToolResult: ...
```

**Implementation (desktop/window_management.py):**
- `move_window(dx, dy)`: Send `Alt+F7`, then arrow keys proportional to dx/dy, then `Return`
  - Arrow keys move ~10px per press in GNOME's keyboard move mode
  - Steps: `abs(dx) // 10` Right/Left presses + `abs(dy) // 10` Up/Down presses
- `resize_window(dw, dh)`: Send `Alt+F8`, then arrow keys, then `Return`
- `snap_window("maximize")`: `key_combo("super+Up")`
- `snap_window("restore")`: `key_combo("super+Down")`
- `snap_window("left")`: `key_combo("super+Left")`
- `snap_window("right")`: `key_combo("super+Right")`

**TDD tests (tests/test_window_mgmt.py):**
4. `test_move_sends_alt_f7_then_arrows` — verify sequence: Alt+F7, arrow keys, Return
5. `test_move_right_uses_right_arrows` — positive dx sends Right keys
6. `test_move_left_uses_left_arrows` — negative dx sends Left keys
7. `test_resize_sends_alt_f8_then_arrows` — verify Alt+F8 sequence
8. `test_snap_maximize_sends_super_up` — verify key combo
9. `test_snap_left_sends_super_left` — verify key combo
10. `test_snap_invalid_position_returns_error` — bad position handled

**Dependencies:** None — uses existing key_combo. Approximate (keyboard move mode is ~10px per arrow press).

---

## F3: Toggle Fullscreen / Minimize

**Verified API:**
- `toggle-fullscreen` has NO default keybinding in GNOME WM. Most apps use `F11` internally.
- Keyboard shortcuts (from `org.gnome.desktop.wm.keybindings`):
  - `Alt+F10` — toggle maximized
  - `Super+h` — minimize
  - `F11` — fullscreen (app-level, works in Firefox, Nautilus, etc.)

**Tool interface:**
```python
@mcp.tool(description="Toggle the focused window's state.")
def toggle_window_state(
    state: Literal["fullscreen", "maximize", "minimize"],
) -> CallToolResult: ...
```

**Implementation (desktop/window_management.py):**
- `"fullscreen"`: `press_key("F11")` (app-level, most apps handle this)
- `"maximize"`: `key_combo("alt+F10")` (WM-level toggle)
- `"minimize"`: `key_combo("super+h")`

**TDD tests (tests/test_window_mgmt.py):**
11. `test_toggle_fullscreen_sends_f11` — verify press_key("F11")
12. `test_toggle_maximize_sends_alt_f10` — verify key_combo
13. `test_minimize_sends_super_h` — verify key_combo
14. `test_invalid_state_returns_error` — bad state handled

**Dependencies:** None.

---

## F4: OCR Type-Into by Label

**Verified approach (from hyprland-mcp source):**
- hyprland-mcp clicks the placeholder text itself (not a nearby input field) — works because clicking placeholder text inside an input focuses that field.
- We have a significant advantage: AT-SPI can find editable elements directly.

**Hybrid AT-SPI + OCR approach:**
1. AT-SPI first: Search for editable elements whose name/label contains the hint text
2. If found, use `set_element_text()` (faster, more reliable)
3. If not found, fall back to OCR: find text on screen, click it, then type

**Tool interface:**
```python
@mcp.tool(
    description=(
        "Find an input field by its label or placeholder text and type into it. "
        "Tries AT-SPI first, falls back to OCR."
    )
)
def type_into(
    label: str,
    text: str,
    submit: bool = False,
) -> CallToolResult: ...
```

**Implementation (desktop/ocr.py — extend existing):**
1. AT-SPI path: `find_elements(query=label, showing_only=True)` → filter for editable elements → `set_element_text(element_id, text)` or `focus_element` + `type_text`
2. OCR path: `find_text_ocr(label)` → click center of match → `type_text(text)`
3. If `submit=True`: `press_key("Return")` after typing

**TDD tests (tests/test_type_into.py):**
1. `test_atspi_path_finds_editable_element` — when AT-SPI finds editable match, uses set_element_text
2. `test_atspi_path_skips_non_editable` — non-editable matches are skipped
3. `test_ocr_fallback_when_atspi_fails` — when no AT-SPI match, OCR is used
4. `test_ocr_clicks_then_types` — OCR path: click match center, then type_text
5. `test_submit_sends_return` — submit=True sends Return key after typing
6. `test_no_match_returns_error` — neither AT-SPI nor OCR finds the label
7. `test_empty_label_returns_error` — empty label string handled

**Dependencies:** Existing OCR + AT-SPI infrastructure.

---

## F5: VLM/AI Vision Analysis

**Verified API options:**
- **OpenRouter** (OpenAI-compatible): `POST https://openrouter.ai/api/v1/chat/completions`
  - Free vision models: `google/gemma-3-27b-it:free`, `nvidia/nemotron-nano-12b-v2-vl:free`
  - Image format: `{"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}`
  - Env var: `OPENROUTER_API_KEY`
- **Anthropic Claude**: `POST https://api.anthropic.com/v1/messages`
  - Image format: `{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "..."}}`
  - Env var: `ANTHROPIC_API_KEY`
  - Cost: ~$0.008/screenshot at 1080p
- **Ollama local**: `POST http://localhost:11434/api/chat`
  - Image format: `"images": ["<base64>"]` on message object
  - Free, requires local GPU
- **Latency**: 3-15s depending on provider and model
- **Dependencies**: `httpx` or `requests` for HTTP calls, `base64` (stdlib)

**Tool interfaces:**
```python
@mcp.tool(description="Analyze a screenshot using a vision language model.")
def analyze_screenshot(
    prompt: str,
    provider: Literal["openrouter", "anthropic", "ollama"] = "openrouter",
    model: str | None = None,
) -> CallToolResult: ...

@mcp.tool(description="Compare two screenshots using a vision language model.")
def compare_screenshots(
    image_path_1: str,
    image_path_2: str,
    prompt: str | None = None,
    provider: Literal["openrouter", "anthropic", "ollama"] = "openrouter",
) -> CallToolResult: ...
```

**Implementation (new file: desktop/vlm.py):**
1. Take screenshot (or use provided path)
2. Read file → base64 encode
3. Build provider-specific request payload
4. HTTP POST with timeout (60s)
5. Parse response → return analysis text
6. API key from env var, with clear error if missing

**Provider abstraction:**
```python
def _build_openrouter_payload(prompt, images_b64, model): ...
def _build_anthropic_payload(prompt, images_b64, model): ...
def _build_ollama_payload(prompt, images_b64, model): ...
```

**TDD tests (tests/test_vlm.py):**
1. `test_openrouter_payload_format` — correct JSON structure with image_url
2. `test_anthropic_payload_format` — correct JSON structure with image source
3. `test_ollama_payload_format` — correct JSON structure with images array
4. `test_missing_api_key_returns_error` — no env var → clean error
5. `test_api_timeout_returns_error` — timeout handled gracefully
6. `test_base64_encoding_correct` — PNG file encodes correctly
7. `test_analyze_takes_screenshot_first` — screenshot called when no path given
8. `test_compare_sends_two_images` — both images in payload

**Dependencies:** `httpx` (add to pyproject.toml) or `requests`. `base64` (stdlib).

---

## Items NOT planned (N9-N15)

These are lower priority. Plans will be written when higher-priority items are complete:
- **N9: Conditional action chains** — design TBD
- **N10: File dialog helper** — needs GTK file chooser AT-SPI tree research
- **N11: GNOME Extensions control** — `org.gnome.Shell.Extensions` D-Bus, straightforward
- **N12: System tray interaction** — SNI protocol research needed
- **N13: Element highlight/annotate** — would need overlay window or screenshot annotation
- **N14: IME support** — IBus D-Bus won't work for injection (verified), alternative TBD
- **N15: Undo verification** — simple wrapper around Ctrl+Z + effect verification
