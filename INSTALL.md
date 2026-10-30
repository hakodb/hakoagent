# HakoAgent — Installation and Usage

## 1. Installation

### Prerequisites
- Python 3 (stdlib only, no external dependencies)

### Install

```bash
# Clone the repository
git clone https://github.com/hakodb/hakoagent.git
cd hakoagent

# Install (cross-platform installer, Python stdlib only)
python install.py            # project-local: ./hakoagent + ./lib/ + ./AGENTS.md + .opencode/
python install.py --global   # global: ~/.local/bin (Linux) | %LOCALAPPDATA%\hakoagent\bin + .cmd shims (Windows)
export PATH="$HOME/.local/bin:$PATH"   # Linux only; Windows: setx PATH (printed by the installer)

# Verify the installation
hakoagent --help
```

Notes:
- `install.py` downloads the native hakodb library from the latest `github.com/hakodb/hakodb`
  release (Windows x86_64: `.dll`, Linux x86_64: `.so`) and verifies it against `SHA256SUMS`.
- **HakoAgent refuses to run without the native library** (no JSON fallback).
- macOS is not supported yet (no native library) — the installer exits with a clear message.
- Windows: run the scripts through the interpreter, e.g. `python hakoagent --help`; MCP config
  is written with `python "<path to hakoagent-mcp>"` as the command.
- `--remove-data` on uninstall also deletes `.hakoagent/`.

### Database initialization (once per project)

```bash
cd /path/to/project
hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

This creates:
- A `.hakoagent/` directory at the project root
- 9 primary collections: sessions, events, decisions, findings, code_index, tasks, context_cache, skills, lessons_learned
- OpenCode config files: `.opencode/skills/hakoagent-usage-pattern/SKILL.md` and `.opencode/commands/hakoagent.md`

---

## 2. Database initialization

Every project that will use HakoAgent must be initialized first:

```bash
cd /path/to/project
hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

This creates:
- A `.hakoagent/` directory at the project root
- A `hakoagent.db` database file
- 9 primary collections: sessions, events, decisions, findings, code_index, tasks, context_cache, skills, lessons_learned

---

## 3. CLI commands

| Command | Description | Example |
|---------|-------------|---------|
| `hakoagent init` | Initialize database and collections | `hakoagent init --db ./.hakoagent/hakoagent.db --collections all` |
| `hakoagent index` | Scan and index the codebase | `hakoagent index` |
| `hakoagent recall` | Retrieve context from memory (HNSW + FTS) | `hakoagent recall "Rust error handling"` |
| `hakoagent skill list` | List all active skills | `hakoagent skill list` |
| `hakoagent skill add` | Add a new skill | `hakoagent skill add "rust-error-handling-pattern"` |
| `hakoagent task list` | List tasks and status | `hakoagent task list` |
| `hakoagent events` | View chronological history | `hakoagent events` |
| `hakoagent vigilance` | Detect forgotten files / regressions | `hakoagent vigilance` |
| `hakoagent cache stats` | View cache statistics | `hakoagent cache stats` |
| `hakoagent cache get` | Retrieve context from the cache | `hakoagent cache get "query"` |
| `hakoagent cache put` | Store context in the cache | `hakoagent cache put "query" "summary"` |
| `hakoagent graph traverse` | Dependency graph traversal | `hakoagent graph traverse <node> <dir> <depth>` |
| `hakoagent graph shortest-path` | Shortest path (Dijkstra) | `hakoagent graph shortest-path <from> <to>` |
| `hakoagent graph dependents` | Files depending on a node | `hakoagent graph dependents <node>` |
| `hakoagent graph dependents-reverse` | Files a node depends on | `hakoagent graph dependents-reverse <node>` |
| `hakoagent revision prune` | Remove volatile-collection revisions | `hakoagent revision prune --dry-run` |
| `hakoagent mcp enable` | Enable MCP for this project | `hakoagent mcp enable` |
| `hakoagent mcp disable` | Disable MCP for this project | `hakoagent mcp disable` |
| `hakoagent mcp status` | Check MCP status for this project | `hakoagent mcp status` |

---

## 4. Usage examples

### 4.1 Initialization and first setup

Initialize the database at your project root:

```bash
cd /your-project
hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

Output:

```
HakoAgent database initialized at: ./.hakoagent/hakoagent.db
Collections: ["sessions", "events", "decisions", "findings", "code_index", "tasks", "context_cache", "skills", "lessons_learned"]
```

### 4.2 Retrieving context (anti-forgetting and codebase fluency)

Prior to searching information manually in the codebase, run `hakoagent recall` first:

```bash
hakoagent recall "Rust error handling best practices" --limit 5
```

Output:

```
Query: Rust error handling best practices
Context retrieval initialized (HNSW + FTS + summarizer + cache).
  Results:
    - speckit-core/src/memory/mod.rs :: mod
    - specs/001-refactor-hakoagent/plan.md :: plan
    - speckit-core/src/memory/events.rs :: events
```

### 4.3 Skill management (self skill improvement)

```bash
# List the active skills
hakoagent skill list

# Add a new skill
hakoagent skill add "python-error-handling-pattern"

# Store in the cache for reuse
hakoagent cache put "error-handling-python" "Use specific try/except, avoid bare except, re-raise with raise ... from exc"

# Retrieve from the cache (fast, no LLM calls)
hakoagent cache get "error-handling-python"
```

### 4.4 Task management (clear targets)

```bash
# List the tasks
hakoagent task list

# Create a task with a target and definition of done
hakoagent task create "Implement error handling" "All public functions must use Result<T, E>" "Unit tests >= 80% coverage, docs updated" P1

# Mark a task complete
hakoagent task complete <task_id>

# List the tasks
hakoagent task list
```

### 4.5 Vigilance checks

```bash
# Detect edited-but-untested files, leftover TODOs, regressions
hakoagent vigilance
```

### 4.6 Cache management (context frugality)

```bash
# View cache statistics
hakoagent cache stats

# Manually store context in the cache
hakoagent cache put "sample-query" "summary of the search results" 300

# Retrieve context from the cache (fast, no LLM calls)
hakoagent cache get "sample-query"
```

### 4.7 Graph traversal (codebase fluency)

```bash
# Traverse from a symbol (e.g. the function validate_input)
hakoagent graph traverse validate_input in 2

# Find the shortest path between two symbols
hakoagent graph shortest-path main error_handler

# See what depends on a file
hakoagent graph dependents src/utils.rs

# See what a function calls
hakoagent graph dependents-reverse src/main.rs

# View the blast radius before editing a file
hakoagent impact src/main.rs
```

---

## 5. Data collections (HakoDB)

All data lives in `./.hakoagent/hakoagent.db` with 9 primary collections:

| Collection | Purpose |
|------------|---------|
| `sessions` | Agent session records (started_at, ended_at, status) |
| `events` | Chronological history of all actions (append-only) |
| `decisions` | Architecture decisions + rationale + consequences |
| `findings` | Codebase findings, bugs, patterns, error notes |
| `code_index` | Symbols, files, dependencies (for graph traversal) |
| `tasks` | Tasks with target, priority, DoD, status |
| `context_cache` | Compact context cache reducing LLM calls |
| `skills` | Successful skills/patterns for reuse |
| `lessons_learned` | Lessons from failures to avoid |

---

## 6. Harness agent integration (OpenCode)

HakoAgent is designed as an add-on/skill for personal harness agents like OpenCode. To integrate:

1. **Add hakoagent to your agent configuration** so the `hakoagent` command can be called from within chat
2. **Use the following interaction template** in the agent's system prompt:

```
You are an AI agent with access to the HakoAgent Memory System. Use these commands:

- hakoagent recall <query> - Retrieve context from memory (do not forget to check the cache first)
- hakoagent skill list - List the available skills
- hakoagent task list - List tasks and status
- hakoagent events - View the action history
- hakoagent vigilance - Detect regressions and forgotten files
- hakoagent graph traverse <node> <dir> <depth> - Traverse codebase dependencies
- hakoagent graph shortest-path <from> <to> - Find the shortest path between symbols
- hakoagent cache stats - View cache statistics
- hakoagent cache put <query> <summary> [ttl] - Store context in the cache

Always use hakoagent recall before searching information in the codebase to reduce LLM endpoint calls.
```

### 6.1 MCP server (optional, per project)

MCP is **off by default**. A global install does not write MCP config to `~/.claude.json`
or `~/.config/opencode/opencode.jsonc`.

```bash
cd /path/to/project
hakoagent mcp enable    # creates .hakoagent/mcp-enabled + writes mcp.servers.hakoagent
hakoagent mcp status    # check status
hakoagent mcp disable   # removes the marker + config entry
```

`mcp enable` writes the following OpenCode V2 entry to `opencode.json` (or
`.opencode/opencode.json`) with absolute paths:

```json
{
  "mcp": {
    "servers": {
      "hakoagent": {
        "type": "local",
        "command": ["/home/user/.local/bin/hakoagent-mcp"]
      }
    }
  }
}
```

If the project only has `opencode.jsonc`, the command prints a snippet for manual pasting so
comments are not lost. After enabling, restart the OpenCode session or run `hakoagent-mcp`.

---

## 7. Data architecture

All data is stored under `./.hakoagent/` via the hakodb engine:

```
.hakoagent/
├── memory/          # data per collection
│   ├── sessions/
│   ├── events/
│   ├── decisions/
│   ├── findings/
│   ├── code_index/
│   ├── tasks/
│   ├── context_cache/
│   ├── skills/
│   └── lessons_learned/
├── skills/          # skill files in Markdown format
├── sessions/        # session exports (optional)
└── logs/            # operation logs (optional)
```

## 8. Troubleshooting

| Issue | Solution |
|-------|----------|
| `hakoagent: command not found` | Make sure `~/.local/bin` is on PATH: `export PATH="$HOME/.local/bin:$PATH"` (Windows: add `%LOCALAPPDATA%\hakoagent\bin` to PATH) |
| `Database not found` | Run `hakoagent init --db ./.hakoagent/hakoagent.db --collections all` first |
| `Cache empty` | Run `hakoagent recall <query>` at least once to populate the cache |
| `Graph empty` | Make sure the codebase is indexed via `hakoagent init` or `hakoagent index` |
| hakodb native library missing | Run `python install.py` to download the library for your platform (see section 1) |

---

## 9. License

MIT License — same as HakoDB. See `LICENSE-MIT` in the HakoDB repository.

---

## 10. Contact and support

- Repository: https://github.com/hakodb/hakoagent
- Documentation: https://github.com/hakodb.github.io (HakoDB docs site)
- License: MIT
