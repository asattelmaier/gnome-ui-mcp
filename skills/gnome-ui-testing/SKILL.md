---
name: gnome-ui-testing
description: Uses GNOME UI MCP for desktop UI testing, assertions, and state verification. Use when writing or running UI tests, checking element states, comparing screenshots, or verifying desktop behavior.
---

## Core Concepts

**State snapshots**: `snapshot_state` captures the full desktop state (applications, windows, focus, popups). `compare_state` diffs two snapshots to detect changes. Use these to verify side effects of actions.

**Assertions**: `assert_element` and `assert_text` poll for conditions with a timeout, making them suitable for async UI that takes time to settle.

**Visual verification**: `screenshot` + `visual_diff` for pixel-level comparison. `get_pixel_color` and `get_region_color` for spot checks.

## Workflow Patterns

### Verifying an action took effect

1. `snapshot_state` before the action
2. Perform the action (click, type, etc.)
3. `snapshot_state` after the action
4. `compare_state` the two snapshots to see what changed

### Waiting for UI to settle

- `wait_for_element(query="Save completed")` waits for an element to appear
- `wait_for_element_gone(query="Loading...")` waits for an element to disappear
- `wait_for_shell_settled` waits for GNOME Shell animations to finish
- `wait_for_popup_count` waits for a specific number of popups

### Asserting element state

```
assert_element(query="Submit", role="push button", expected_states=["sensitive"])
```

This polls until the Submit button exists and is sensitive (enabled), or times out.

### Visual regression testing

1. `screenshot(filename="baseline.png")` for the reference image
2. Perform the action
3. `screenshot(filename="current.png")`
4. `visual_diff(image_path_1="baseline.png", image_path_2="current.png")`

### OCR-based verification

- `ocr_screen` extracts all visible text from the screen
- `find_text_ocr` locates specific text by position
- Useful when AT-SPI does not expose the text (e.g. rendered images)

## Best Practices

- Always use timeouts on wait/assert tools to avoid hanging
- Prefer `assert_element` over manual find + check loops
- Use `showing_only=True` to ignore hidden elements
- Take screenshots at key checkpoints for debugging failed tests
