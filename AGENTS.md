# Agent guide

This repository is an MCP server and CLI for automating a GNOME Wayland
desktop through AT-SPI (discovery) and Mutter RemoteDesktop (input).

## Commands

- `./scripts/check.sh` — full verification suite (sync, lint, format, tests).
- `uv run pytest tests -q` — run all tests.
- `uv run pytest path/to/test.py -q` — run a single test file.
- `uv run ruff check src tests scripts` — lint.
- `uv run ruff format src tests scripts` — format.
- `uv run python scripts/generate_docs.py` — regenerate the tool reference
  after changing tool definitions.

## Rules for Python

- Do not use `Any`, bare `except:`, `cast(...)`, or `# type: ignore`.
- Tools are declarations (`define_tool`); handlers return `None` and mutate
  the `McpResponse`. Layering is strict and one-directional:
  `tools/ -> adapters/ -> desktop/ -> runtime/gi_env.py`.
- Desktop modules return `{"success": bool, ...}` and never raise across the
  boundary; adapters flip failures into exceptions; the dispatcher in
  `server.py` formats them.

## Navigation workflow (preferred)

Drive the desktop snapshot-first — take a snapshot, then act on uids:

1. `take_snapshot` — capture the active window (or pass `window` from
   `list_windows`, or `app_name`). Returns a compact tree where every element
   has a stable `uid` like `7_42`.
2. `click` / `fill` / `hover` / `fill_form` — reference elements by `uid`.
   Actions auto-wait for the UI to settle and report effect verification.
   Pass `include_snapshot=true` to see the result in the same turn.
3. If a uid is rejected as stale (the UI changed), call `take_snapshot`
   again and use a fresh uid. uids are only valid for the latest snapshot.

`select_window` sets the implicit snapshot scope. The lower-level path-based
tools (`find_elements`, `click_element`, `set_element_text`, ...) remain
available as advanced building blocks.

See `docs/design-principles.md` and `docs/architecture.md` for the full model.
