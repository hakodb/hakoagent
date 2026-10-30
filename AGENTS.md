# HakoAgent — Agent Memory & Skill Engine

> **⚠️ For AI agents only.** This document instructs harness agents (OpenCode, etc.)
> on how to call `hakoagent` via the shell tool. Human users should read
> `INSTALL.md` instead.

## Architecture

**`hakoagent`** runs as an MCP server by default. It opens the hakodb embedded
database once and keeps it alive for the session. Agents connect via stdin/stdout
JSON-RPC (MCP protocol).

**`hakoagent-cli`** is the same binary but defaults to CLI mode for one-off commands.

---

## Session Lifecycle

1. **Agent starts `hakoagent`** → MCP server opens hakodb engine, stays alive
2. **Agent sends JSON-RPC over stdin** → server processes each call
3. **Agent closes stdin** → server frees engine, exits

---

## Agent Connection (stdin/stdout JSON-RPC)

Start `hakoagent` as a subprocess, send JSON-RPC messages on stdin:

```python
import subprocess, json

proc = subprocess.Popen(
    ["hakoagent"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    bufsize=1,
)

# Initialize
proc.stdin.write(json.dumps({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {"capabilities": {}}
}) + "\n")
proc.stdin.flush()

# Call a tool
proc.stdin.write(json.dumps({
    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
    "params": {"name": "recall", "arguments": {"query": "graph impact"}}
}) + "\n")
proc.stdin.flush()
resp = json.loads(proc.stdout.readline())

# End session
proc.stdin.close()
proc.wait()
```

### Available MCP Tools

| Tool | Purpose |
|------|---------|
| `save_doc` | Save document to collection |
| `load_doc` | Load document from collection |
| `recall` | Vector search across memory |
| `cache_put` / `cache_get` / `cache_stats` | Context cache |
| `events` | Append-only event history |
| `revision.list` | Immutable revision history |
| `skill.list` / `skill.add` / `skill.refine` / `skill.troubleshoot` | Skill management |
| `task.list` / `task.create` / `task.complete` | Task management |
| `sync.enable` / `sync.disable` / `sync.status` / `sync.sync_now` / `sync.backup` | Multi-agent sync |
| `graph.traverse` / `graph.shortest_path` / `graph.impact` | Code graph |
| `graph.search` / `graph.query` / `graph.detect_changes` / `graph.get_snippet` / `graph.architecture` | Graph queries |
| `graph.adr.add/list/get` | Architecture decisions |
| `graph.ingest_traces` / `graph.list_projects` / `graph.delete_project` | Trace/project management |
| `vigilance` / `bug_scan` | Code quality |
| `team.init` / `team.status` / `team.assign` / `team.context` | Multi-agent team |

### Example: Agent Recall

```python
proc.stdin.write(json.dumps({
    "jsonrpc": "2.0", "id": 2,
    "method": "tools/call",
    "params": {"name": "recall", "arguments": {"query": "null pointer", "actor": "agent-a"}}
}) + "\n")
proc.stdin.flush()
resp = json.loads(proc.stdout.readline())
```

### Graph (codebase fluency & impact analysis)
- `hakoagent graph traverse <node> <direction> <max_depth>` — BFS dependency traversal
- `hakoagent graph shortest-path <from> <to>` — Dijkstra shortest path
- `hakoagent graph dependents <node>` — Files depending on this node
- `hakoagent graph dependents-reverse <node>` — Files this node depends on
- `hakoagent graph coverage <file_path> [...]` — Index coverage report per file

### Team (multi-agent collaboration)
- `hakoagent team init --team <name> --members <a,b,c> [--remote <url>]` — Initialize team
- `hakoagent team status` — Who's online, task assignments, active skills
- `hakoagent team assign <task_id> <member>` — Assign task to member
- `hakoagent team context` — Shared context: recent activity, tasks by assignee, skills
- `hakoagent team sync` — Sync with remote (Git-based)

## Rules (guidance, not enforcement)
1. **Run `hakoagent recall <query>` before searching codebase manually** — cache hit avoids re-querying
2. **Run `hakoagent index` after significant code changes** — keeps dependency graph current.
   **Enforced automatically:** `hakoagent task complete` triggers a quiet re-index, but only if the
   working tree has changes (detected via `git status --porcelain`, so untracked files count). Tasks
   that don't touch code (docs, planning, research) skip re-index. Ad-hoc edits outside a task still
   require manual `hakoagent index`.
3. **Run `hakoagent impact <file>` before editing** — see blast radius of changes
4. Every action is logged to `events` (append-only) — review with `hakoagent events [--limit N]`
5. Completed tasks auto-extract into skills; duplicates are prevented — skills stay lean
6. Use `skill refine` to update skills, `skill troubleshoot` to flag issues — keeps skill set clean
7. Use `bug_scan` to find code quality issues before they become bugs
8. Use `skill get <skill_id> [--summary]` to retrieve skill context — `--summary` skips markdown body
   to keep agent context lean; full skill is available without the flag when needed.
9. **MCP server is OFF by default** — `install.sh --global` does not write MCP config to
   `~/.claude.json` or `~/.config/opencode/opencode.jsonc`. To enable MCP for a specific project:
   `hakoagent mcp enable` creates `.hakoagent/mcp-enabled` **and** adds
   `mcp.servers.hakoagent` (OpenCode V2 shape, absolute `hakoagent-mcp` path) to the project's
   `opencode.json` (or `.opencode/opencode.json`). If only a `.jsonc` exists it prints a snippet
   instead of rewriting comments. Use `hakoagent mcp disable` to remove both marker and config
   entry, and `hakoagent mcp status` to check.
10. **Prune stale revision history** — `hakoagent revision prune [--dry-run]` removes revisions for
   volatile collections (`code_index`, `context_cache`) that should never have been written.
   `--all --yes` also deletes durable history; back up `.hakoagent/` first.
