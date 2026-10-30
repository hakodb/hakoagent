# Feature Specification: Hakodb MCP Server (Local, Session-Bound)

**Feature Branch**: `010-hakodb-mcp-server`

**Created**: 2026-10-29

**Status**: Draft

**Input**: HakoAgent currently runs as a CLI where each command spawns a new Python process, opens the hakodb engine, does work, and exits. This prevents persistent cross-agent context sharing and continuous sync (net syncer needs time to discover peers). The solution is a lightweight MCP (Model Context Protocol) server over stdio that stays alive during an agent session, keeps the hakodb engine + net syncer loaded, and shuts down when the agent disconnects.

**Reference**: Model Context Protocol (MCP) specification — JSON-RPC 2.0 over stdio. https://modelcontextprotocol.io

---

## User Scenarios & Testing *(mandatory)*

### User Story 12 - Agent starts MCP server, keeps context alive across calls (Priority: P1)

A harness agent starts `hakoagent-mcp` as a subprocess. The MCP server opens the hakodb engine once and keeps it loaded. The agent sends multiple tool calls (save_doc, recall, graph.traverse, sync.sync-now) over the lifetime of the session. The engine and net syncer remain loaded between calls, enabling true cross-call context sharing and continuous sync.

**Independent Test**: Start `hakoagent-mcp`, send multiple `save_doc` calls, verify documents persist between calls (no re-open overhead), then close stdin, verify server exits.

**Acceptance Scenarios**:

1. **Given** `hakoagent-mcp` is started, **When** agent sends `save_doc` then `load_doc`, **Then** document is retrievable (engine stayed loaded)
2. **Given** `hakoagent-mcp` with sync enabled, **When** agent sends `sync.sync-now` twice, **Then** both calls succeed (net syncer stayed connected)
3. **Given** `hakoagent-mcp` is running, **When** agent closes stdin (EOF), **Then** server process exits cleanly

---

### User Story 13 - Multi-agent isolation via separate MCP instances (Priority: P1)

Each agent runs its own `hakoagent-mcp` instance with its own `.hakoagent/` directory. Agents do not share engine state. Sync is per-agent (each has its own net syncer with its own room key).

**Independent Test**: Start two `hakoagent-mcp` instances with different `.hakoagent/` directories and room keys. Verify Agent A cannot see Agent B's documents.

**Acceptance Scenarios**:

1. **Given** two MCP server instances with different directories, **When** Agent A writes a document, **Then** Agent B cannot load it
2. **Given** two MCP servers with different room keys, **When** Agent A enables mesh sync, **Then** Agent B does not join Agent A's room

---

### User Story 13 - MCP server shuts down when agent disconnects (Priority: P1)

When the agent process closes stdin (e.g., agent exits, user presses Ctrl+C, network drops), the MCP server detects EOF, shuts down the hakodb engine and net syncer, and exits. No orphan processes.

**Independent Test**: Start `hakoagent-mcp`, close stdin from the client side, verify server process exits within 5 seconds.

**Acceptance Scenarios**:

1. **Given** `hakoagent-mcp` is running, **When** client closes stdin, **Then** server exits within 5 seconds
2. **Given** `hakoagent-mcp` is running with sync enabled, **When** client disconnects, **Then** net syncer is stopped before exit

---

## Edge Cases

- **Stdin EOF mid-command** — Server should finish current command if possible, then shutdown
- **Malformed JSON-RPC** — Return JSON-RPC error response, continue listening
- **Unknown tool/method** — Return `method not found` error
- **Hakodb library unavailable** — Return error on initialization, exit gracefully
- **Port already in use** — N/A (stdio, no ports except net syncer internal)
- **Large document** — No size limit beyond system memory
- **Concurrent tool calls** — Serialized (single-threaded stdio processing)

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-048**: System MUST provide `hakoagent-mcp` executable that runs as a JSON-RPC 2.0 server over stdio
- **FR-049**: System MUST open hakodb engine once at server startup and keep it loaded for the session lifetime
- **FR-050**: System MUST close hakodb engine and net syncer when stdin EOF is detected (agent disconnects)
- **FR-051**: System MUST support `tools/list` and `tools/call` JSON-RPC methods
- **FR-052**: System MUST expose all hakoagent CLI functionality as MCP tools
- **FR-053**: System MUST run without any network connections (stdio only)
- **FR-054**: System MUST be cross-platform (Linux, macOS, Windows)
- **FR-055**: System MUST not require Python external dependencies (stdlib only)
- **FR-056**: System MUST exit within 5 seconds of stdin EOF
- **FR-057**: System MUST return JSON-RPC 2.0 compliant responses (result or error)
- **FR-058**: System MUST support `initialize` handshake with client capabilities
- **FR-059**: System MUST support `shutdown` method for graceful termination

### Key Entities

| Entity | Key Attributes | Relationships |
|--------|---------------|---------------|
| **MCP Server** | pid, started_at, engine_handle, net_syncer_handle, collections_config | owns Engine, NetSyncer |
| **MCP Session** | session_id, client_info, capabilities, connected_at, last_activity | belongs to MCP Server |
| **MCP Tool** | name, description, input_schema, handler_function | registered in MCP Server |

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-029**: `hakoagent-mcp` starts and responds to `initialize` within 1 second
- **SC-030**: Multiple `tools/call` succeed in sequence within same session (engine stays loaded)
- **SC-031**: Server exits within 5 seconds of stdin EOF
- **SC-032**: Net syncer stays connected across multiple `sync.sync-now` calls in same session
- **SC-033**: All 75+ existing tests continue to pass
- **SC-034**: New MCP server tests pass (initialize, tools/list, tools/call, shutdown, EOF shutdown)
- **SC-035**: No external Python dependencies required

---

## Assumptions

- Each agent runs its own `hakoagent-mcp` subprocess
- Agents communicate with the MCP server via stdin/stdout only
- The `.hakoagent/` directory is shared between the agent and the MCP server (same working directory)
- Sync room keys are unique per agent/team to avoid cross-contamination
- The MCP server does not need authentication (local-only, same user)

---
