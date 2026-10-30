# Tasks: HakoAgent Memory, Context & History System (Non-MCP, Embedded Hakodb)

**Input**: Design documents from `specs/007-hakodb-memory-context-history/` (spec.md, plan.md)

**Prerequisites**: plan.md (required), spec.md (required)

**Organization**: Tasks are grouped by user story (US1-US6) corresponding to the 6 user stories from spec.md.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5, US6)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure per plan.md

- [ ] T001 [P] Verify `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` and `lib/hakodb.h` are present and hash-verified against `lib/SHA256SUMS.txt`
- [ ] T002 [P] Verify Python 3 is available and `test_hakoagent.py` passes (31+ tests baseline)
- [ ] T003 [P] Confirm `.hakoagent/_indices/` directory structure (definitions.json, coverage.json, ram_indexes.bin, index.log, snapshots/)
- [ ] T004 [P] Verify all Phase 1 docs present: spec.md, plan.md, research.md, data-model.md, contracts/hakodb-memory-context-interface.md, quickstart.md

---

## Phase 2: User Story 1 - Agent Memory Write via Real Hakodb FFI (Priority: P1) 🎯 MVP

**Goal**: Agent can store session, event, decision, finding, task documents to hakodb via ctypes FFI with append-only guard

**Independent Test**: Call `hakoagent.event_log`, verify event appears in `events` collection via `hakoagent events` and `hakoagent.load_doc`

### Tests for User Story 1 (write FIRST, ensure FAIL before implementation)

- [ ] T005 [P] [US1] Unit test: `hk_engine_put` calls `hk_engine_insert_json` with correct argtypes (c_void_p, c_char_p, c_char_p, c_char_p)
- [ ] T006 [P] [US1] Unit test: `hk_engine_get` calls `hk_engine_get_json` with c_void_p restype and `ctypes.string_at()` + `hk_string_free`
- [ ] T007 [P] [US1] Unit test: append-only guard rejects duplicate `event_id` in `events` collection
- [ ] T008 [P] [US1] Unit test: event has ISO 8601 `timestamp` and unique `event_id`

### Implementation for User Story 1

- [ ] T009 [US1] Update `hakoagent` FFI wrapper: `hk_engine_put` uses `hk_engine_insert_json` (not `hk_engine_insert` with 4 strings)
- [ ] T010 [US1] Update `hakoagent` FFI wrapper: `hk_engine_get` uses `hk_engine_get_json` with `c_void_p` restype + `string_at()` + `hk_string_free`
- [ ] T011 [US1] Add `actor` parameter to `hakoagent.event_log` and store in event metadata
- [ ] T012 [US1] Add append-only guard: check `event_id` uniqueness before writing to `events` collection
- [ ] T013 [US1] Ensure `save_doc`/`load_doc`/`delete_doc` dual-write to both JSON files and Hakodb FFI
- [ ] T014 [US1] Integration test: write event → read back via `load_doc` → verify content matches

**Checkpoint**: User Story 1 complete — single agent can write and read memory via real Hakodb FFI

---

## Phase 3: User Story 2 - Context Retrieval & Efficiency (Priority: P1)

**Goal**: `hakoagent recall` with TF-IDF + cosine similarity + TTL-based `context_cache` tracking `llm_calls_saved`

**Independent Test**: Write document to `skills`/`findings`, run `hakoagent recall <query>`, verify document returned. Run same query twice within TTL, verify second is cache hit.

### Tests for User Story 2

- [ ] T015 [P] [US2] Unit test: `cache_get_internal` returns None for TTL-expired entries
- [ ] T016 [P] [US2] Unit test: `cache_put_internal` stores entry with `created_at`, `ttl_seconds`, `hit_count`, `llm_calls_saved`
- [ ] T017 [P] [US2] Unit test: `_vector_search_collection` returns results ranked by cosine similarity
- [ ] T018 [P] [US2] Unit test: second identical query within TTL returns cache hit (llm_calls_saved incremented)

### Implementation for User Story 2

- [ ] T019 [US2] Verify `hakoagent recall` searches `code_index`, `skills`, `findings`, `decisions`, `events` collections
- [ ] T020 [US2] Verify `hakoagent recall` checks `context_cache` first (TTL-valid) before vector search
- [ ] T021 [US2] Verify `hakoagent recall` stores results in `context_cache` with default TTL 300s and `llm_calls_saved=0`
- [ ] T022 [US2] On cache hit, increment `hit_count` and `llm_calls_saved`
- [ ] T023 [US2] `hakoagent cache stats` reports `llm_calls_saved`
- [ ] T024 [US2] Integration test: write skill → recall finds it → second query is cache hit with llm_calls_saved=1

**Checkpoint**: User Story 2 complete — context retrieval with efficiency tracking works

---

## Phase 4: User Story 3 - Immutable Revisions / History (Priority: P1)

**Goal**: Every document update creates an immutable revision in `revisions` collection

**Independent Test**: Modify a document multiple times, verify each revision stored immutably and retrievable by revision ID

### Tests for User Story 3

- [ ] T025 [P] [US3] Unit test: revision created with `revision_id`, `doc_id`, `doc_collection`, `previous_content`, `new_content`, `changed_by`, `changed_at`
- [ ] T026 [P] [US3] Unit test: revision is immutable — cannot be updated or deleted
- [ ] T027 [P] [US3] Unit test: `revision.list` returns revisions in chronological order

### Implementation for User Story 3

- [ ] T028 [US3] Add `revisions` collection — on document update, save previous version as revision before writing new
- [ ] T029 [US3] Add `hakoagent revision.list <doc_id> <doc_collection>` command
- [ ] T030 [US3] Enforce revision immutability — reject updates/deletes to existing revisions
- [ ] T031 [US3] Integration test: update doc → verify revision created → verify revision immutable

**Checkpoint**: User Story 3 complete — immutable revision history works

---

## Phase 5: User Story 4 - Graph Trace / Shortest-Path / Impact (Priority: P1)

**Goal**: Graph traversal over `code_index` — trace (inbound/outbound/both), shortest-path (Dijkstra), impact analysis (blast radius)

**Independent Test**: Index a codebase, run `hakoagent graph trace <symbol> outbound <depth>`, verify all reachable nodes found. Run `hakoagent graph shortest-path <from> <to>`, verify shortest chain.

### Tests for User Story 4

- [ ] T032 [P] [US4] Unit test: BFS traversal over `code_index` dependencies returns correct nodes
- [ ] T033 [P] [US4] Unit test: Dijkstra shortest-path returns correct dependency chain
- [ ] T034 [P] [US4] Unit test: impact analysis returns all transitive dependents (blast radius)
- [ ] T035 [P] [US4] Unit test: graph cycle handled (visited set prevents infinite loop)

### Implementation for User Story 4

- [ ] T036 [US4] Add `hakoagent graph trace <node> <direction> <max_depth>` command (BFS over `code_index.dependensi`)
- [ ] T037 [US4] Add `hakoagent graph shortest-path <from> <to>` command (Dijkstra)
- [ ] T038 [US4] Add `hakoagent impact <file_path>` command (blast radius via reverse edges)
- [ ] T039 [US4] Integration test: index codebase → trace → shortest-path → impact all work

**Checkpoint**: User Story 4 complete — graph traversal works

---

## Phase 6: User Story 5 - Multi-Agent Context Sync (Priority: P2)

**Goal**: Multiple agents share context through shared hakodb; documents carry `actor` attribution

**Independent Test**: Agent-A writes finding, Agent-B (separate session) recalls and sees Agent-A's document

### Tests for User Story 5

- [ ] T040 [P] [US5] Unit test: document written with `actor` field is retrievable by query without actor filter
- [ ] T041 [P] [US5] Unit test: query filtered by `actor` returns only that actor's documents
- [ ] T042 [P] [US5] Unit test: concurrent writes from two "agents" (simulated) both succeed without data loss

### Implementation for User Story 5

- [ ] T043 [US5] Ensure all `save_doc` calls include `actor` in document metadata
- [ ] T044 [US5] Ensure `hakoagent recall` returns documents with `actor` attribution visible
- [ ] T045 [US5] Add `actor` filter parameter to `hakoagent recall`
- [ ] T046 [US5] Integration test: simulate agent-A write + agent-B read via separate `hakoagent` invocations against same `.hakoagent/`

**Checkpoint**: User Story 5 complete — multi-agent context sharing verified

---

## Phase 7: User Story 6 - Index Coverage & Source Fallback (Priority: P2)

**Goal**: Index coverage check (like MCP `check_index_coverage`) with source read/grep fallback for gaps

**Independent Test**: Run coverage check on files, verify indexed/unindexed status, fall back to source grep for gaps

### Tests for User Story 6

- [ ] T046 [P] [US6] Unit test: coverage check reports indexed/unindexed status per file
- [ ] T047 [P] [US6] Unit test: source read/grep fallback retrieves info for uncovered files
- [ ] T048 [P] [US6] Unit test: evidence tier (scout/verify/auditor) affects verification depth

### Implementation for User Story 6

- [ ] T049 [US6] Maintain `.hakoagent/_indices/coverage.json` with per-file coverage status
- [ ] T050 [US6] Add `hakoagent graph coverage <file_paths...>` command
- [ ] T051 [US6] Add source read/grep fallback for files with coverage gaps
- [ ] T052 [US6] Add evidence tier parameter (`--tier scout\|verify\|auditor`) to graph commands
- [ ] T053 [US6] Integration test: coverage check → identify gaps → source fallback retrieves info

**Checkpoint**: User Story 6 complete — index coverage with source fallback works

---

## Phase 7.5: User Story 7 - Bug Fixing Loop: Finding → Task → Fix → Skill (Priority: P1)

**Goal**: Agent logs a bug as a `finding`, spawns a `task` with target + DoD to fix it, verifies the fix, saves an immutable revision, then extracts the bug pattern as a reusable `skill` and `lessons_learned` entry.

**Independent Test**: Log a bug finding, verify a task is created with target+DoD, mark the task complete, verify a revision is saved, then verify a new skill + lessons_learned entry exist.

### Tests for User Story 7

- [ ] T054 [P] [US7] Unit test: bug finding creates a task with target + DoD
- [ ] T055 [P] [US7] Unit test: completed fix task triggers immutable revision save
- [ ] T056 [P] [US7] Unit test: post-fix reflection creates skill + lessons_learned entry
- [ ] T057 [P] [US7] Unit test: similar bug retrieves prior bug-fix skill via recall

### Implementation for User Story 7

- [ ] T058 [US7] Add bug-finding → task spawning: `finding` (type: bug) creates `task` with target + DoD
- [ ] T059 [US7] On task completion (dod_verified=true), trigger immutable revision of fixed document
- [ ] T060 [US7] Post-task reflection extracts bug pattern as new `skill` in `.hakoagent/skills/`
- [ ] T061 [US7] Save failure lesson to `lessons_learned` collection
- [ ] T062 [US7] Integration test: log bug → create task → complete → save revision → extract skill → retrieve skill on similar bug

**Checkpoint**: User Story 7 complete — bug fixing loop (finding → task → fix → revision → skill → lessons_learned) works

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories

- [ ] T063 [P] Run full `test_hakoagent.py` suite — verify 31+ tests still pass after FFI/graph changes
- [ ] T064 [P] Verify no MCP/Rust/Cargo/build references remain in code or documentation
- [ ] T065 [P] Verify all files stored under `.hakoagent/` or project root only
- [ ] T066 [P] Verify graceful fallback to JSON when Hakodb library is unavailable
- [ ] T067 [P] Update `AGENTS.md` if needed to reflect real hakodb FFI + graph functions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **User Story 1 (US1)**: Depends on Setup — provides core FFI write capability
- **User Story 2 (US2)**: Depends on US1 (reads require writes to work)
- **User Story 3 (US3)**: Depends on US1 (revisions need document updates)
- **User Story 4 (US4)**: Depends on US1 (graph needs code_index from index)
- **User Story 5 (US5)**: Depends on US1 + US2 + US4 (sharing needs write + recall + graph)
- **User Story 6 (US6)**: Depends on US4 (coverage needs index)
- **User Story 7 (US7)**: Depends on US1 + US2 (bug loop needs FFI write + context retrieval + task)
- **Polish (Phase 8)**: Depends on all user stories

### User Story Dependencies

- **US1 (Hakodb FFI Write, P1)**: Can start after Setup — no dependencies on other stories
- **US2 (Context Retrieval, P1)**: Depends on US1 (needs documents to retrieve)
- **US3 (Revisions/History, P1)**: Depends on US1
- **US4 (Graph Trace/Path/Impact, P1)**: Depends on US1 + index
- **US5 (Multi-Agent Sync, P2)**: Depends on US1 + US2 + US4
- **US6 (Index Coverage, P2)**: Depends on US4
- **US7 (Bug Fixing Loop, P1)**: Depends on US1 + US2 (needs FFI write + task + context)

### Within Each User Story

- Tests written FIRST, ensure they FAIL before implementation (TDD)
- Core FFI/graph functions before CLI commands
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All test tasks marked [P] within a user story can run in parallel
- US3 and US6 can start once their dependencies are complete
- US7 can start once US1 + US2 are complete

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete US1 (Hakodb FFI Write) — write/read via FFI with append-only guard
3. Complete US2 (Context Retrieval) — recall + context_cache with llm_calls_saved
4. **STOP and VALIDATE**: Test `hakoagent event_log` + `hakoagent recall` independently
5. Deploy/demo if ready (MVP: single-agent memory + context + efficiency)

### Incremental Delivery

1. Setup → Foundation ready
2. Add US1 → Test independently → Deploy/Demo
3. Add US2 → Test independently → Deploy/Demo
4. Add US3 → Test independently → Deploy/Demo (immutable revisions)
5. Add US4 → Test independently → Deploy/Demo (graph trace/shortest-path/impact)
6. Add US5 → Test independently → Deploy/Demo (multi-agent sync)
7. Add US6 → Test independently → Deploy/Demo (index coverage + source fallback)
8. Add US7 → Test independently → Deploy/Demo (bug fixing loop: finding → task → fix → skill)
9. Polish → Quality assurance

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD)
- Constitution compliance: every task must have target + DoD; every action logged to `events` (append-only); Python only; real hakodb FFI; no MCP
- Patterns adapted from `/home/web/.claude/skills/codebase-memory/SKILL.md` (codebase-memory knowledge graph MCP): trace_path → graph trace, query_graph → shortest-path, get_architecture → impact, check_index_coverage → graph coverage, Scout/Verify/Auditor → evidence tiers — all implemented with embedded hakodb + Python stdlib, no MCP server
