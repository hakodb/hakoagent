# Feature Specification: Auto Codebase Indexing

**Feature Branch**: `002-auto-code-indexing`

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "auto codebase indexing without manual agent indexing"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agent does not need to start indexing manually (Priority: P1)

The system automatically detects codebase changes and runs indexing without the agent calling `hakoagent index` manually. Indexing happens incrementally whenever files are added, changed, or deleted.

**Why this priority**: This is the core of the auto indexing feature — it reduces agent burden and keeps code_index always up-to-date without manual intervention.

**Independent Test**: Can be tested independently by modifying a file in the repository and then verifying that code_index has been updated automatically without the agent calling the index command.

**Acceptance Scenarios**:

1. **Given** the system is initialized, **When** the agent creates a new file in the repository, **Then** that new file is automatically indexed into code_index without the agent calling `hakoagent index`
2. **Given** the system is initialized, **When** the agent modifies an existing file, **Then** the code_index entry for that file is updated automatically
3. **Given** the system is initialized, **When** the agent deletes a file from the repository, **Then** the code_index entry for that file is removed automatically

---

### User Story 2 - Incremental indexing without reprocessing the entire codebase (Priority: P2)

The system only processes files changed since the last indexing, not the whole codebase from scratch. This keeps performance good even for large codebases.

**Why this priority**: Important for scalability — a large codebase must not cause slow indexing every time there is a small change.

**Independent Test**: Can be tested by measuring the indexing time for a single changed file compared to indexing the entire codebase.

**Acceptance Scenarios**:

1. **Given** the codebase was indexed previously, **When** one file is changed, **Then** the indexing time for that single file is far faster than re-indexing the whole codebase
2. **Given** many files are changed at once, **Then** only the changed files are processed, not the whole codebase

---

### User Story 3 - Agent receives a notification when indexing finishes (Priority: P3)

Every time automatic indexing finishes, the agent receives a concise notification about what was indexed and whether there were errors.

**Why this priority**: Gives the agent visibility into code_index status without manual checking.

**Independent Test**: Can be tested by triggering a file change and then verifying that the indexing notification appears.

**Acceptance Scenarios**:

1. **Given** automatic indexing is running, **When** indexing finishes, **Then** the agent receives a concise notification (number of files indexed, success/error status)
2. **Given** indexing fails on one file, **Then** the agent receives an error notification for that file without other files' indexing being stopped

---

### Edge Cases

- Files with unsupported extensions (not source code) → skipped during indexing
- Files that are too large → skipped or partially indexed
- Directories that must be ignored (node_modules, .git, target, etc.) → not indexed
- Connection lost while indexing is running → indexing resumes from the latest point when back online
- Files with special characters in their names → still indexed safely

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST automatically detect file changes in the repository without the agent calling the index command manually. At session startup, codebase scanning runs as a background thread within the same agent process (no separate process needed). If the database does not exist yet, a full scan is performed; if it does exist, it is verified and only changed files are updated.
- **FR-002**: The system MUST perform incremental indexing — processing only files changed since the last indexing
- **FR-003**: The system MUST store indexing results in the `code_index` collection in HakoDB
- **FR-004**: The system MUST ignore irrelevant directories and files (node_modules, .git, target, build output, etc.)
- **FR-005**: The system MUST notify the agent when automatic indexing completes or fails
- **FR-006**: The system MUST handle deleted files by removing their related code_index entries
- **FR-007**: The system MUST handle new files by creating new code_index entries
- **FR-008**: The system MUST handle modified files by updating their existing code_index entries
- **FR-009**: The system MUST contain no references to external tools such as hakoagent in any code or documentation
- **FR-010**: The system MUST store all hakoagent-related files under the `.hakoagent/` directory or the project root

### Key Entities *(include if feature involves data)*

- **CodeIndexEntry**: A code index entry with entry_id, file_path, symbol_name, symbol_type, dependencies, line_number, last_indexed_at, file_hash
- **FileChange**: A file change record with change_id, file_path, change_type (created/modified/deleted), timestamp, indexed_status
- **IndexingRun**: An indexing session record with run_id, started_at, ended_at, files_processed, files_indexed, errors, status

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The agent does not need to call `hakoagent index` manually to keep code_index up-to-date
- **SC-002**: Incremental indexing time for one changed file < 5 seconds
- **SC-003**: 100% of relevant source code files are indexed in code_index
- **SC-004**: 0 code_index entries for files deleted from the repository
- **SC-005**: The agent receives a notification after every automatic indexing session completes
- **SC-006**: 0 references to "hakoagent" found across all source files, documentation, and project configuration

## Assumptions

- A file system watcher is available on the target platforms (Linux, macOS, Windows)
- The agent has permission to read files in the repository
- The HakoDB database is initialized before automatic indexing runs
- Supported file formats are source code (Rust, Python, JavaScript, TypeScript, Go, etc.)

## Clarifications

### Session 2026-10-29

- Q: At session startup, is codebase scanning run as a separate background process, or as a thread within the same agent process? → A: Background thread within the same agent process

---
