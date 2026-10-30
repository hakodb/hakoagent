# Data Model — Codebase Knowledge Graph (US8)

**Feature**: 008-codebase-knowledge-graph  
**Date**: 2026-10-29  
**Status**: Draft

Entities extracted from the feature specification, extending the MCP codebase-memory skill patterns adapted to embedded hakodb.

## Entities

| Entity | Key Attributes | Relationships |
|--------|---------------|---------------|
| **CodeNode** | `entry_id`, `file_path`, `symbol_name`, `symbol_type`, `label`, `qualified_name`, `line_number`, `file_hash`, `actor` | has outgoing/incoming edges → CodeEdge |
| **CodeEdge** | `edge_id`, `source_id`, `target_id`, `edge_type`, `confidence`, `line_number`, `actor` | source → CodeNode, target → CodeNode |
| **ArchitectureDecision** | `adr_id`, `title`, `status`, `rationale`, `consequences`, `created_at`, `actor` | — |
| **TraceEntry** | `trace_id`, `timestamp`, `span_id`, `parent_span_id`, `operation`, `service`, `duration_ms`, `actor` | — |
| **Project** | `project_name`, `root_path`, `indexed_at`, `node_count`, `edge_count`, `actor` | — |

## Edge Types (16+)

| Edge Type | Meaning |
|-----------|---------|
| `CALLS` | Function A calls Function B |
| `HTTP_CALLS` | Function A makes HTTP request to endpoint B |
| `ASYNC_CALLS` | Function A calls B asynchronously (promise/callback) |
| `SPAWNS` | Function A spawns process/thread B |
| `DATA_FLOWS` | Data flows from A to B |
| `IMPORTS` | File A imports symbol from File B |
| `DEFINES` | File A defines symbol B |
| `DEFINES_METHOD` | Class A defines method B |
| `OVERRIDE` | Method A overrides Method B |
| `USAGE` | File A uses symbol B |
| `CALL_REFERENCE` | Symbol A references Symbol B in call |
| `CONFIGURES` | Config A configures component B |
| `REFERENCES_FILE` | File A references File B |
| `MENTIONS` | Doc comment A mentions code B |
| `FILE_CHANGES_WITH` | File A changes together with File B |
| `SIMILAR_TO` | Symbol A is similar to Symbol B |
| `SEMANTICALLY_RELATED` | Symbol A is semantically related to Symbol B |
| `CONTAINS_FILE` | Folder A contains File B |
| `CONTAINS_FOLDER` | Folder A contains Folder B |
| `INFRA_MAPS` | K8s Service A maps to workload B |
| `DEPENDS_ON` | Chart/manifest A depends on B |
| `DEPLOYS` | Deployment A puts B on cluster |
| `CONNECTS_TO` | Workload A connects to Service B |

## Schema Examples (JSON-like)

### code_index (graph nodes)
```json
{
  "entry_id": "code_001",
  "file_path": "src/main.py",
  "symbol_name": "func_a",
  "symbol_type": "function",
  "label": "Function",
  "qualified_name": "src.main.func_a",
  "line_number": 10,
  "file_hash": "abc123",
  "actor": "agent-a"
}
```

### code_edges (typed edges)
```json
{
  "edge_id": "edge_001",
  "source_id": "code_001",
  "target_id": "code_002",
  "edge_type": "CALLS",
  "confidence": 0.95,
  "line_number": 15,
  "actor": "agent-a"
}
```

### adrs (architecture decisions)
```json
{
  "adr_id": "adr_001",
  "title": "Use embedded hakodb instead of MCP",
  "status": "accepted",
  "rationale": "No MCP server needed, Python stdlib only",
  "consequences": "Simpler deployment, no external process",
  "created_at": "2026-10-29T08:00:00Z",
  "actor": "agent-a"
}
```

### traces (execution traces)
```json
{
  "trace_id": "trace_001",
  "timestamp": "2026-10-29T08:05:00Z",
  "span_id": "span_abc",
  "parent_span_id": null,
  "operation": "http_request",
  "service": "api-gateway",
  "duration_ms": 120,
  "actor": "agent-a"
}
```

### projects (project lifecycle)
```json
{
  "project_name": "bimbingan",
  "root_path": "/home/web/bimbingan",
  "indexed_at": "2026-10-29T08:00:00Z",
  "node_count": 1500,
  "edge_count": 3200,
  "actor": "agent-a"
}
```

## Collections (15 total — 11 from US7 + 4 new)

| Collection | Purpose | Primary Entity |
|------------|---------|---------------|
| `sessions` | Agent session history | Session |
| `events` | Append-only action log | Event |
| `decisions` | Architecture decisions | Decision |
| `findings` | Codebase findings, bugs, patterns | Finding |
| `code_index` | File/symbol index (graph nodes) | CodeNode |
| `code_edges` | Typed edges between code nodes | CodeEdge |
| `tasks` | Task tracking with target + DoD | Task |
| `context_cache` | TTL-cached context summaries | ContextCacheEntry |
| `skills` | Reusable skill patterns | Skill |
| `lessons_learned` | Lessons from failures | — |
| `revisions` | Immutable document revision history | Revision |
| `adrs` | Architecture Decision Records | ArchitectureDecision |
| `traces` | Execution trace entries | TraceEntry |
| `projects` | Indexed project lifecycle | Project |
| `softdel` | Soft-delete tracking | — |

## Index Coverage (`.hakoagent/_indices/coverage.json`)

Extended from US6 with graph-specific coverage:

```json
{
  "src/main.py": {
    "indexed": true,
    "last_indexed_at": "2026-10-29T08:00:00Z",
    "coverage_gaps": [],
    "source_fallback": false,
    "node_count": 5,
    "edge_count": 8,
    "edge_types": ["CALLS", "IMPORTS", "DEFINES"]
  },
  "src/legacy.py": {
    "indexed": false,
    "last_indexed_at": null,
    "coverage_gaps": ["symbols", "dependencies", "edge_types"],
    "source_fallback": true,
    "node_count": 0,
    "edge_count": 0,
    "edge_types": []
  }
}
```

Index kinds supported: `secondary`, `fts`, `composite`, `vector`, `unique`, `sparse`, `graph` (new — for code_edges)

## State Transitions

| Entity | Transitions |
|--------|-------------|
| CodeNode | `created` → `indexed` → `stale` (re-index needed) |
| CodeEdge | `created` → `validated` → `deprecated` (symbol removed) |
| ArchitectureDecision | `proposed` → `accepted` → `rejected` → `superseded` |
| Project | `created` → `indexed` → `deleted` |
| Event | append-only (create only; no update/delete) |
| Revision | immutable (create only) |

## Validation Rules

- **CodeNode**: `entry_id` must be unique; `qualified_name` must be unique per project
- **CodeEdge**: `edge_type` must be one of the 16+ valid types; `source_id` and `target_id` must reference existing CodeNodes
- **ADR**: `status` must be one of: proposed, accepted, rejected, superseded
- **All graph documents**: `actor` field must be present
- **Cypher query**: Row ceiling 100k enforced; LIMIT recommended for broad queries

## Evidence Tiers (Scout/Verify/Auditor)

| Tier | Depth | Behavior |
|------|-------|----------|
| Scout (Tier 1) | Fast positive lookup | Few graph calls, targeted source checks, provisional results only |
| Verify (Tier 2, default) | Task-directed | Relevant trace directions, exact snippets for material claims |
| Auditor (Tier 3) | Bounded-scope full | Complete pagination, both call directions, explicit unresolved limitations |
