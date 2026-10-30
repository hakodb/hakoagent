# Feature Specification: HakoAgent Memory, Context & History System (Non-MCP, Embedded Hakodb)

**Feature Branch**: `007-hakodb-memory-context-history`

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "assess opencode addon/skill in /home/web account related to memory mcp. has not related to hakobackend since current project use embedded hakodb. the mcp implemented in /home/web/bimbingan and used by opencode agent in that project. re-analyze and re-write our plan without hakobackend."

**Reference**: `/home/web/.claude/skills/codebase-memory/SKILL.md` — Codebase Memory knowledge graph MCP (15 tools: index_repository, index_status, list_projects, delete_project, search_graph, search_code, trace_path, detect_changes, query_graph, get_graph_schema, get_code_snippet, get_architecture, check_index_coverage, manage_adr, ingest_traces; evidence tiers Scout/Verify/Auditor). Adapted to **Python-only, non-MCP, embedded hakodb** — no MCP server, no external plugin.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agent writes memory events to embedded hakodb via FFI (Priority: P1)

A harness agent stores session, event, decision, finding, task, skill, and code_index documents to the embedded hakodb shared library via Python ctypes FFI. Every write is an append-only event with an ISO 8601 timestamp. No MCP server — the prebuilt `libhakodb` `.so` is loaded in-process.

**Why this priority**: Embedded hakodb FFI is the foundation — without reliable read/write, no context efficiency or history system exists.

**Independent Test**: Call `hakoagent.event_log`, verify event appears in `events` collection via `hakoagent events` and `hakoagent.load_doc("events", event_id)`.

**Acceptance Scenarios**:

1. **Given** hakodb library is loaded, **When** agent calls `hakoagent.event_log`, **Then** a new event is appended to `events` with unique `event_id` and ISO 8601 `timestamp`
2. **Given** an event exists with `event_id`, **When** agent writes same `event_id`, **Then** write is rejected (append-only guard)
3. **Given** multiple collections, **When** agent writes to each, **Then** documents stored in correct collection via FFI

---

### User Story 2 - Agent retrieves context efficiently to reduce LLM endpoint calls (Priority: P1)

A harness agent queries relevant context from hakodb collections using `hakoagent recall` with TF-IDF + cosine similarity, plus TTL-based `context_cache` tracking `llm_calls_saved`. Context efficiency directly reduces LLM token costs — the core cost-saving goal.

**Why this priority**: Context efficiency saves LLM model cost and boosts agent effectiveness — the distinguishing value of this feature.

**Independent Test**: Write a document to `skills`/`findings`, run `hakoagent recall <query>`, verify document returned. Run same query twice within TTL, verify second call comes from cache (no LLM call).

**Acceptance Scenarios**:

1. **Given** documents exist, **When** agent calls `hakoagent recall <query>`, **Then** relevant documents returned ranked by similarity
2. **Given** same query twice within TTL, **When** second call made, **Then** result from `context_cache` without LLM endpoint call
3. **Given** cache entry expired, **When** query repeated, **Then** fresh search performed, cache updated
4. **Given** context efficiency target, **When** measuring LLM calls per task, **Then** endpoint calls reduced by ≥ N% vs no-cache baseline

---

### User Story 3 - Agent maintains full immutable history across sessions (Priority: P1)

Each agent session tracked with `started_at`, `ended_at`, `status`, `model_used`. Every significant action logged as append-only event. Immutable document revisions preserved on update (mirroring `posts_revisions` pattern — revisions are immutable snapshots). History persists across sessions in hakodb.

**Why this priority**: History provides context continuity — agents don't repeat work, can learn from prior sessions, boosting effectiveness.

**Independent Test**: Start session, perform actions across multiple invocations, verify `hakoagent events` shows all actions chronologically with timestamps. Modify a document, verify previous version preserved as immutable revision.

**Acceptance Scenarios**:

1. **Given** no active session, **When** agent first action, **Then** new session auto-created with `started_at`, `status: "active"`
2. **Given** active session across invocations, **When** agent calls `event_log`, **Then** all events share `session_id`, monotonically increasing timestamps
3. **Given** session ended, **When** agent checks events, **Then** session `ended_at` set, `status: "ended"`
4. **Given** document updated, **When** new version written, **Then** previous version preserved as immutable revision in `revisions` collection
5. **Given** revision exists, **When** agent attempts to modify it, **Then** write rejected (revisions immutable)

---

### User Story 4 - Agent traces codebase relationships like MCP knowledge graph (Priority: P1)

A harness agent traces codebase relationships (who calls what, dependencies, impact analysis) using graph traversal over `code_index` — adapted from MCP `trace_path` (inbound/outbound/both), `search_graph` (name patterns), and `detect_changes`. Implemented with embedded hakodb BFS/Dijkstra over `code_index` dependencies.

**Why this priority**: The MCP codebase-memory skill's core value is structural code queries — adapting it to embedded hakodb gives the same capability without an MCP server.

**Independent Test**: Index a codebase, run `hakoagent graph trace <symbol> outbound <depth>`, verify all reachable nodes found. Run `hakoagent graph shortest-path <from> <to>`, verify shortest dependency chain.

**Acceptance Scenarios**:

1. **Given** codebase indexed, **When** agent traces symbol outbound, **Then** all nodes reachable via dependencies returned
2. **Given** two symbols, **When** agent finds shortest path, **Then** shortest dependency chain returned
3. **Given** file changed, **When** agent runs impact analysis, **Then** all dependents (blast radius) reported
4. **Given** query by name pattern, **When** agent searches graph, **Then** matching symbols/files returned

---

### User Story 5 - Multi-agent context sharing via shared hakodb file (Priority: P2)

Multiple harness agents share context through a shared hakodb file: one agent writes, others read via `hakoagent recall`. Each document carries `actor` field identifying originating agent. No MCP — filesystem-level sharing.

**Why this priority**: Enables team-wide context sharing — agents build on each other's work without redundant LLM calls.

**Independent Test**: Agent A writes finding with `actor: "agent-a"`. Agent B (separate process) runs `hakoagent recall` and sees agent-A's finding.

**Acceptance Scenarios**:

1. **Given** agent-A writes document with `actor`, **When** agent-B recalls, **Then** agent-A's document appears with `actor` attribution
2. **Given** two agents write concurrently, **When** both complete, **Then** both documents present (no lost writes)
3. **Given** agent-B filters by `actor`, **When** query specifies actor, **Then** only that actor's documents returned

---

### User Story 6 - Agent verifies graph index coverage like MCP Auditor tier (Priority: P2)

A harness agent verifies that graph index coverage is complete for evidence paths, with source read/grep fallback for gaps — adapted from MCP `check_index_coverage` and the Scout/Verify/Auditor evidence tiers.

**Why this priority**: The MCP skill's evidence-tier system ensures reliable structural queries — adapting it ensures the hakodb graph is trustworthy for impact analysis.

**Independent Test**: Agent runs coverage check on a set of files, verifies all are indexed, identifies gaps, falls back to source read/grep for uncovered ranges.

**Acceptance Scenarios**:

1. **Given** files indexed, **When** agent checks coverage, **Then** coverage status reported per file
2. **Given** gap in coverage, **When** agent falls back to source grep, **Then** missing information retrieved from source
3. **Given** evidence tier selected (Scout/Verify/Auditor), **When** agent runs verification, **Then** depth matches tier (Scout: provisional, Verify: task-directed, Auditor: bounded-scope full)

---

### User Story 7 - Agent closes the bug fixing loop: finding → task → fix → skill (Priority: P1)

A harness agent logs a bug as a `finding`, spawns a `task` with target + DoD to fix it, verifies the fix, saves an immutable revision, then extracts the bug pattern as a reusable `skill` and a `lessons_learned` entry so the same bug class doesn't recur. This completes the self-improvement loop: find bug → fix bug → learn from bug → store as skill → reuse on similar tasks.

**Why this priority**: Bug fixing is a core agent activity; turning each fix into a reusable skill prevents recurrence and continuously improves agent effectiveness.

**Independent Test**: Log a bug finding, verify a task is created with target+DoD, mark the task complete, verify a revision is saved, then verify a new skill + lessons_learned entry exist.

**Acceptance Scenarios**:

1. **Given** a bug is found, **When** agent logs it as a `finding` (type: bug), **Then** a `task` is created with target and `definition_of_done` for the fix
2. **Given** the fix task is complete (dod_verified=true), **When** agent checks revisions, **Then** an immutable revision of the fixed document is preserved
3. **Given** a fixed bug, **When** agent reflects post-task, **Then** a new `skill` (bug pattern) and `lessons_learned` entry are created
4. **Given** a similar bug arises later, **When** agent queries `skills`, **Then** the prior bug-fix skill is retrieved and applied

---

## Edge Cases

- **Concurrent writes from multiple agents**: Hakodb handles locking at storage layer; Python layer retries on conflict
- **Missing hakodb library**: Falls back gracefully to JSON file storage under `.hakoagent/memory/`
- **Empty query**: `hakoagent recall ""` returns informative message
- **Expired cache**: TTL-expired entries deleted and re-fetched
- **Non-existent collection**: Clear error returned
- **Corrupt JSON document**: Skipped during scan, warning logged
- **LLM endpoint unavailable**: System continues using cached context, with warning
- **Revision immutability**: Revisions cannot be updated or deleted once created
- **Soft-deleted documents**: Excluded from recall, recoverable

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST store agent memory in embedded hakodb via prebuilt shared library (`lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so`) using Python `ctypes` FFI
- **FR-002**: System MUST expose `lib/hakodb.h` C ABI header (v0.20.0, hash-verified) as source of truth for FFI signatures
- **FR-003**: System MUST implement append-only event log — events cannot be overwritten (application-level `event_id` uniqueness guard)
- **FR-004**: System MUST store every event with unique `event_id` and ISO 8601 `timestamp`
- **FR-005**: System MUST support `hakoagent recall <query>` with TF-IDF + cosine similarity across collections
- **FR-006**: System MUST support TTL-based `context_cache` (default 300s) with LRU eviction, tracking `llm_calls_saved`
- **FR-007**: System MUST tag every document with `actor` field identifying originating harness agent
- **FR-008**: System MUST support multi-agent read sharing via shared hakodb file
- **FR-009**: System MUST gracefully fall back to JSON file storage when hakodb library unavailable
- **FR-010**: System MUST NOT reference MCP, Rust, Cargo, or build steps (Python-only, non-MCP, embedded hakodb)
- **FR-011**: System MUST keep all runtime data under `.hakoagent/` or project root
- **FR-012**: System MUST reduce LLM endpoint calls by ≥ N% per task through context cache + efficient retrieval
- **FR-013**: System MUST provide context efficiency metrics (cache hit ratio, LLM calls saved) via `hakoagent cache stats`
- **FR-014**: System MUST support immutable document revisions (history) — previous versions preserved on update
- **FR-015**: System MUST support graph trace (inbound/outbound/both) over `code_index` dependencies
- **FR-016**: System MUST support shortest-path (Dijkstra) between two symbols in codebase
- **FR-017**: System MUST support impact analysis (blast radius: transitive dependents)
- **FR-018**: System MUST support graph index coverage check with source fallback for gaps
- **FR-019**: System MUST support evidence tiers (Scout/Verify/Auditor) for graph verification depth

### Key Entities *(include if feature involves data)*

- **Session**: `session_id`, `started_at`, `ended_at`, `status`, `summary`, `model_used`, `actor`
- **Event**: `event_id`, `timestamp` (ISO 8601), `session_id`, `actor`, `action`, `target`, `change_type`, `metadata`
- **Decision**: `decision_id`, `title`, `rationale`, `consequences`, `event_id` (ref), `actor`
- **Finding**: `finding_id`, `content`, `finding_type`, `file`, `event_id` (ref), `actor`
- **Task**: `task_id`, `title`, `target`, `definition_of_done`, `priority`, `status`, `dod_verified`, `actor`
- **Skill**: `skill_id`, `name`, `description`, `context_tags`, `success_count`, `failure_count`, `status`, `actor`
- **CodeIndex**: `entry_id`, `file_path`, `symbol_name`, `symbol_type`, `dependensi`, `line_number`, `file_hash`, `actor`
- **Revision** (History): `revision_id`, `doc_id`, `doc_collection`, `previous_content`, `new_content`, `changed_by` (actor), `changed_at` (ISO 8601), immutable
- **ContextCacheEntry**: `cache_key`, `query`, `summary`, `source_documents`, `created_at`, `ttl_seconds`, `hit_count`, `llm_calls_saved`
- **IndexCoverage**: `file_path`, `indexed`, `last_indexed_at`, `coverage_gaps`, `source_fallback`

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Single agent write/read via hakodb FFI < 1 second
- **SC-002**: Two separate agents share document through same hakodb file
- **SC-003**: Append-only guard verified — 0 events overwritten on duplicate `event_id`
- **SC-004**: Cache hit ratio ≥ 50% for repeated queries within TTL
- **SC-005**: LLM endpoint calls reduced by ≥ N% per task vs no-cache baseline
- **SC-006**: All 31+ existing `test_hakoagent.py` tests continue to pass
- **SC-007**: 0 references to MCP / Rust / Cargo / build in code or documentation
- **SC-008**: All files stored under `.hakoagent/` or project root
- **SC-009**: Immutable revisions preserved — 0 revisions overwritten/deleted
- **SC-010**: Graph trace (inbound/outbound/both) returns correct nodes
- **SC-011**: Shortest-path returns correct dependency chain
- **SC-012**: Index coverage check reports gaps with source fallback
- **SC-013**: Bug fixing loop verified — finding → task → fix → revision → skill → lessons_learned works end-to-end

---

## Assumptions

- Prebuilt hakodb shared library compatible with running Python (same platform, glibc version)
- Multiple agents share access to same `.hakoagent/` directory and `hakoagent.db` file (filesystem-level, no MCP server)
- Hakodb handles concurrent access locking internally
- Python 3 stdlib only — no external dependencies
- `hakodb.h` header (v0.20.0) accurately reflects exported symbols in prebuilt `.so`
- LLM cost savings measured by counting avoided endpoint calls via cache hits (`llm_calls_saved`)
- Graph trace/shortest-path operate on `code_index` dependency edges produced by `hakoagent index`

---
