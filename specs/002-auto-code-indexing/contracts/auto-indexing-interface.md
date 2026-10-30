# Auto Indexing Interface Contract — HakoAgent

**Feature**: 002-auto-code-indexing  
**Date**: 2026-10-29  
**Status**: Draft

## Overview

Auto Codebase Indexing is exposed as part of the HakoAgent tool calling interface. The background thread runs automatically when `hakoagent init` is executed. There is no dedicated CLI command for auto indexing — everything is integrated into initialization and the file system watcher.

## Tool List

| Tool | Description | Main Parameters | Return |
|------|-----------|-----------------|--------|
| `hakoagent.init` | Initialize the HakoDB database and start the background thread auto indexing | `db_path` (string), `collections` (array of string) | `status` (string), `collections_created` (array), `indexing_started` (boolean) |
| `hakoagent.index` | Force a re-index of the entire codebase (manual override) | — | `indexing_run_id` (string), `status` (string) |
| `hakoagent.recall` | Retrieve context from memory (HNSW + FTS on code_index) | `query` (string), `limit` (integer) | `context_results` (array) |
| `hakoagent.events` | View chronological history including indexing events | `limit` (integer), `session_id` (string) | `events_list` (array) |

## Response Format

All responses are in JSON format:

```json
{
  "status": "success|error",
  "data": { ... },
  "error": null | { "code": "...", "message": "..." }
}
```

Example success response for `hakoagent.init`:
```json
{
  "status": "success",
  "data": {
    "collections_created": ["sessions", "events", "decisions", "findings", "code_index", "tasks", "context_cache", "skills", "lessons_learned"],
    "indexing_started": true
  },
  "error": null
}
```

Example success response for `hakoagent.recall`:
```json
{
  "status": "success",
  "data": {
    "context_results": [
      {
        "file_path": "src/error_handling.rs",
        "symbol_name": "handle_error",
        "symbol_type": "function",
        "relevance_score": 0.95
      }
    ]
  },
  "error": null
}
```

## Integration Notes

- The background thread starts automatically when `hakoagent.init` is executed
- The file system watcher monitors changes in real time
- Every indexing event is recorded in the `events` collection (append-only)
- An error on one file does not stop indexing of other files
- A concise notification is sent to the agent after every indexing session finishes

## Integration Example (Pseudocode)

```python
# Initialize HakoAgent (background thread auto indexing starts automatically)
result = hakoagent.init(db_path="./.hakoagent/hakoagent.db", collections="all")
print(f"Indexing started: {result['data']['indexing_started']}")

# The agent works, files change in the background
# The background thread automatically detects and indexes them

# Retrieve context from code_index
context = hakoagent.recall(query="error handling pattern", limit=5)

# View indexing history
events = hakoagent.events(limit=10)
```
