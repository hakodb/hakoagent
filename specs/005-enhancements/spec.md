# Spec: HakoAgent — HakoDB Native Vector + Graph Memory & Graph Traversal

**Input**: ponytail research on hakodb v0.20.0 + OpenCode codebase-memory-mcp integration
**Status**: Draft
**Prerequisite**: specs/003-cache-graph-system/spec.md (context_cache, graph traversal base)
**Prerequisite**: specs/004-team-context/spec.md (team context, multi-agent)

## 1. Overview

HakoAgent currently uses JSON file storage under `.hakoagent/memory/` with TF-IDF keyword scoring for context retrieval. This spec describes upgrading to **hakodb-native vector + graph storage** per the ponytail research, plus **multi-agent collaboration** via shared memory collections.

## 2. Ponytail Corner-Cut Markers

| Corner-cut | Ceiling | Upgrade path |
|------------|---------|--------------|
| JSON file storage | No concurrent writes, no vector search, no concurrency safety | Replace with hakodb FFI (libhakodb.so) |
| TF-IDF keyword scoring | No semantic similarity, misses synonyms | HNSW vector search with embeddings |
| Single `dependinsi` edge type | Only one edge type, no typed relationships | Typed edges: import, call, depends_on, test_of |
| Manual `hakoagent index` | No real-time file watching | `watch_collection()` background watcher |
| JSON file storage | No shared state between agents | hakodb net-sync / cloud-sync for team sync |

## 3. User Stories

### US1: Vector Semantic Search (P1)
The agent can search for context by meaning, not just exact keywords. A query for "error handling" must find code that uses `try/catch` even when the word "error" does not appear.

**Independent Test**: Query "error handling" returns code with `try/catch` blocks even when word "error" doesn't appear.

### US2: Graph Traversal with Typed Edges (P1)
The agent can traverse dependencies with varying relationship types: `imports`, `calls`, `data_flows`, `test_of`, `depends_on`.

**Independent Test**: Query "what does this function call?" returns only direct function calls, not all dependents.

### US3: Graph Shortest Path with Weighted Edges (P1)
The agent can find the shortest path between two symbols with varying edge weights (e.g., `calls` weight=1, `imports` weight=2, `data_flows` weight=5).

**Independent Test**: Dijkstra returns path with minimum total weight, not just fewest hops.

### US4: Multi-Agent Team Context (P2)
Multiple agents can see tasks, skills, and events created by other agents in the same team.

**Independent Test**: Agent B can see skills created by agent A after auto-sync.

### US5: Append-Only Event Log with Watch (P2)
Every agent action is recorded as an append-only event. The system can detect changes in real time.

**Independent Test**: After a file is modified, the event is saved automatically without manual logging.

---

## 4. Data Model Changes

### New Collections

| Collection | Purpose |
|------------|---------|
| `graph_edges` | Typed graph edges: from_node, to_node, edge_type, weight |
| `code_vectors` | Vector embeddings for semantic search: doc_id, vector, text_chunk |
| `team_meta` | Team configuration: team_name, members, remote, room_key |
| `agent_sessions` | Per-agent session: agent_name, agent_type, started_at |

### Enhanced Collections

| Collection | New Fields |
|------------|-----------|
| `code_index` | Add `vector_id` (link to code_vectors), `file_hash` (for change detection) |
| `skills` | Already has version, failure_count, hit_count — add `depends_on` (skill dependencies) |
| `tasks` | Already has `assignee` — add `blocked_by` (task dependencies), `blocking` (tasks blocked by this) |
| `events` | Already append-only — add `source` (auto-index, manual, agent_action), `run_id` (correlation ID) |

### New Structs (Python dicts)

```python
# Graph Edge
{
    "edge_id": "edge_abc123",
    "from_node": "code_index_abc123",
    "to_node": "code_index_def456",
    "edge_type": "calls",  # import, call, depends_on, data_flows, test_of
    "weight": 1.0,
    "created_at": "2026-10-29T..."
}

# Vector Entry
{
    "cache_key": "vec_abc123",
    "file_path": "src/main.rs",
    "symbol_name": "validate_input",
    "vector": [0.1, -0.3, ...],  # embedding vector
    "text_chunk": "...",  # original code/text
    "created_at": "..."
}

# Task with assignee & blocking
{
    "task_id": "task_xyz",
    "title": "Implement error handling",
    "assignee": "alice",
    "blocked_by": ["task_abc"],  # task IDs this depends on
    "blocking": ["task_def"],   # task IDs that depend on this
    ...
}
```

---

## 5. New CLI Commands

| Command | Description |
|---------|---------|
| `hakoagent graph traverse <node> <dir> <depth> [--edge-type <type>]` | BFS traversal with optional edge type filter |
| `hakoagent graph shortest-path <from> <to> [--weighted]` | Dijkstra shortest path with weighted edges |
| `hakoagent graph dependents <node> [--edge-type <type>]` | Nodes that depend on given node |
| `hakoagent graph dependents-reverse <node> [--edge-type <type>]` | Nodes given node depends on |
| `hakoagent graph search <query> [--limit N]` | Vector search (semantic) across code_index |
| `hakoagent graph impact <file> [--max-depth N]` | Impact analysis: what breaks if this file changes |
| `hakoagent init --auto` | Auto-initialize if not already (replaces manual init) |

### Updated Commands

| Command | Change |
|---------|--------|
| `hakoagent recall <query> [--limit N] [--semantic]` | Add `--semantic` flag for vector search |
| `hakoagent index` | Also builds graph edges and vector embeddings |
| `hakoagent task create ... [--assignee <name>] [--depends-on <task_id>]` | Add assignee and depends_on fields |

---

## 6. Implementation Strategy

### Phase 1: Replace JSON Storage with Hakodb FFI (Week 1)

Replace JSON file storage with hakodb C ABI calls:
- `hk_engine_open`, `hk_engine_put`, `hk_engine_get`, `hk_engine_delete`
- `hk_engine_watch_collection` for real-time change detection

**PONYTAIL**: JSON files work for single-agent. Ceiling: no concurrent writes, no concurrent safety. Upgrade: hakodb FFI with `hk_engine_*` C ABI calls.

### Phase 2: Add Vector Search (Week 2)

Replace TF-IDF with HNSW vector search using hakodb's native HNSW index. Add embedding generation (can use sentence-transformers or simple TF-IDF vectors as fallback).

### Phase 3: Typed Graph Edges (Week 2)

Replace single `dependinsi` field with typed `graph_edges` collection. Add edge types: import, call, depends_on, data_flows, test_of, defines.

### Phase 4: Real-Time Change Stream (Week 3)

Use `watch_collection("code_index")` to detect file changes and auto-update graph edges. No manual `hakoagent index` needed.

### 5. Multi-Agent Sync (Week 4)

Add `hakodb` `net-sync` feature flag. Agent instances sync events, tasks, and skills via mesh network.

---

## 7. Implementation Tasks

See `tasks.md` in this directory for detailed task list.

## 8. Contracts

See `contracts/` directory for CLI tool contracts and API contracts.

## 9. Quickstart

See `quickstart.md` for getting started guide.

---

**End of spec.md part 1.** Next: plan.md with implementation phases and timeline.