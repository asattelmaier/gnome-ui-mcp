# Design Principles

Guidelines for shipping features for the MCP server.
Apply them with nuance.

- **Agent-Agnostic API**: Use the MCP standard. Don't lock in to one
  LLM provider. Interoperability is key.
- **Token-Optimized**: Return semantic summaries via `append_text()`.
  "Found 3 applications" is better than dumping a full JSON tree.
  Files are the right location for large amounts of data.
- **Small, Deterministic Blocks**: Give agents composable tools
  (`find_elements`, `click_element`, `screenshot`), not magic buttons
  that try to do everything at once.
- **Self-Healing Errors**: Return actionable errors that include
  context and potential fixes. Errors are text in `content`, not
  structured data.
- **Human-Agent Collaboration**: Output must be readable by machines
  (structured JSON in `structuredContent`) AND humans (text summaries
  in `content`).
- **Progressive Complexity**: Tools should be simple by default
  (high-level actions with sensible defaults) but offer advanced
  optional arguments for power users.
- **Reference over Value**: For heavy assets (screenshots, recordings),
  return a file path, never the raw data stream. `attach_image()` is
  the exception for inline display.
- **Exceptions over Error Dicts**: Desktop modules raise exceptions on
  failure. The central dispatcher catches them. No `{"success": False}`
  pattern.
- **Central State**: Mutable session state (boundaries, history,
  locators, the current snapshot) lives in `McpContext`, not in
  module-level globals.
- **Snapshot-Bound, Stale-Rejecting UIDs**: The blessed navigation
  surface refers to elements by an opaque `uid` (`{snapshot_id}_{index}`)
  minted by `take_snapshot`. A uid resolves only against the *current*
  snapshot, and the resolved element is re-validated (role + name) before
  use. A uid from an older snapshot, or one whose element drifted, is
  rejected with an actionable error -- never silently re-targeted. This is
  the central reliability property of the navigation model. The internal
  positional AT-SPI path is kept only as the resolution vehicle and is
  never surfaced.
- **Implicit Auto-Settle**: Navigation actions (`click`, `fill`,
  `fill_form`) wait for the shell to settle before returning and report
  effect verification, so agents do not need a separate wait call. Pass
  `include_snapshot=true` to get a fresh snapshot of the result in the
  same turn.

## Navigation model: scope choices

GNOME-specific choices in the navigation model:

- **A "page" is a top-level window.** `take_snapshot` defaults to the
  active window; `select_window` sets the implicit scope. There is no
  history/URL navigation (windows have none).
- **No uid reuse across snapshots (yet)**: each snapshot mints fresh
  uids. AT-SPI lacks a stable durable node id, so the headline
  stale-*rejection* is implemented; uid *longevity* is a future
  enhancement. Re-snapshot after a UI change.
- **Input goes through Mutter RemoteDesktop** (with an AT-SPI fallback).
  Coordinate clicks (`click_at`) remain available as an advanced fallback.
- **Out of scope** (no GNOME analog): network, performance/tracing,
  audits, browser extensions, heap/memory.
- The lower-level path-based tools (`find_elements`, `click_element`,
  `set_element_text`, ...) remain as advanced building blocks; the
  snapshot/uid tools are what most automation should use.
