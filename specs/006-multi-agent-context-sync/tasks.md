# Tasks: HakoAgent Multi-Agent Context Sync

**Input**: Design documents from `specs/006-multi-agent-context-sync/` (spec.md, plan.md)

**Prerequisites**: plan.md (required), spec.md (required)

**Organization**: Tasks are grouped by user story (US1-US4) corresponding to the 4 user stories from spec.md.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure per plan.md

- [ ] T001 [P] Verify `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` and `lib/hakodb.h` are present and hash-verified against `lib/SHA256SUMS.txt`
- [ ] T002 [P] Verify Python 3 is available and `test_hakoagent.py` passes (31+ tests baseline)
- [ ] T003 [P] Create `specs/006-multi-agent-context-sync/research.md` documenting FFI symbol verification
- [ ] T004 [P] Create `specs/006-multi-agent-context-sync/data-model.md` with entity definitions
- [ ] T005 [P] Create `specs/006-multi-agent-context-sync/contracts/multi-agent-context-interface.md`
- [ ] T006 [P] Create `specs/006-multi-agent-context-sync/quickstart.md` (already drafted in plan.md)

---

## Phase 2: User Story 1 - Agent Memory Write via Real Hakodb FFI (Priority: P1) 🎯 MVP

**Goal**: Agent can store session, event, decision, finding, task documents to HakoDB via ctypes FFI with append-only guard

**Independent Test**: Call `hakoagent.event_log`, verify event appears in `events` collection via `hakoagent events` and `hakoagent.load_doc`

### Tests for User Story 1 (write FIRST, ensure FAIL before implementation)

- [ ] T007 [P] [US1] Unit test: `hk_engine_put` calls `hk_engine_insert_json` with correct argtypes (c_void_p, c_char_p, c_char_p, c_char_p)
- [ ] T008 [P] [US1] Unit test: `hk_engine_get` calls `hk_engine_get_json` with c_void_p restype and `ctypes.string_at()` + `hk_string_free`
- [ ] T009 [P] [US1] Unit test: append-only guard rejects duplicate `event_id` in `events` collection
- [ ] T010 [P] [US1] Unit test: event has ISO 8601 `timestamp` and unique `event_id`

### Implementation for User Story 1

- [ ] T011 [US1] Update `hakoagent` FFI wrapper: `hk_engine_put` uses `hk_engine_insert_json` (not `hk_engine_insert` with 4 strings)
- [ ] T012 [US1] Update `hakoagent` FFI wrapper: `hk_engine_get` uses `hk_engine_get_json` with `c_void_p` restype + `string_at()` + `hk_string_free`
- [ ] T013 [US1] Add `actor` parameter to `hakoagent.event_log` and store in event metadata
- [ ] T014 [US1] Add append-only guard: check `event_id` uniqueness before writing to `events` collection
- [ ] T015 [US1] Ensure `save_doc`/`load_doc`/`delete_doc` dual-write to both JSON files and HakoDB FFI
- [ ] T016 [US1] Integration test: write event → read back via `load_doc` → verify content matches

**Checkpoint**: User Story 1 complete — single agent can write and read memory via real HakoDB FFI

---

## Phase 3: User Story 2 - Context Retrieval via Recall (Priority: P1)

**Goal**: Agent can query context from HakoDB collections using `hakoagent recall` with TF-IDF + cosine similarity and TTL-based context_cache

**Independent Test**: Write document to `skills`/`findings`, run `hakoagent recall <query>`, verify document returned

### Tests for User Story 2

- [ ] T017 [P] [US2] Unit test: `cache_get_internal` returns None for TTL-expired entries
- [ ] T018 [P] [US2] Unit test: `cache_put_internal` stores entry with `created_at`, `ttl_seconds`, `hit_count`
- [ ] T019 [P] [US2] Unit test: `_vector_search_collection` returns results ranked by cosine similarity
- [ ] T020 [P] [US2] Unit test: second identical query within TTL returns cache hit

### Implementation for User Story 2

- [ ] T021 [US2] Verify `hakoagent recall` searches `code_index`, `skills`, `findings`, `decisions`, `events` collections
- [ ] T022 [US2] Verify `hakoagent recall` checks `context_cache` first (TTL-valid) before vector search
- [ ] T023 [US2] Verify `hakoagent recall` stores results in `context_cache` with default TTL 300s
- [ ] T024 [US2] Integration test: write skill → recall query finds it → second query is cache hit

**Checkpoint**: User Story 2 complete — context retrieval with caching works

---

## Phase 4: User Story 3 - Multi-Agent Context Sync (Priority: P1)

**Goal**: Multiple agents share context through shared HakoDB; documents carry `actor` attribution

**Independent Test**: Agent-A writes finding, Agent-B (separate session) recalls and sees Agent-A's document

### Tests for User Story 3

- [ ] T025 [P] [US3] Unit test: document written with `actor` field is retrievable by query without actor filter
- [ ] T026 [P] [US3] Unit test: query filtered by `actor` returns only that actor's documents
- [ ] T027 [P] [US3] Unit test: concurrent writes from two "agents" (simulated) both succeed without data loss

### Implementation for User Story 3

- [ ] T028 [US3] Ensure all `save_doc` calls include `actor` in document metadata
- [ ] T029 [US3] Ensure `hakoagent recall` returns documents with `actor` attribution visible
- [ ] T030 [US3] Integration test: simulate agent-A write + agent-B read via separate `hakoagent` invocations against same `.hakoagent/`

**Checkpoint**: User Story 3 complete — multi-agent context sharing verified

---

## Phase 5: User Story 4 - Session & History Tracking (Priority: P2)

**Goal**: Each agent session tracked with started_at/ended_at/status/model_used; all actions logged as append-only events

**Independent Test**: Start session, perform actions, verify `hakoagent events` shows chronological history

### Tests for User Story 4

- [ ] T031 [P] [US4] Unit test: session auto-created on first action with `started_at` and `status: "active"`
- [ ] T032 [P] [US4] Unit test: all events in a session share the same `session_id`
- [ ] T033 [P] [US4] Unit test: ending session sets `ended_at` and `status: "ended"`

### Implementation for User Story 4

- [ ] T034 [US4] Verify `current_session()` auto-creates session on first action
- [ ] T035 [US4] Verify `log_event` records `session_id`, `timestamp`, `actor`, `action`, `target`
- [ ] T036 [US4] Verify `hakoagent events` displays events in chronological order
- [ ] T037 [US4] Integration test: full session lifecycle (start → actions → end → verify history)

**Checkpoint**: User Story 4 complete — session and history tracking works

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories

- [ ] T038 [P] Run full `test_hakoagent.py` suite — verify 31+ tests still pass after FFI changes
- [ ] T039 [P] Verify no Rust/Cargo/build references remain in code or documentation
- [ ] T040 [P] Verify all files stored under `.hakoagent/` or project root only
- [ ] T041 [P] Verify graceful fallback to JSON when HakoDB library is unavailable
- [ ] T042 [P] Update `AGENTS.md` if needed to reflect real hakodb FFI usage

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **User Story 1 (US1)**: Depends on Setup — provides core FFI write capability
- **User Story 2 (US2)**: Depends on US1 (reads require writes to work)
- **User Story 3 (US3)**: Depends on US1 and US2 (sharing requires write + recall)
- **User Story 4 (US4)**: Depends on US1 (sessions use event_log)
- **Polish (Phase 6)**: Depends on all user stories

### User Story Dependencies

- **US1 (Hakodb FFI Write, P1)**: Can start after Setup — no dependencies on other stories
- **US2 (Context Retrieval, P1)**: Depends on US1 (needs documents to retrieve)
- **US3 (Multi-Agent Sync, P1)**: Depends on US1 + US2 (needs write + recall for sharing)
- **US4 (Session & History, P2)**: Depends on US1 (uses event_log)

### Within Each User Story

- Tests written FIRST, ensure they FAIL before implementation (TDD)
- Core FFI functions before CLI commands
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All test tasks marked [P] within a user story can run in parallel
- US3 and US4 can start once US1 is complete (US3 also needs US2)

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete US1 (Hakodb FFI Write) — write/read via FFI with append-only guard
3. Complete US2 (Context Retrieval) — recall + context_cache
4. **STOP and VALIDATE**: Test `hakoagent event_log` + `hakoagent recall` independently
5. Deploy/demo if ready (MVP: single-agent memory + context)

### Incremental Delivery

1. Setup → Foundation ready
2. Add US1 → Test independently → Deploy/Demo
3. Add US2 → Test independently → Deploy/Demo
4. Add US3 → Test independently → Deploy/Demo (multi-agent sync)
5. Add US4 → Test independently → Deploy/Demo (session history)
6. Polish → Quality assurance

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD)
- Constitution compliance: every task must have target + DoD; every action logged to `events` (append-only); Python only; real hakodb FFI
