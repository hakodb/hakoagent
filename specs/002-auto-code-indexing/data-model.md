# Data Model — Auto Codebase Indexing

**Feature**: 002-auto-code-indexing  
**Date**: 2026-10-29  
**Status**: Draft

## Entities

### CodeIndexEntry

A code index entry stored in the `code_index` collection of HakoDB.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| entry_id | string | Unique entry ID | Must be unique |
| file_path | string | File path relative to the project root | Must not be empty |
| symbol_name | string | Symbol name (function, class, struct, etc.) | Must not be empty |
| symbol_type | string | Symbol type (function, struct, trait, module, class, method, etc.) | Must not be empty |
| dependencies | array of string | List of imported/used dependencies | Must be an array |
| line_number | integer | Line number of the symbol definition | May be null |
| last_indexed_at | string (ISO 8601) | Last time the file was indexed | ISO 8601 format |
| file_hash | string | SHA-256 hash of the file content | Must not be empty, unique per file_path |

**Constraint**: file_hash is used to detect changes. If the hash is the same, the file does not need re-indexing.

### FileChange

A file change record detected by the file system watcher.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| change_id | string | Unique change ID | Must be unique |
| file_path | string | Path of the changed file | Must not be empty |
| change_type | string | Change type (created/modified/deleted) | Must be one of the valid values |
| timestamp | string (ISO 8601) | When the change was detected | ISO 8601 format |
| indexed_status | string | Indexing status (indexed/skipped/error) | Must be one of the valid values |

**State transitions**: detected → indexed / skipped / error

### IndexingRun

A record of an indexing session performed by the background thread.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| run_id | string | Unique indexing session ID | Must be unique |
| started_at | string (ISO 8601) | When indexing started | ISO 8601 format |
| ended_at | string (ISO 8601) | When indexing finished | ISO 8601 format, may be null |
| files_processed | integer | Number of files processed | Must be >= 0 |
| files_indexed | integer | Number of files successfully indexed | Must be >= 0, <= files_processed |
| errors | array of string | List of errors that occurred | Must be an array |
| status | string | Status (started/completed/failed) | Must be one of the valid values |

**State transitions**: started → completed / failed

## Relationships

- IndexingRun 1:N FileChange (one indexing session can have many file changes)
- FileChange N:1 CodeIndexEntry (one file change can create/update one code_index entry)

## Validation Rules

1. **File hash uniqueness**: file_hash must be unique per file_path. If a file_path already exists with the same hash, it does not need re-indexing.
2. **Change type validity**: change_type must be one of created/modified/deleted.
3. **Indexing status validity**: indexed_status must be one of indexed/skipped/error.
4. **Required fields**: All fields that must not be empty must be filled at create time.

## State Transitions

| Entity | From | To | Condition |
|--------|------|-----|-----------|
| IndexingRun | started | completed | All files processed without fatal errors |
| IndexingRun | started | failed | A fatal error prevents indexing from continuing |
| FileChange | detected | indexed | File successfully indexed into code_index |
| FileChange | detected | skipped | File skipped (unsupported extension, ignored directory, too large) |
| FileChange | detected | error | Error while processing the file |
| CodeIndexEntry | created | updated | File changed, hash differs |
| CodeIndexEntry | updated | deleted | File deleted from the repository |
