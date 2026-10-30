# Tool Calling Interface Contract — HakoAgent

**Feature**: 001-refactor-hakoagent  
**Date**: 2026-10-29  
**Status**: Draft

## Overview

HakoAgent exposes a tool calling interface for harness agents (OpenCode and similar). Each tool has a name prefixed with `hakoagent.`, clearly defined parameters, and a return value in JSON format for easy parsing by the agent.

## Tool List

| Tool | Description | Main Parameters | Return |
|------|-----------|-----------------|--------|
| `hakoagent.init` | Initialize the HakoDB database and all collections | `db_path` (string), `collections` (array of string) | `status` (string), `collections_created` (array) |
| `hakoagent.index` | Scan and index the codebase into `code_index` | `root_path` (string) | `indexed_count` (integer) |
| `hakoagent.recall` | Retrieve context from memory (HNSW + FTS) | `query` (string), `limit` (integer) | `context_results` (array) |
| `hakoagent.skill_list` | List all active skills from `.hakoagent/skills/` | — | `skills_list` (array) |
| `hakoagent.skill_add` | Add a new skill in Markdown format | `name` (string), `content` (string) | `skill_id` (string), `status` (string) |
| `hakoagent.skill_get` | Retrieve details of a specific skill | `skill_id` (string) or `name` (string) | `skill_content` (string, Markdown) |
| `hakoagent.task_list` | View tasks and statuses from the `tasks` collection | — | `tasks_list` (array) |
| `hakoagent.task_create` | Create a new task with target + DoD | `title` (string), `target` (string), `definition_of_done` (string), `priority` (string) | `task_id` (string), `status` (string) |
| `hakoagent.task_complete` | Mark a task complete with DoD verification | `task_id` (string), `dod_verified` (boolean) | `status` (string), `completed_at` (string) |
| `hakoagent.events` | View chronological history from the `events` collection | `limit` (integer), `session_id` (string) | `events_list` (array) |
| `hakoagent.event_log` | Record a new action to the `events` collection (append-only) | `action` (string), `target` (string), `actor` (string), `metadata` (JSON) | `event_id` (string), `timestamp` (string) |
| `hakoagent.vigilance` | Detect overlooked files, regressions, TODOs | `root_path` (string) | `vigilance_report` (object) |
| `hakoagent.finding_save` | Save a finding to the `findings` collection | `content` (string), `finding_type` (string), `file` (string) | `finding_id` (string) |
| `hakoagent.decision_save` | Save a decision to the `decisions` collection | `title` (string), `rationale` (string), `consequences` (string) | `decision_id` (string) |

## Response Format

All responses are in JSON format:

```json
{
  "status": "success|error",
  "data": { ... },
  "error": null | { "code": "...", "message": "..." }
}
```

Example success response:
```json
{
  "status": "success",
  "data": { "event_id": "evt_001", "timestamp": "2026-10-29T08:05:00Z" },
  "error": null
}
```

Example error response:
```json
{
  "status": "error",
  "data": null,
  "error": { "code": "APPEND_ONLY_VIOLATION", "message": "event_id already exists and cannot be overwritten" }
}
```

## Integration Notes

- Tool names are prefixed with `hakoagent.` to avoid conflicts with other tools in the harness agent.
- Parameters must be type-verified before execution.
- Return values are always structured JSON so the AI agent can easily parse them.
- All operations are idempotent except `event_log` (append-only, cannot be repeated with the same event_id).

## Integration Example (Pseudocode)

```python
# Before starting a task
context = hakoagent.recall(query="bagaimana implementasi error handling Rust?", limit=5)
skills = hakoagent.skill_list()

# While working - record every action
hakoagent.event_log(action="code_read", target="src/main.rs", actor="agent")

# Save findings
hakoagent.finding_save(content="Polanya menggunakan Result<T, E>", finding_type="pattern", file="src/main.rs")

# After the task is done - skill extraction
hakoagent.skill_add(name="rust_error_handling", content="...markdown content...")

# Mark the task complete
hakoagent.task_complete(task_id="task_001", dod_verified=True)
```
