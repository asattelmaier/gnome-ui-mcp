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
  locators) lives in `McpContext`, not in module-level globals.
