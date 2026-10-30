# Implementation Plan: Hakodb MCP Server (Local, Session-Bound)

**Branch**: `010-hakodb-mcp-server` | **Date**: 2026-10-29 | **Spec**: `specs/010-hakodb-mcp-server/spec.md`

**Input**: Feature specification from `/specs/010-hakodb-mcp-server/spec.md`

**Reference**: Model Context Protocol (MCP) — JSON-RPC 2.0 over stdio

---

## Summary

Add a lightweight `hakoagent-mcp` executable that runs as a JSON-RPC 2.0 server over stdio. The server opens the hakodb engine once at startup, keeps it loaded for the session lifetime, optionally starts a net syncer for cross-agent sync, and shuts down when the agent disconnects (stdin EOF). This enables persistent cross-call context and continuous sync within a single agent session.

---

## Technical Context

**Language/Version**: Python 3.6.8 (stdlib only, no external dependencies)

**Primary Dependencies**: Python standard library (`json`, `sys`, `ctypes`, `threading`, `signal`, `os`, `time`); prebuilt hakodb shared library via `ctypes`; C ABI header `lib/hakodb.h` (v0.20.0)

**New Entry Point**: `hakoagent-mcp` — a copy of `hakoagent` that enters MCP mode instead of CLI mode

**New Functions in hakoagent**:
- `cmd_mcp(args)` — entry point when invoked as `hakoagent-mcp` or `hakoagent --mcp`
- `_mcp_json_rpc_loop()` — read stdin lines, parse JSON-RPC, dispatch, write stdout responses
- `_mcp_tool_dispatch(method, params)` — route MCP tool calls to existing hakoagent functions
- `_mcp_shutdown()` — free engine, stop net syncer, exit

**Testing**: `test_hakoagent.py` — existing 75 tests + new MCP server tests (initialize, tools/list, tools/call, shutdown, EOF shutdown)

**Target Platform**: Linux (x86_64 glibc2.28-el8), cross-platform Python (macOS, Windows via stdio)

**Constraints**: Python stdlib only; no external dependencies; stdio only (no TCP/HTTP); server shuts down on stdin EOF; no socket_sync; cloud sync optional with server+token

---

## Constitution Check

| Constitution Principle | Status | Notes |
|-------------------|--------|---------|
| Smart Memory | Met | MCP server keeps engine loaded across calls |
| Anti-Lupa | Met | Context persists across tool calls in same session |
| Kronologi & Histori | Met | Events + revisions preserved in session |
| Consistency | Met | JSON-RPC 2.0 responses, standard tool names |
| Cross-Model Consistency | Met | Same flow for all LLM models |
| Vigilance | Met | Server lifecycle is deterministic (start → serve → shutdown) |
| Clear Target | Met | Each tool call has clear target and result |
| Codebase Fluency | Met | All graph/code_index tools available |
| Context Frugality | Met | Context persists across calls, reducing re-embedding |
| Self Skill Improvement | Met | Skills persist in same session |
| Python Only | Met | stdlib only, no MCP Python package |
| Real Hakodb FFI | Met | ctypes to libhakodb .so |
| Code Quality | Met | Clean Python, no bare except |
| Testing | Met | Unit tests for MCP server functions |
| Maintainability | Met | Docs updated, no stale references |

No violations. Constitution check PASSED.

---

## Project Structure

### Documentation (this feature)

```text
specs/010-hakodb-mcp-server/
├── spec.md          # Feature specification
├── plan.md          # Implementation plan (this file)
├── research.md      # Phase 0 output (MCP protocol analysis)
├── data-model.md    # Phase 1 output (server session model)
├── quickstart.md    # Phase 1 output (validation scenarios)
├── contracts/
│   └── mcp-server-interface.md  # Phase 1 output (tool contracts)
└── tasks.md         # Phase 2 output (implementation tasks)
```

### Source Code Changes (repository root)

```text
hakoagent                      # Python CLI script — extended with cmd_mcp()
hakoagent-mcp                  # Symlink or copy: hakoagent --mcp entry point
lib/
├── libhakodb-x86_64-unknown-linux-glibc2.28-el8.so   # Prebuilt hakodb (v0.20.0)
├── hakodb.h                                               # Hakodb C ABI header (v0.20.0)
└── SHA256SUMS.txt                                         # Release checksums
.hakoagent/                      # Runtime data directory
├── hakoagent.db                 # Hakodb database file (loaded once per session)
├── memory/                      # JSON files per collection
├── sync/                        # Sync config (sync.json)
├── skills/
├── sessions/
├── logs/
└── _indices/
specs/                         # Feature specs (001-010)
test_hakoagent.py              # Python stdlib unittest (75+ tests)
install.sh                     # Project installer (installs hakoagent-mcp too)
INSTALL.md                     # Installation guide
AGENTS.md                      # Agent-facing instructions
```

---

## Phase 0: Outline & Research

### Unknowns from Technical Context

| Unknown | Status | Resolution |
|---------|--------|----------|
| stdio JSON-RPC parsing in Python 3.6 | Open | `sys.stdin.readline()` + `json.loads()` per line |
| Detecting stdin EOF in Python 3.6 | Open | `sys.stdin.readline()` returns `""` on EOF |
| Keeping engine alive across tool calls | Open | Module-level `_hako_engine` global persists in server process |
| Net syncer lifecycle in server | Open | Start on `sync.enable`, free on shutdown |
| Cross-platform stdio behavior | Open | Stdio works on Linux/macOS/Windows without modification |

### Research Findings

**MCP Protocol Basics:**
- Transport: stdio (stdin for client→server, stdout for server→client)
- Protocol: JSON-RPC 2.0
- Core methods: `initialize`, `initialized`, `tools/list`, `tools/call`, `shutdown`, `cancelRequest`
- Notifications (no response expected): `initialized`, `cancelRequest`, `progress`
- Requests (response expected): `initialize`, `tools/list`, `tools/call`, `shutdown`

**MCP JSON-RPC Message Format:**
```json
// Client → Server (request)
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"save_doc","arguments":{"collection":"events","doc_id":"evt_1","doc":{...}}}}

// Server → Client (response)
{"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"..."}]}}

// Server → Client (error)
{"jsonrpc":"2.0","id":1,"error":{"code":-32601,"message":"Method not found"}}
```

**Tool Result Format:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {"type": "text", "text": "result text"},
      {"type": "json", "data": {"key": "value"}}
    ]
  }
}
```

**Gap vs current hakoagent CLI:**

| CLI Behavior | MCP Server Behavior |
|-------------|-------------------|
| Process starts per command | Process stays alive for session |
| Engine opens/closes per command | Engine opens once, stays loaded |
| Net syncer starts/stops per command | Net syncer stays connected |
| No cross-call state | State persists in server memory |
| Exit after each command | Exit on stdin EOF |

Output: `research.md` documenting MCP protocol analysis and server design.

---

## Phase 1: Design & Contracts

### Data Model (`data-model.md`)

Entities:

| Entity | Key Attributes | Relationships |
|--------|---------------|---------------|
| **MCP Server** | pid, started_at, engine_handle, net_syncer_handle, collections_config, actor | owns Engine, NetSyncer |
| **MCP Session** | session_id, client_info, capabilities, connected_at, last_activity | belongs to MCP Server |
| **MCP Tool** | name, description, input_schema, handler_function | registered in MCP Server |

Collections: No new hakodb collections. Uses existing `code_index`, `code_edges`, `events`, `findings`, etc.

State transitions:
- Server: `starting` → `running` (after `initialize`) → `stopping` (on `shutdown` or EOF) → `stopped`
- NetSyncer: `stopped` → `running` (on `sync.enable`) → `stopped` (on `sync.disable` or server shutdown)

### Interface Contracts (`contracts/`)

**File**: `contracts/mcp-server-interface.md`

**MCP Methods:**

| Method | Params | Result |
|--------|--------|--------|
| `initialize` | clientInfo, capabilities | serverInfo, capabilities |
| `initialized` | — | (notification, no response) |
| `tools/list` | — | tools[] |
| `tools/call` | name, arguments | result |
| `shutdown` | — | ok |

**MCP Tools (all hakoagent functionality):**

| Tool | Input Params | Output |
|------|-------------|--------|
| `save_doc` | collection, doc_id, doc | {success, doc_id} |
| `load_doc` | collection, doc_id | doc |
| `recall` | query, limit, actor | results[] |
| `cache_put` | query, summary, ttl | cache_key |
| `cache_get` | query | summary |
| `cache_stats` | — | stats |
| `events` | limit | events[] |
| `graph.traverse` | node, direction, depth | nodes[], edges[] |
| `graph.shortest_path` | from, to | path[] |
| `graph.impact` | file | dependents[], blast_radius |
| `graph.search` | label, name_pattern, limit | nodes[] |
| `graph.query` | cypher_like | rows[] |
| `graph.detect_changes` | — | affected_symbols[] |
| `graph.get_snippet` | qualified_name | snippet |
| `graph.architecture` | tier | modules[], dependencies[] |
| `graph.adr.add` | title, status, rationale, consequences | adr_id |
| `graph.adr.list` | — | adrs[] |
| `graph.adr.get` | adr_id | adr |
| `graph.ingest_traces` | trace_file | count |
| `graph.list_projects` | — | projects[] |
| `graph.delete_project` | name | deleted |
| `sync.enable` | type, room_key, port, server, token, collections, local_only | status |
| `sync.disable` | — | status |
| `sync.status` | tier | status, peers |
| `sync.sync_now` | — | changes_synced |
| `sync.backup` | path | backup_path |
| `revision.list` | doc_id, collection | revisions[] |
| `skill.list/add/refine/troubleshoot/get` | name, id, summary | skill |
| `task.list/create/complete` | title, target, dod, priority | task |
| `vigilance` | — | report |
| `bug_scan` | — | findings[] |

Return value always in JSON-RPC 2.0 format: `{"jsonrpc":"2.0","id":<id>,"result":{...}}` or `{"jsonrpc":"2.0","id":<id>,"error":{"code":<code>,"message":<msg>}}`.

### Quickstart Validation Guide (`quickstart.md`)

**Prerequisites**:
- Python 3 (stdlib only)
- Prebuilt hakodb library at `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so`

**Setup**:
```bash
# Install (installs both hakoagent and hakoagent-mcp)
./install.sh --global
```

**Session-based MCP usage**:

```bash
# Terminal 1: Start MCP server as subprocess
$ hakoagent-mcp
# Server is now running, waiting for JSON-RPC on stdin

# Terminal 2: Send MCP commands (simulated)
$ echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"capabilities":{}}}' | ./hakoagent-mcp
{"jsonrpc":"2.0","id":1,"result":{"capabilities":{"tools":true}}}

# Send multiple tool calls in same session
$ echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"save_doc","arguments":{"collection":"findings","doc_id":"f1","doc":{"content":"test","actor":"agent-a"}}}}' | ./hakoagent-mcp
{"jsonrpc":"2.0","id":2,"result":{"success":true,"doc_id":"f1"}}

# Close stdin → server shuts down
$ echo '{"jsonrpc":"2.0","id":3,"method":"shutdown"}' | ./hakoagent-mcp
{"jsonrpc":"2.0","id":3,"result":{}}
# Server exits
```

**Expected outcomes**:
- `hakoagent-mcp` starts and responds to `initialize`
- Multiple `tools/call` succeed in sequence (engine stays loaded)
- `sync.enable` starts net syncer, `sync.sync-now` works across calls
- Server exits when stdin closes or `shutdown` method received
- `python3 test_hakoagent.py` — 75+ tests pass

---

## Phase 2: Implementation Tasks (see `tasks.md`)

Plan workflow complete. Ready to proceed to `/speckit-implement`.
