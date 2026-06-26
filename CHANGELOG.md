# Changelog

All notable changes to this project are documented here.

## 0.5.0 - 2026-06-26

### Added

- **Snapshot-driven navigation model**:
  - `take_snapshot` — captures the active window (or a chosen `window` /
    `app_name`) as a compact, LLM-readable tree and mints a stable opaque
    `uid` (`{snapshot_id}_{index}`) for every element.
  - `click`, `fill`, `hover`, `fill_form` — interaction tools that reference
    elements by `uid` from the latest snapshot, auto-wait for the shell to
    settle, and accept `include_snapshot` to return a fresh snapshot of the
    result in one turn. `fill` dispatches by element kind (editable text vs.
    checkbox/radio/switch from a boolean value).
  - `select_window` — choose a window (from `list_windows`) as the implicit
    snapshot scope and focus it.
  - New `navigation` tool category, with per-category CLI gating via
    `--category` / `--no-category`.
- **Stale-uid rejection**: a uid resolves only against the current snapshot
  and the live element is re-validated (role + name) before use. Stale or
  drifted references now raise an actionable, self-healing error instead of
  silently acting on the wrong element.

### Notes

- The lower-level path-based tools (`find_elements`, `click_element`,
  `set_element_text`, ...) remain available as advanced building blocks.
- Intentionally out of scope (no GNOME analog): network,
  performance/tracing, audits, browser extensions, heap/memory, and
  window history/URL navigation.
