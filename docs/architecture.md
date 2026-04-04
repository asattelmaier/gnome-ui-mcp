# Architecture

Overview of the server internals for contributors and integrators.

## Layers

```
MCP Client (Claude, VS Code, ...)
    |
    v
server.py          Tool registration, FIFO lock, JSON-RPC dispatch
    |
    v
tools/*            Declarative tool definitions with handlers
    |
    v
adapters/*         Typed wrappers around desktop modules (dataclasses)
    |
    v
desktop/*          Low-level AT-SPI, D-Bus, Mutter, subprocess calls
```

### server.py

Server factory using the low-level MCP SDK. Creates the `McpContext`,
registers all tools via `create_tools()`, and dispatches incoming
`tools/call` requests through a FIFO `asyncio.Lock`.

Each tool call:
1. Looks up the `ToolDefinition` by name
2. Creates a `ToolRequest` from the MCP arguments
3. Creates an empty `McpResponse`
4. Calls `tool.handler(request, response, context)`
5. Catches exceptions and calls `response.set_error()`
6. Returns `response.to_tool_result()`

### McpResponse

Mutable builder that accumulates tool output. Produces dual content:

- **Text** (`content[0].text`): human-readable summary for LLMs
- **Structured** (`structuredContent`): domain data as JSON

Domain methods: `set_matches()`, `set_trees()`, `set_screenshot()`,
`set_element_result()`, `set_result()`, `set_items()`, `attach_image()`.

Errors produce only `{content: [TextContent], isError: true}` with no
`structuredContent`.

### McpContext

Central session state created lazily on first tool call:

- AT-SPI desktop connection
- Boundary enforcement (`check_boundary`, `set_boundary`)
- Action history (`record_action`, `get_history`)
- Locator cache
- Backend info (screenshot, remote desktop)

### Tools

Each tool file defines tools declaratively with `define_tool()`:

```python
ping = define_tool(
    name="ping",
    description="Return basic health information.",
    handler=_ping,
    category=ToolCategory.SYSTEM,
    parameters={...},
    read_only=True,
)
```

Handler signature: `(request: ToolRequest, response: McpResponse, context: McpContext) -> None`

Tools are auto-discovered from modules listed in `tools/tools.py` and
sorted alphabetically. Category-based gating filters tools at
registration time.

### Adapters

Typed wrappers around `desktop/*` modules. Each adapter:

- Returns dataclasses instead of dicts
- Raises exceptions instead of returning `{"success": False}`
- Provides a clean API boundary between tool handlers and low-level code

### Formatters

Dual-output formatters with `to_string()` (for LLM text) and `to_json()`
(for structured content). Used by tool handlers to build both text and
data from the same source.

### Desktop

Low-level integration with the GNOME desktop:

- `accessibility.py`: AT-SPI tree traversal, element search
- `interaction.py`: click, activate, keyboard, settle verification
- `input.py`: Mutter Remote Desktop + AT-SPI input fallback
- `locators.py`: element relocation after stale IDs
- Other modules: D-Bus, GSettings, screenshots, OCR, etc.

## Design Principles

- **Token-Optimized**: Return summaries via `append_text()`, not raw JSON
- **Small, Deterministic Blocks**: composable tools, not magic buttons
- **Self-Healing Errors**: actionable error messages with context
- **Human-Agent Collaboration**: dual content (text + structured)
- **Progressive Complexity**: simple defaults, optional advanced params
- **Reference over Value**: return file paths for screenshots, not raw bytes
