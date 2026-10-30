# Feature Specification: HakoAgent Multi-Agent Context Sync

**Feature Branch**: `006-multi-agent-context-sync`

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "build hakoagent an agent memory, context and history system, with hakodb and sync path for multi agent/group context system"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agent writes memory events to HakoDB via real FFI (Priority: P1)

A single harness agent can store session, event, decision, finding, and task documents to HakoDB through the prebuilt `libhakodb` shared library using Python ctypes FFI. Each write is recorded as an append-only event with an ISO 8601 timestamp.

**Why this priority**: This is the core memory capability — without reliable write access to HakoDB via the real FFI library, no multi-agent sync can be built.

**Independent Test**: Call `hakoagent.event_log` with an action and target, then verify the event appears in the `events` collection via `hakoagent events` and `hakoagent.load_doc("events", event_id)`.

**Acceptance Scenarios**:

1. **Given** HakoDB library is loaded, **When** agent calls `hakoagent.event_log`, **Then** a new event is appended to `events` collection with unique `event_id` and ISO 8601 `timestamp`
2. **Given** an event already exists with a given `event_id`, **When** agent attempts to write the same `event_id`, **Then** the write is rejected (append-only guard)
3. **Given** multiple collections, **When** agent writes to `sessions`, `decisions`, `findings`, `tasks`, **Then** each document is stored in the correct collection

---

### User Story 2 - Agent reads context from HakoDB collections (Priority: P1)

A harness agent can query and retrieve context from HakoDB collections (`code_index`, `skills`, `findings`, `decisions`, `events`) using `hakoagent recall` with TF-IDF + cosine similarity vector search, plus TTL-based `context_cache` to avoid redundant lookups.

**Why this priority**: Context retrieval is the read side of memory — agents need to find relevant prior knowledge before acting.

**Independent Test**: Write a document to `skills` or `findings`, then run `hakoagent recall <query>` and verify the document is returned in results.

**Acceptance Scenarios**:

1. **Given** documents exist in `skills` and `findings`, **When** agent calls `hakoagent recall <query>`, **Then** relevant documents are returned ranked by similarity score
2. **Given** the same query is run twice within TTL, **When** the second call is made, **Then** the result comes from `context_cache` without re-searching
3. **Given** a cache entry has expired (TTL elapsed), **When** the query is repeated, **Then** a fresh search is performed and the cache is updated

---

### User Story 3 - Multi-agent context sync path (Priority: P1)

Multiple harness agents (or agent groups) can share context through a sync path: one agent writes events/documents to a shared HakoDB, and other agents can read them via `hakoagent recall`. Each document carries an `actor` field identifying the originating agent, enabling group context awareness.

**Why this priority**: This is the distinguishing feature — enabling a group of agents to operate with shared memory rather than isolated per-agent state.

**Independent Test**: Agent A writes a finding to `findings` with `actor: "agent-a"`. Agent B (separate process/session) runs `hakoagent recall` and sees agent-A's finding in results.

**Acceptance Scenarios**:

1. **Given** agent-A writes a document with `actor` metadata, **When** agent-B queries `hakoagent recall`, **Then** agent-A's document appears in results with its `actor` attribution
2. **Given** two agents write to the same collection concurrently, **When** both writes complete, **Then** both documents are present (no lost writes)
3. **Given** agent-B queries with a filter on `actor`, **When** the query specifies a particular actor, **Then** only documents from that actor are returned

---

### User Story 4 - Agent session and history tracking (Priority: P2)

Each agent session is tracked with `started_at`, `ended_at`, `status`, and `model_used`. Every significant agent action is logged as an append-only event, enabling full history replay and time-travel debugging.

**Why this priority**: Session history provides the audit trail and context continuity needed for multi-agent collaboration.

**Independent Test**: Start a session via `hakoagent`, perform several actions, then verify `hakoagent events` shows all actions in chronological order with timestamps.

**Acceptance Scenarios**:

1. **Given** no active session, **When** agent performs its first action, **Then** a new session is auto-created with `started_at` and `status: "active"`
2. **Given** an active session, **When** agent calls `hakoagent event_log` multiple times, **Then** all events share the same `session_id` and have monotonically increasing timestamps
3. **Given** a session is ended, **When** agent checks `hakoagent events`, **Then** the session's `ended_at` is set and `status` is `"ended"`

---

## Edge Cases

- **Concurrent writes from multiple agents**: Two agents writing to the same collection simultaneously must not corrupt the database; HakoDB handles locking at the storage layer
- **Missing HakoDB library**: If `lib/libhakodb-...so` is absent or unloadable, the system falls back gracefully to JSON file storage under `.hakoagent/memory/`
- **Empty query**: `hakoagent recall ""` returns an informative message rather than crashing
- **Expired cache**: TTL-expired entries are deleted and re-fetched on next query
- **Non-existent collection**: Writing to an unknown collection returns a clear error
- **Corrupt JSON document**: A malformed document in memory collections is skipped during scan with a warning logged

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST store agent memory (sessions, events, decisions, findings, tasks) in HakoDB via the prebuilt shared library (`lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so`) using Python `ctypes` FFI
- **FR-002**: System MUST expose `hk_engine.h` C ABI header (`lib/hakodb.h`, v0.20.0, hash-verified) as the source of truth for FFI function signatures
- **FR-003**: System MUST implement append-only event log — events cannot be overwritten once written (application-level guard checking `event_id` uniqueness)
- **FR-004**: System MUST store every event with a unique `event_id` and ISO 8601 `timestamp`
- **FR-005**: System MUST support `hakoagent recall <query>` with TF-IDF + cosine similarity across `code_index`, `skills`, `findings`, `decisions`, `events` collections
- **FR-006**: System MUST support TTL-based `context_cache` (default 300s) with LRU eviction when cache exceeds 100 entries
- **FR-007**: System MUST tag every stored document with an `actor` field identifying the originating harness agent
- **FR-008**: System MUST support multi-agent read sharing — any agent can read documents written by any other agent through the same HakoDB
- **FR-009**: System MUST gracefully fall back to JSON file storage under `.hakoagent/memory/<collection>/` when the HakoDB library is unavailable
- **FR-010**: System MUST NOT have references to Rust, Cargo, or build steps in code or documentation (Python-only)
- **FR-011**: System MUST keep all runtime data under `.hakoagent/` or project root

### Key Entities *(include if feature involves data)*

- **Session**: `session_id`, `started_at`, `ended_at`, `status`, `summary`, `model_used`, `actor`
- **Event**: `event_id`, `timestamp` (ISO 8601), `session_id`, `actor`, `action`, `target`, `change_type`, `metadata`
- **Decision**: `decision_id`, `title`, `rationale`, `consequences`, `event_id` (reference), `actor`
- **Finding**: `finding_id`, `content`, `finding_type`, `file`, `event_id` (reference), `actor`
- **Task**: `task_id`, `title`, `target`, `definition_of_done`, `priority`, `status`, `dod_verified`, `actor`
- **Skill**: `skill_id`, `name`, `description`, `context_tags`, `success_count`, `failure_count`, `status`, `actor`
- **CodeIndex**: `entry_id`, `file_path`, `symbol_name`, `symbol_type`, `dependensi`, `line_number`, `file_hash`, `actor`
- **ContextCacheEntry**: `cache_key`, `query`, `summary`, `source_documents`, `created_at`, `ttl_seconds`, `hit_count`

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Single agent can write and read back a document via HakoDB FFI in < 1 second
- **SC-002**: Two separate agents can share a document written by one and read by the other through the same HakoDB
- **SC-003**: Append-only guard verified — 0 events overwritten when duplicate `event_id` is attempted
- **SC-004**: Cache hit ratio ≥ 50% for repeated queries within TTL
- **SC-005**: All 31+ existing `test_hakoagent.py` tests continue to pass
- **SC-006**: 0 references to Rust/Cargo/build in code or documentation
- **SC-007**: All files stored under `.hakoagent/` or project root

---

## Assumptions

- The prebuilt HakoDB shared library (`libhakodb-x86_64-unknown-linux-glibc2.28-el8.so`) is compatible with the running Python interpreter (same platform, glibc version)
- Multiple agents share access to the same `.hakoagent/` directory and `hakoagent.db` file (filesystem-level sharing, no network server)
- HakoDB handles concurrent access locking internally; the Python layer does not implement additional distributed locking
- Python 3 stdlib only — no external `ctypes` dependencies beyond what's built-in
- The `hakodb.h` header (v0.20.0) accurately reflects the exported symbols in the prebuilt `.so`

---
