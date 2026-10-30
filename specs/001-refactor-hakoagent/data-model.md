# Data Model — Refactor HakoAgent to Constitution

**Feature**: 001-refactor-hakoagent  
**Date**: 2026-10-29  
**Status**: Draft

## Entities

### Event

An agent action recorded chronologically in the `events` collection.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| event_id | string | Unique event ID | Must be unique, must not be overwritten |
| timestamp | string (ISO 8601) | When the event occurred | ISO 8601 format |
| session_id | string | Reference to a session | Must match a valid session_id |
| actor | string | Actor performing the action (e.g.: "hakoagent") | Must not be empty |
| action | string | Type of action (e.g.: "code_read", "task_complete") | Must not be empty |
| target | string | Target of the action (e.g.: file path, collection) | Must not be empty |
| change_type | string | Change type (e.g.: "read", "write", "delete") | Must not be empty |
| metadata | JSON | Optional additional data | May be empty |

**Constraint**: Append-only. event_id cannot be overwritten. The system checks whether event_id exists before writing (application-level guard).

### Session

Agent session history in the `sessions` collection.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| session_id | string | Unique session ID | Must be unique |
| started_at | string (ISO 8601) | When the session started | ISO 8601 format |
| ended_at | string (ISO 8601) | When the session ended | ISO 8601 format, may be null |
| summary | string | Session summary | May be empty |
| status | string | Session status (e.g.: "active", "completed") | Must not be empty |
| model_used | string | LLM model used | May be null |
| task_ids | array of string | List of task_id within the session | Must be an array |

### Task

A task the agent works on in the `tasks` collection.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| task_id | string | Unique task ID | Must be unique |
| title | string | Task title | Must not be empty |
| description | string | Task description | Must not be empty |
| target | string | Task goal target | Must not be empty (Clear Target) |
| definition_of_done | string | Measurable completion criteria | Must not be empty (Clear Target) |
| priority | string | Priority (P1, P2, P3) | Must be one of P1/P2/P3 |
| status | string | Status (todo, in-progress, done, blocked) | Must be one of the valid values |
| story_id | string | Reference to a user story | May be null |
| dependencies | array of string | List of task_id this task depends on | Must be an array |
| created_at | string (ISO 8601) | When the task was created | ISO 8601 format |
| completed_at | string (ISO 8601) | When the task was completed | ISO 8601 format, may be null |
| dod_verified | boolean | Whether the DoD has been verified | Default false |
| model_used | string | LLM model used | May be null |

**State transitions**: todo → in-progress → done (if dod_verified=true) / blocked

### Skill

A success pattern extracted from tasks, stored as a Markdown file under `.hakoagent/skills/`.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| skill_id | string | Unique skill ID | Must be unique |
| name | string | Skill name | Must not be empty |
| description | string | Skill description | Must not be empty |
| context_tags | array of string | Context tags for retrieval | Must be an array |
| success_count | integer | Number of successes | Default 0 |
| failure_count | integer | Number of failures | Default 0 |
| last_used | string (ISO 8601) | Last time used | May be null |
| example_code | string | Code example | May be null |
| status | string | Status (active, deprecated, archived) | Must be one of the valid values |

**Format**: Markdown file (`.md`), not YAML or JSON.

### Finding

A codebase finding in the `findings` collection.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| finding_id | string | Unique finding ID | Must be unique |
| collection | string | Collection where the finding was discovered | Must not be empty |
| content | string | Finding content | Must not be empty |
| finding_type | string | Finding type (bug, pattern, error, note) | Must not be empty |
| file | string | Related file | May be null |
| event_id | string | Reference to the originating event | May be null |

### Decision

An architecture decision in the `decisions` collection.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| decision_id | string | Unique decision ID | Must be unique |
| title | string | Decision title | Must not be empty |
| rationale | string | Decision rationale | Must not be empty |
| consequences | string | Decision consequences | Must not be empty |
| event_id | string | Reference to the originating event | May be null |
| status | string | Status (active, superseded) | Must be one of the valid values |

### CodeIndex

A code index entry in the `code_index` collection.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| entry_id | string | Unique entry ID | Must be unique |
| file_path | string | File path | Must not be empty |
| symbol_name | string | Symbol name | Must not be empty |
| symbol_type | string | Symbol type (function, struct, trait, module, etc.) | Must not be empty |
| dependencies | array of string | List of dependencies | Must be an array |
| line_number | integer | Line number | May be null |

### ContextCacheEntry

A context cache entry in the `context_cache` collection.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| cache_key | string | Unique cache key | Must be unique |
| query | string | Original query | Must not be empty |
| summary | string | Summary of search results | Must not be empty |
| source_documents | array of string | List of source documents | Must be an array |
| created_at | string (ISO 8601) | When the entry was created | ISO 8601 format |
| ttl_seconds | integer | Expiration time in seconds | Must be > 0 |
| hit_count | integer | Number of times accessed | Default 0 |

### Lesson

A lesson from failures in the `lessons_learned` collection.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| lesson_id | string | Unique lesson ID | Must be unique |
| title | string | Lesson title | Must not be empty |
| description | string | Lesson description | Must not be empty |
| failure_context | string | Context of the failure | Must not be empty |
| remediation | string | Follow-up remediation action | Must not be empty |
| tags | array of string | Lesson tags | Must be an array |
| status | string | Status (active, resolved) | Must be one of the valid values |

## Relationships

- Session 1:N Event (one session can have many events)
- Task N:1 Session (one task relates to one session)
- Event N:1 Session (one event relates to one session)
- Finding N:1 Event (a finding refers to one originating event)
- Decision N:1 Event (a decision refers to one originating event)

## Validation Rules

1. **Event append-only**: Before writing an event, the system checks whether event_id already exists. If it does, the operation is rejected with an error.
2. **Task completeness**: A task cannot be marked complete if `definition_of_done` is empty or `dod_verified` is false.
3. **Skill uniqueness**: skill_id must be unique within the `.hakoagent/skills/` directory.
4. **Required fields**: All fields marked "Must not be empty" must be filled at create time.

## State Transitions

| Entity | From | To | Condition |
|--------|------|-----|-----------|
| Task | todo | in-progress | Agent starts working on the task |
| Task | in-progress | done | Task completed and dod_verified=true |
| Task | in-progress | blocked | Task blocked by dependencies or issues |
| Skill | active | deprecated | Skill no longer recommended |
| Skill | deprecated | archived | Skill unused for a certain period |
| Skill | active | archived | Skill archived immediately (no longer relevant) |
