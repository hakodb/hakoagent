# Interface Contract — Hakodb MCP Server (US12-US14)

**Feature**: 010-hakodb-mcp-server  
**Date**: 2026-10-29  
**Status**: Draft

## Protocol

**Transport**: stdio (stdin = client→server, stdout = server→client)  
**Protocol**: JSON-RPC 2.0  
**Encoding**: UTF-8, one JSON object per line  
**Session**: Server process lifetime = agent session lifetime

---

## MCP Methods

### initialize

Client → Server:
```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"capabilities":{}}}
```

Server → Client:
```json
{"jsonrpc":"2.0","id":1,"result":{"capabilities":{"tools":true}}}
```

### initialized (notification, no response)

Client → Server:
```json
{"jsonrpc":"2.0","method":"initialized","params":{}}
```

### tools/list

Client → Server:
```json
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
```

Server → Client:
```json
{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"save_doc","description":"...","inputSchema":{...}},...]}}
```

### tools/call

Client → Server:
```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"save_doc","arguments":{"collection":"events","doc_id":"evt_1","doc":{"content":"test"}}}}
```

Server → Client:
```json
{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"saved"},{"type":"json","data":{"success":true,"doc_id":"evt_1"}}]}}
```

### shutdown

Client → Server:
```json
{"jsonrpc":"2.0","id":4,"method":"shutdown","params":{}}
```

Server → Client:
```json
{"jsonrpc":"2.0","id":4,"result":{}}
```
Then server exits.

---

## MCP Tools

All hakoagent CLI functionality exposed as MCP tools. Each tool returns:
```json
{
  "content": [
    {"type": "text", "text": "<human readable summary>"},
    {"type": "json", "data": <structured data>}
  ]
}
```

### Memory Operations

| Tool | Input Params | Output Data |
|------|-------------|-------------|
| `save_doc` | collection (str), doc_id (str), doc (dict) | {success: bool, doc_id: str} |
| `load_doc` | collection (str), doc_id (str) | doc (dict or null) |
| `recall` | query (str), limit (int, default 5), actor (str, optional) | results[] |
| `cache_put` | query (str), summary (str), ttl (int, default 300) | cache_key (str) |
| `cache_get` | query (str) | summary (str or null) |
| `cache_stats` | — | {hits, misses, hit_rate, cache_size, evictions} |
| `events` | limit (int, default 10) | events[] |
| `revision.list` | doc_id (str), doc_collection (str) | revisions[] |

### Graph Operations

| Tool | Input Params | Output Data |
|------|-------------|-------------|
| `graph.traverse` | node (str), direction (str), depth (int) | nodes[], edges[] |
| `graph.shortest_path` | from (str), to (str) | path[], distance |
| `graph.impact` | file (str) | dependents[], blast_radius |
| `graph.search` | label (str, opt), name_pattern (str, opt), limit (int) | nodes[] |
| `graph.query` | cypher_like (str), limit (int) | rows[] |
| `graph.detect_changes` | diff_path (str, opt) | affected_symbols[], affected_files[] |
| `graph.get_snippet` | qualified_name (str), context_lines (int) | snippet, file_path, line_range |
| `graph.architecture` | tier (str, opt) | modules[], dependencies[], entry_points[] |
| `graph.adr.add` | title, status, rationale, consequences, actor | adr_id |
| `graph.adr.list` | — | adrs[] |
| `graph.adr.get` | adr_id (str) | adr |
| `graph.ingest_traces` | trace_file (str) | count |
| `graph.list_projects` | — | projects[] |
| `graph.delete_project` | name (str) | deleted |

### Sync Operations

| Tool | Input Params | Output Data |
|------|-------------|-------------|
| `sync.enable` | type (str), room_key (str), port (int, opt), server (str, opt), token (str, opt), collections (str[], opt), local_only (str[], opt), actor (str) | enabled, type, room_key, port |
| `sync.disable` | — | enabled (false) |
| `sync.status` | tier (str, opt) | enabled, type, peers, replication_collections, local_only_collections |
| `sync.sync_now` | — | changes_synced, peers_contacted |
| `sync.backup` | path (str) | backup_path, status |

### Skill Operations

| Tool | Input Params | Output Data |
|------|-------------|-------------|
| `skill.list` | — | skills[] |
| `skill.add` | name (str) | skill_id |
| `skill.refine` | id (str), new_summary (str) | skill_id |
| `skill.troubleshoot` | id (str), issue (str) | failure_count |
| `skill.get` | skill_id (str) | skill |

### Task Operations

| Tool | Input Params | Output Data |
|------|-------------|-------------|
| `task.list` | — | tasks[] |
| `task.create` | title, target, definition_of_done, priority (opt), actor (opt) | task_id |
| `task.complete` | task_id, dod_verified (bool) | status |

### Other Operations

| Tool | Input Params | Output Data |
|------|-------------|-------------|
| `vigilance` | — | report |
| `bug_scan` | — | findings[] |
| `team.init` | name, members, remote (opt) | team_id |
| `team.status` | — | team info |
| `team.assign` | task_id, member | status |
| `team.context` | — | team context |

---

## Error Codes

| Code | Message | Meaning |
|------|---------|---------|
| -32600 | Invalid Request | Invalid JSON-RPC |
| -32601 | Method not found | Unknown method name |
| -32602 | Invalid params | Invalid tool arguments |
| -32603 | Internal error | Engine error, FFI failure |
| -32604 | Sync not enabled | sync.sync-now called without sync.enable |
| -32605 | Engine not available | hakodb library not loaded |

---

## Session Lifecycle Events

| Event | Trigger | Server Action |
|-------|---------|---------------|
| `initialize` | First client message | Open hakodb engine, set config |
| `tools/call` | Any tool call | Execute, return result, update last_activity |
| `shutdown` | Client request | Free engine, stop net syncer, exit 0 |
| `stdin EOF` | Agent disconnects | Free engine, stop net syncer, exit 0 |
| `SIGINT/SIGTERM` | OS signal | Free engine, stop net syncer, exit 0 |
