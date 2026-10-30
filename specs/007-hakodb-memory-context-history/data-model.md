# Data Model — HakoAgent Memory, Context & History System (Non-MCP, Embedded Hakodb)

**Feature**: 007-hakodb-memory-context-history  
**Date**: 2026-10-29  
**Status**: Draft

Entities extracted from the feature specification, incorporating MCP codebase-memory skill patterns adapted to embedded hakodb.

## Entities

| Entity | Key Attributes | Relationships |
|--------|---------------|---------------|
| **Session** | `session_id`, `started_at`, `ended_at`, `status`, `summary`, `model_used`, `actor` | 1:N with Event (session_id → Event) |
| **Event** | `event_id`, `timestamp` (ISO 8601), `session_id`, `actor`, `action`, `target`, `change_type`, `metadata` | session_id → Session |
| **Decision** | `decision_id`, `title`, `rationale`, `consequences`, `event_id`, `actor` | event_id → Event |
| **Finding** | `finding_id`, `content`, `finding_type`, `file`, `event_id`, `actor` | event_id → Event |
| **Task** | `task_id`, `title`, `target`, `definition_of_done`, `priority`, `status`, `dod_verified`, `actor` | — |
| **Skill** | `skill_id`, `name`, `description`, `context_tags`, `success_count`, `failure_count`, `status`, `actor` | — |
| **CodeIndex** | `entry_id`, `file_path`, `symbol_name`, `symbol_type`, `dependensi`, `line_number`, `file_hash`, `actor` | — |
| **Revision** (History) | `revision_id`, `doc_id`, `doc_collection`, `previous_content`, `new_content`, `changed_by` (actor), `changed_at` (ISO 8601), immutable | doc_id → source document |
| **ContextCacheEntry** | `cache_key`, `query`, `summary`, `source_documents`, `created_at`, `ttl_seconds`, `hit_count`, `llm_calls_saved` | — |
| **IndexCoverage** | `file_path`, `indexed`, `last_indexed_at`, `coverage_gaps`, `source_fallback` | — |

## Schema Examples (JSON-like)

### events (append-only)
```json
{
  "event_id": "evt_abc123",
  "timestamp": "2026-10-29T08:05:00Z",
  "session_id": "sess_xyz789",
  "actor": "agent-a",
  "action": "code_read",
  "target": "src/main.py",
  "change_type": "info",
  "metadata": {"file": "src/main.py"}
}
```

### tasks (with target and DoD)
```json
{
  "task_id": "task_001",
  "title": "Implement memory system",
  "target": "Embedded hakodb memory, context, history work via FFI",
  "definition_of_done": "All 31+ tests pass; context hit ratio >= 50%",
  "priority": "P1",
  "status": "todo",
  "dod_verified": false,
  "actor": "agent-a"
}
```

### context_cache (LLM cost reduction)
```json
{
  "cache_key": "cache_a1b2c3d4",
  "query": "python error handling pattern",
  "summary": "Use try/except with specific exception types, avoid bare except",
  "source_documents": ["skills/skill_001"],
  "created_at": 1793263346.123,
  "ttl_seconds": 300,
  "hit_count": 5,
  "llm_calls_saved": 5
}
```

### revision (immutable history)
```json
{
  "revision_id": "rev_001",
  "doc_id": "doc_abc123",
  "doc_collection": "findings",
  "previous_content": null,
  "new_content": {"content": "buffer overflow in parser", "severity": "high"},
  "changed_by": "agent-a",
  "changed_at": "2026-10-29T08:05:00Z"
}
```

### code_index (graph nodes for trace/shortest-path/impact)
```json
{
  "entry_id": "code_001",
  "file_path": "src/main.py",
  "symbol_name": "func_a",
  "symbol_type": "function",
  "dependensi": ["code_002", "code_003"],
  "line_number": 10,
  "file_hash": "abc123",
  "actor": "agent-a"
}
```

### skills (Markdown file + metadata)
```json
{
  "skill_id": "skill_001",
  "name": "python-error-handling",
  "status": "active",
  "version": 1,
  "created_at": "2026-10-29T08:00:00Z",
  "success_count": 12,
  "failure_count": 1,
  "actor": "agent-a"
}
```

## State Transitions

| Entity | Transitions |
|--------|-------------|
| Session | `active` → `ended` (ended_at set) |
| Task | `todo` → `in-progress` → `done` (dod_verified=true) / `blocked` |
| Skill | `active` → `deprecated` / `archived` |
| Event | append-only (create only; no update/delete) |
| Revision | immutable (create only) |

## Validation Rules

- **Event**: `event_id` must be unique; append-only guard rejects duplicates before write
- **Task**: `target` and `definition_of_done` must not be empty
- **All documents**: `actor` field must be present (multi-agent attribution requirement)
- **ContextCacheEntry**: `cache_key` must be unique; `ttl_seconds` must be > 0
- **Revision**: immutable — cannot be updated or deleted once created

## Collections (11)

| Collection | Purpose | Primary Entity |
|------------|---------|---------------|
| `sessions` | Agent session history | Session |
| `events` | Append-only action log | Event |
| `decisions` | Architecture decisions | Decision |
| `findings` | Codebase findings, bugs, patterns | Finding |
| `code_index` | File/symbol/dependency index (graph nodes) | CodeIndex |
| `tasks` | Task tracking with target + DoD | Task |
| `context_cache` | TTL-cached context summaries (LLM cost reduction) | ContextCacheEntry |
| `skills` | Reusable skill patterns (Markdown) | Skill |
| `lessons_learned` | Lessons from failures | — |
| `revisions` | Immutable document revision history | Revision |
| `softdel` | Soft-delete tracking (deleted_at, recoverable) | — |

## Index Coverage (`.hakoagent/_indices/coverage.json`)

```json
{
  "src/main.py": {"indexed": true, "last_indexed_at": "2026-10-29T08:00:00Z", "coverage_gaps": [], "source_fallback": false},
  "src/utils.py": {"indexed": true, "last_indexed_at": "2026-10-29T08:00:00Z", "coverage_gaps": [], "source_fallback": false},
  "src/legacy.py": {"indexed": false, "last_indexed_at": null, "coverage_gaps": ["symbols", "dependencies"], "source_fallback": true}
}
```

Index kinds supported: `secondary`, `fts`, `composite`, `vector`, `unique`, `sparse`
