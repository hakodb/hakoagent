# hakoagent

Use the hakoagent CLI for memory, caching, graph traversal, skills, tasks, and vigilance checks.

## Commands

- `hakoagent init --db <path> --collections all` — Initialize HakoDB database (9 collections)
- `hakoagent index` — Scan and index codebase dependencies
- `hakoagent recall <query> [--limit N]` — Retrieve context from memory (cache-first, TTL 300s)
- `hakoagent skill list|add|get` — Manage reusable skill patterns
- `hakoagent task list|create|complete` — Track tasks with targets and DoD
- `hakoagent events` — View chronological action history (append-only)
- `hakoagent vigilance` — Detect regressions, forgotten files, TODO items
- `hakoagent cache stats|get|put` — Manage context cache (TTL 300s default)
- `hakoagent graph traverse|shortest-path|dependents|dependents-reverse` — Codebase dependency graph (BFS/Dijkstra)
- `hakoagent mcp enable|disable|status` — Per-project MCP server control (OFF by default)

## Rules

1. Run `hakoagent recall <query>` before searching codebase manually
2. Run `hakoagent index` after significant code changes — **enforced automatically on `hakoagent task complete`** (quiet re-index, only if git shows uncommitted file changes). Ad-hoc edits outside a task still require manual `hakoagent index`.
3. Every action is logged to `events` (append-only) — use `hakoagent events [--limit N]`
4. Use `hakoagent skill get <skill_id> [--summary]` to retrieve skill context — `--summary` skips markdown body; full skill available without the flag
5. **MCP server is OFF by default** — `install.sh --global` no longer writes MCP config to `~/.claude.json` or `~/.config/opencode/opencode.jsonc`. To enable MCP for a specific project:
   `hakoagent mcp enable` (creates `.hakoagent/mcp-enabled`), then `hakoagent-mcp` to start the server.
   Use `hakoagent mcp disable` to turn it off, `hakoagent mcp status` to check.
6. Install with: `install.sh` (project) or `install.sh --global` (global)
