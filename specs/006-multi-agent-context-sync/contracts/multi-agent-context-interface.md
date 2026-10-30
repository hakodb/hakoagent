# Interface Contract: HakoAgent Multi-Agent Context Sync

**Feature**: 006-multi-agent-context-sync  
**File**: `contracts/multi-agent-context-interface.md`  
**Status**: Draft

HakoAgent exposes a tool calling interface for the harness agent. All return values are in JSON format for easy parsing by the harness agent.

## Tool Contracts

| Tool | Parameter | Return |
|------|-----------|--------|
| `hakoagent.init` | `db_path`, `collections` | `status`, `collections_created` |
| `hakoagent.event_log` | `action`, `target`, `actor`, `session_id`, `change_type`, `metadata` | `event_id`, `timestamp` |
| `hakoagent.recall` | `query`, `limit`, `actor` | `context_results`, `cache_hit` (bool) |
| `hakoagent.cache.stats` | — | `total_hits`, `total_misses`, `eviction_count`, `cache_size` |
| `hakoagent.cache.get` | `query` | `summary`, `cache_hit` (bool) |
| `hakoagent.cache.put` | `query`, `summary`, `ttl_seconds` | `cache_key`, `status` |
| `hakoagent.task.create` | `title`, `target`, `definition_of_done`, `priority`, `actor` | `task_id`, `status` |
| `hakoagent.task.complete` | `task_id`, `dod_verified`, `actor` | `status`, `completed_at` |
| `hakoagent.skill.add` | `name`, `content` (Markdown), `actor` | `skill_id`, `status` |
| `hakoagent.skill.list` | — | `skills_list` (name, id, status, success, failure) |
| `hakoagent.events` | `limit`, `session_id`, `actor` | `events_list` |
| `hakoagent.index` | `root_path` | `indexed_count` |
| `hakoagent.vigilance` | `root_path` | `vigilance_report` |

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

## Multi-Agent Sync Path

All write tools (`event_log`, `task.create`, `skill.add`, etc.) accept an `actor` parameter identifying the originating harness agent. The `actor` is stored in document metadata, enabling any agent to:

1. Read documents written by any other agent through the same HakoDB (`hakoagent recall`)
2. Filter results by a specific actor (`actor` query parameter)
3. Trace the origin of each document via the `actor` field

Multiple agents share context by accessing the same `.hakoagent/hakoagent.db` file on the filesystem. HakoDB handles concurrent access locking internally.

## Append-Only Guard

The `events` collection enforces append-only at the application level: before writing an event, the system checks if `event_id` already exists and rejects the write if it does. Events cannot be overwritten once written.
