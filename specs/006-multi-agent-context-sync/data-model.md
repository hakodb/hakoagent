# Data Model — HakoAgent Multi-Agent Context Sync

**Feature**: 006-multi-agent-context-sync  
**Date**: 2026-10-29  
**Status**: Draft

Entities extracted from the feature specification for the HakoDB-backed agent memory, context, and history system.

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
| **ContextCacheEntry** | `cache_key`, `query`, `summary`, `source_documents`, `created_at`, `ttl_seconds`, `hit_count` | — |

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
  "title": "Implement multi-agent sync",
  "target": "Two agents can read the same document through shared HakoDB",
  "definition_of_done": "Verify via recall from separate agent sessions",
  "priority": "P1",
  "status": "todo",
  "dod_verified": false,
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
  "success_count": 0,
  "failure_count": 0,
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

## Validation Rules

- **Event**: `event_id` must be unique; append-only guard rejects duplicates before write
- **Task**: `target` and `definition_of_done` must not be empty
- **All documents**: `actor` field must be present (multi-agent attribution requirement)
- **ContextCacheEntry**: `cache_key` must be unique; `ttl_seconds` must be > 0

## Collections (9)

| Collection | Purpose | Primary Entity |
|------------|---------|---------------|
| `sessions` | Agent session history | Session |
| `events` | Append-only action log | Event |
| `decisions` | Architecture decisions | Decision |
| `findings` | Codebase findings, bugs, patterns | Finding |
| `code_index` | File/symbol/dependency index | CodeIndex |
| `tasks` | Task tracking with target + DoD | Task |
| `context_cache` | TTL-cached context summaries | ContextCacheEntry |
| `skills` | Reusable skill patterns (Markdown) | Skill |
| `lessons_learned` | Lessons from failures | — |
