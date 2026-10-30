# Interface Contract: HakoAgent Memory, Context & History System (Non-MCP, Embedded Hakodb)

**Feature**: 007-hakodb-memory-context-history  
**File**: `contracts/hakodb-memory-context-interface.md`  
**Status**: Draft

HakoAgent exposes a tool calling interface for the harness agent. All return values are in JSON format for easy parsing by the harness agent. **No MCP server or plugin is involved** — all context sharing via embedded hakodb FFI + shared file on filesystem.

## Tool Contracts

| Tool | Parameter | Return |
|------|-----------|--------|
| `hakoagent.init` | `db_path`, `collections` | `status`, `collections_created` |
| `hakoagent.event_log` | `action`, `target`, `actor`, `session_id`, `change_type`, `metadata` | `event_id`, `timestamp` |
| `hakoagent.recall` | `query`, `limit`, `actor`, `collection` | `context_results`, `cache_hit` (bool), `llm_calls_saved` |
| `hakoagent.cache.stats` | — | `total_hits`, `total_misses`, `eviction_count`, `cache_size`, `llm_calls_saved` |
| `hakoagent.cache.get` | `query` | `summary`, `cache_hit` (bool) |
| `hakoagent.cache.put` | `query`, `summary`, `ttl_seconds` | `cache_key`, `status` |
| `hakoagent.task.create` | `title`, `target`, `definition_of_done`, `priority`, `actor` | `task_id`, `status` |
| `hakoagent.task.complete` | `task_id`, `dod_verified`, `actor` | `status`, `completed_at` |
| `hakoagent.skill.add` | `name`, `content` (Markdown), `actor` | `skill_id`, `status` |
| `hakoagent.skill.list` | — | `skills_list` (name, id, status, success, failure) |
| `hakoagent.events` | `limit`, `session_id`, `actor` | `events_list` |
| `hakoagent.index` | `root_path` | `indexed_count` |
| `hakoagent.graph.trace` | `node`, `direction`, `max_depth`, `tier` | `visited_nodes`, `edges_traversed` |
| `hakoagent.graph.shortest-path` | `from_node`, `to_node` | `path_nodes`, `total_cost` |
| `hakoagent.graph.dependents` | `node_id` | `dependent_nodes` |
| `hakoagent.graph.dependents-reverse` | `node_id` | `dependent_reverse_nodes` |
| `hakoagent.graph.impact` | `file_path` | `blast_radius_nodes` |
| `hakoagent.graph.coverage` | `file_paths` | `coverage_status_per_file` |
| `hakoagent.vigilance` | `root_path` | `vigilance_report` |
| `hakoagent.revision.list` | `doc_id`, `doc_collection` | `revisions_list` |

## Return Format

All tools return JSON:

```json
{
  "status": "ok",
  "data": { ... },
  "timestamp": "2026-10-29T08:05:00Z",
  "actor": "agent-a"
}
```

Error format:

```json
{
  "status": "error",
  "error": "human-readable error message",
  "timestamp": "2026-10-29T08:05:00Z",
  "actor": "agent-a"
}
```

## Context Efficiency & LLM Cost Reduction

The `context_cache` collection tracks `llm_calls_saved` per entry — each cache hit increments this counter, representing an LLM endpoint call that was avoided. `hakoagent cache stats` reports the aggregate `llm_calls_saved` metric.

Context efficiency is achieved through:
1. **Cache-first retrieval**: `hakoagent recall` checks `context_cache` (TTL-valid) before performing vector search
2. **Minimal context**: Only the most relevant documents are returned, ranked by TF-IDF + cosine similarity
3. **Cache reuse**: Repeated queries within TTL (default 300s) are served from cache without any LLM endpoint call
4. **LLM calls saved counter**: Each cache hit increments `llm_calls_saved`, providing measurable cost reduction

## Multi-Agent Sync Path (Non-MCP)

All write tools (`event_log`, `task.create`, `skill.add`, etc.) accept an `actor` parameter identifying the originating harness agent. The `actor` is stored in document metadata, enabling any agent to:

1. Read documents written by any other agent through the same hakodb (`hakoagent recall`)
2. Filter results by a specific actor (`actor` query parameter)
3. Trace the origin of each document via the `actor` field

Multiple agents share context by accessing the same `.hakoagent/hakoagent.db` file on the filesystem. Hakodb handles concurrent access locking internally. **No MCP server or plugin is required**.

## Graph Trace (adapted from MCP `trace_path`)

`hakoagent graph trace <node> <direction> <max_depth> [<tier>]` performs BFS over `code_index` dependency edges:

| Direction | Meaning |
|-----------|---------|
| `outbound` | What does this node depend on? (outgoing edges) |
| `inbound` | Who depends on this node? (incoming edges) |
| `both` | Full neighborhood in both directions |

Evidence tier (`--tier scout\|verify\|auditor`, default `verify`):
- **scout**: Fast provisional lookup, depth limited, small result set
- **verify**: Task-directed with relevant trace directions, exact snippets
- **auditor**: Bounded-scope full verification, both call directions, explicit limitations

## Shortest Path (adapted from MCP `query_graph`)

`hakoagent graph shortest-path <from> <to>` runs Dijkstra over `code_index` dependency edges, returning the shortest dependency chain between two symbols.

## Impact Analysis (adapted from MCP `get_architecture`)

`hakoagent impact <file_path>` computes blast radius — all transitive dependents of a file — using BFS over reverse edges in `code_index`.

## Index Coverage (adapted from MCP `check_index_coverage`)

`hakoagent graph coverage <file_paths...>` reports per-file index coverage status. Files with gaps fall back to source read/grep (read/grep fallback for uncovered ranges).

## Immutable Revisions (History)

The `revisions` collection stores previous document versions on every update. Revisions are immutable — once created, they cannot be updated or deleted. This provides time-travel debugging and history continuity.

## Append-Only Guard

The `events` collection enforces append-only at the application level: before writing an event, the system checks if `event_id` already exists and rejects the write if it does. Events cannot be overwritten once written.
