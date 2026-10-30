# Data Model — Hakodb MCP Server (US12-US14)

**Feature**: 010-hakodb-mcp-server  
**Date**: 2026-10-29  
**Status**: Draft

## Entities

### MCP Server (in-memory, not persisted)

| Attribute | Type | Description |
|-----------|------|-------------|
| `pid` | int | Process ID |
| `started_at` | string | ISO 8601 timestamp |
| `engine_handle` | c_void_p | Hakodb engine pointer |
| `net_syncer_handle` | c_void_p or None | Net syncer pointer (if sync enabled) |
| `config` | dict | Sync configuration (type, room_key, port, etc.) |
| `actor` | string | Agent name |
| `collections_config` | dict | Replication/collections settings |

### MCP Session (in-memory, per server instance)

| Attribute | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Unique session ID |
| `client_info` | dict | Client name, version |
| `capabilities` | dict | Client capabilities (tools, etc.) |
| `connected_at` | string | ISO 8601 timestamp |
| `last_activity` | string | ISO 8601 timestamp |
| `tool_call_count` | int | Number of tool calls in session |

### MCP Tool Registry (static, in-memory)

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | string | Tool name (e.g., "save_doc", "recall") |
| `description` | string | Human-readable description |
| `input_schema` | dict | JSON Schema for input validation |
| `handler` | function | Python function reference |

## Collections

No new hakodb collections. The MCP server uses existing collections:
- `code_index`, `code_edges`, `events`, `findings`, `decisions`, `tasks`
- `context_cache`, `skills`, `lessons_learned`, `revisions`
- `sessions`, `adrs`, `traces`, `projects`

## State Transitions

| Entity | Transitions |
|--------|-------------|
| **MCP Server** | `starting` → `running` (after `initialize`) → `stopping` (on `shutdown` or stdin EOF) → `stopped` |
| **NetSyncer** | `stopped` → `running` (on `sync.enable`) → `stopped` (on `sync.disable` or server shutdown) |
| **Hakodb Engine** | `closed` → `open` (on server start) → `closed` (on server shutdown) |

## Validation Rules

- **Server**: Must have engine open before processing any `tools/call`
- **Sync**: Must be enabled before `sync.sync-now` or `sync.status`
- **Collections**: Must exist in COLLECTIONS list for `save_doc`/`load_doc`
- **Tool name**: Must be registered in tool registry for `tools/call`

## Evidence Tiers for Sync (via MCP)

| Tier | Behavior |
|------|----------|
| Scout | Fast status check, provisional peer list |
| Verify | Full peer enumeration, pending change count |
| Auditor | Complete change listing, per-collection sync status, conflict details |
