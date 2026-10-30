# Feature Specification: Refactor HakoAgent to Constitution

**Feature Branch**: `001-refactor-hakoagent`

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "refactor hakoagent according to the latest constitution"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agent uses HakoAgent tool calling to manage memory and skills (Priority: P1)

The AI agent in the harness (OpenCode) can call HakoAgent tools to save events, search context, create tasks, and manage skills in Markdown format, all through a consistent and measurable interface.

**Why this priority**: This is the core of the constitution — the agent must be able to interact with HakoDB memory and skills through easy-to-use tool calling, without references to external tools such as hakoagent.

**Independent Test**: Can be tested independently by calling each HakoAgent tool (init, recall, event_log, skill_add, task_create, etc.) and verifying that files under `.hakoagent/` are created or updated correctly.

**Acceptance Scenarios**:

1. **Given** the `.hakoagent/` directory does not exist yet, **When** the agent calls `hakoagent.init`, **Then** the `.hakoagent/` directory and the `hakoagent.db` database are created with all 9 collections
2. **Given** the agent has completed a task, **When** the agent calls `hakoagent.event_log` with an action and target, **Then** the event is appended to the `events` collection with a timestamp and cannot be overwritten
3. **Given** there is a new skill extracted from a task, **When** the agent calls `hakoagent.skill_add` with Markdown content, **Then** a new skill file is created under `.hakoagent/skills/` in Markdown format
4. **Given** the agent wants to search context, **When** the agent calls `hakoagent.recall` with a query, **Then** relevant context results are returned within the target time

---

### User Story 2 - Agent saves and retrieves skills in Markdown format (Priority: P2)

Every success pattern or lesson learned from tasks is saved as a Markdown skill file under `.hakoagent/skills/`, searchable, and reusable for similar tasks in the future.

**Why this priority**: The Self Skill Improvement principle requires skills to be stored in a format that is easy to read, edit, and version control. Markdown was chosen because it needs no special parser.

**Independent Test**: Can be tested by creating a Markdown skill file, then finding it via `hakoagent.skill_list` or `hakoagent.skill_get`, and verifying the returned content.

**Acceptance Scenarios**:

1. **Given** the agent extracts a success pattern from a task, **When** the agent saves the skill as a Markdown file under `.hakoagent/skills/`, **Then** the file has metadata (skill_id, name, status, tags, success_count, failure_count) and code examples
2. **Given** there are multiple active skills, **When** the agent calls `hakoagent.skill_list`, **Then** all active skills are listed with their names and success/failure counts
3. **Given** a specific skill is needed, **When** the agent calls `hakoagent.skill_get` with a skill_id, **Then** the full skill content in Markdown format is returned

---

### User Story 3 - Agent tracks tasks with measurable targets and DoD (Priority: P2)

Every task the agent works on has a target and Definition of Done recorded in the `tasks` collection, so progress can be verified and stays consistent across LLM models.

**Why this priority**: The Clear Target principle ensures every task has a measurable, unambiguous goal, supporting consistency across models.

**Independent Test**: Can be tested by creating a new task via `hakoagent.task_create`, then verifying via `hakoagent.task_list` that the target and DoD are recorded correctly.

**Acceptance Scenarios**:

1. **Given** the agent is about to start a new task, **When** the agent calls `hakoagent.task_create` with title, target, and definition_of_done, **Then** a new task is created in the `tasks` collection with status "todo"
2. **Given** a task has been completed, **When** the agent calls `hakoagent.task_complete` with dod_verified=true, **Then** the task status changes to "done" and the completion date is recorded
3. **Given** there are unfinished tasks, **When** the agent calls `hakoagent.task_list`, **Then** all tasks with status "todo" or "in-progress" are listed

---

### User Story 4 - Agent detects regressions and overlooked files (Priority: P3)

The Vigilance Checker automatically detects files that were changed but not tested, untouched TODOs, and regressions against constitution principles.

**Why this priority**: The Vigilance principle helps maintain code quality and constitution compliance without excessive manual intervention.

**Independent Test**: Can be tested by running `hakoagent.vigilance` on the project directory and verifying the generated report.

**Acceptance Scenarios**:

1. **Given** there is a file that was changed but has no corresponding test, **When** the agent runs `hakoagent.vigilance`, **Then** that file is listed in the unused files report
2. **Given** there are TODO or FIXME comments in source code, **When** the agent runs `hakoagent.vigilance`, **Then** all TODO items are listed with file location and line numbers
3. **Given** the constitution exists at `.specify/memory/constitution.md`, **When** the agent runs `hakoagent.vigilance`, **Then** regression checks against constitution principles are reported (e.g.: whether the constitution still exists, whether the events collection is available)

---

### Edge Cases

- The agent calls a tool with empty or invalid parameters → the system returns an error with a clear message
- The HakoDB database already exists from a previous initialization → initialization does not overwrite existing data
- A skill with the same name already exists → the system issues a warning or appends a suffix
- The `.hakoagent/` directory is not writable → a clear file permission error
- A recall query matches no documents → an empty result with an informative message

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a tool calling interface for the agent harness with names prefixed `hakoagent.`
- **FR-002**: The system MUST store all memory data in a single HakoDB database at `.hakoagent/hakoagent.db`
- **FR-003**: The system MUST have 9 collections: sessions, events, decisions, findings, code_index, tasks, context_cache, skills, lessons_learned
- **FR-004**: The system MUST store every agent action as an append-only event in the `events` collection with a timestamp. Append-only enforcement is done at the application level: the system checks whether `event_id` already exists before writing, and rejects overwrite operations.
- **FR-005**: The system MUST store skills as Markdown files under `.hakoagent/skills/`, not in YAML or JSON format
- **FR-006**: The system MUST have every task carry a `target` and `definition_of_done` that are defined and measurable
- **FR-007**: The system MUST provide a `hakoagent.recall` tool to search context via HNSW + FTS
- **FR-008**: The system MUST provide a `hakoagent.vigilance` tool to detect regressions, overlooked files, and TODOs
- **FR-009**: The system MUST contain no references to external tools such as hakoagent in any code or documentation
- **FR-010**: The system MUST store all hakoagent-related files under the `.hakoagent/` directory or the project root

### Key Entities *(include if feature involves data)*

- **Event**: An agent action recorded with event_id, timestamp, session_id, actor, action, target, change_type, metadata
- **Session**: Agent session history with session_id, started_at, ended_at, summary, status, model_used
- **Task**: A task with task_id, title, target, definition_of_done, priority, status, dod_verified
- **Skill**: A success pattern in Markdown format with skill_id, name, description, context_tags, success_count, failure_count, status
- **Finding**: A codebase finding with finding_id, content, finding_type, file, event reference
- **Decision**: An architecture decision with decision_id, title, rationale, consequences, event reference
- **CodeIndex**: A code index entry with entry_id, file_path, symbol_name, symbol_type, dependencies

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The agent can complete a full task cycle (init → recall → event_log → task_create → skill_add → task_complete) in under 30 seconds
- **SC-002**: 100% of tasks marked complete have a filled-in and verified `definition_of_done`
- **SC-003**: 0 references to "hakoagent" found across all source files, documentation, and project configuration
- **SC-004**: 100% of skills are stored as Markdown files (`.md`) under `.hakoagent/skills/`
- **SC-005**: Every event written to the `events` collection has an ISO 8601 timestamp and cannot be overwritten
- **SC-006**: HakoAgent tool calling can be discovered and invoked by the harness agent without complex additional configuration

## Assumptions

- The agent harness (OpenCode) supports invoking tools with configurable names
- The HakoDB database can be built and run as an embedded library without an external server
- The Rust toolchain is available to build the HakoAgent core
- The project directory has write permission to create `.hakoagent/`
- Markdown format is sufficient to represent skill metadata and code examples
- All agent interactions are recorded as events automatically without manual intervention

## Clarifications

### Session 2026-10-29

- Q: How is the append-only enforcement mechanism on the events collection implemented technically? → A: Application-level guard (code checks event_id before write)

---
