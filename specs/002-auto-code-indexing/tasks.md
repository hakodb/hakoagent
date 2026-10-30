# Tasks: Auto Codebase Indexing

**Input**: Design documents from `/specs/002-auto-code-indexing/` (spec.md, plan.md, data-model.md, contracts/, research.md)

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story (US1-US3) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure per plan.md

- [X] T001 Verify existing project structure (hakoagent-core/, cli/, .hakoagent/) is in place
- [X] T002 [P] Verify Rust project (hakoagent-core/Cargo.toml, cli/Cargo.toml) with hakodb 0.19 dependency
- [X] T003 [P] Add `notify` and `walkdir` dependencies to hakoagent-core/Cargo.toml for file system watching
- [X] T004 [P] Verify `.hakoagent/` directory with subdirectories: skills/, sessions/, logs/
- [X] T005 [P] Verify `.gitignore` excludes `.hakoagent/hakoagent.db`, `target/`, `*.db`, `__pycache__/`, `.venv/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Verify `hakoagent-core/src/lib.rs` crate entry point with module declarations including indexer
- [X] T007 Verify `hakoagent-core/src/binding/` C ABI / FFI wrapper (HK_Engine, HK_Doc, HK_Query, HK_Batch, HK_Transaction, HK_Watch, HK_ResultSet handles)
- [X] T008 Verify `hakoagent-core/src/memory/mod.rs` module declaration including code_index collection
- [X] T009 [P] Verify `hakoagent-core/src/memory/code_index.rs` — CodeIndexEntry struct with entry_id, file_path, symbol_name, symbol_type, dependencies, line_number, last_indexed_at, file_hash
- [X] T010 [P] Verify `hakoagent-core/src/memory/tasks.rs` — Task struct with target + definition_of_done (FR-006)
- [X] T011 [P] Verify `hakoagent-core/src/planner/mod.rs` module declaration
- [X] T012 [P] Verify `hakoagent-core/src/planner/task.rs` — Task struct with target + DoD validation
- [X] T013 [P] Verify `hakoagent-core/src/planner/flow.rs` — standard 6-step flow (Cross-Model Consistency)
- [X] T014 [P] Verify `cli/src/main.rs` CLI entry point with subcommands: init, index, recall, skill, task, events, vigilance

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Auto Indexing without Manual Agent (Priority: P1) 🎯 MVP

**Goal**: The agent does not need to start indexing manually. The system automatically detects codebase changes and runs indexing as a background thread at startup.

**Independent Test**: Can be tested independently by modifying a file in the repository and then verifying that code_index has been updated automatically without the agent calling `hakoagent index`.

### Implementation for User Story 1

- [X] T015 [US1] Create `hakoagent-core/src/indexer/mod.rs` module declaration (extend existing)
- [X] T016 [US1] Create `hakoagent-core/src/indexer/scanner.rs` — directory traversal using walkdir for source code files (.rs, .py, .js, .ts, .go)
- [X] T017 [US1] Create `hakoagent-core/src/indexer/watcher.rs` — file system watcher using notify crate for real-time change detection
- [X] T018 [US1] Create `hakoagent-core/src/indexer/auto_indexer.rs` — background thread for startup scanning + incremental update (FR-001)
- [X] T019 [US1] Implement startup logic: if database empty → full scan; if database exists → verify and update only changed files (FR-001)
- [X] T020 [US1] Implement file hash computation (SHA-256) for change detection (FR-002)
- [X] T021 [US1] Implement ignored directories filter: node_modules, .git, target, .hakoagent, build output (FR-004)
- [X] T022 [US1] Implement `cli/src/main.rs` `hakoagent init` — starts background thread auto indexing automatically (FR-001)
- [X] T023 [US1] Integration test: init → background thread scans codebase → code_index populated without manual `hakoagent index` (SC-001)

**Checkpoint**: User Story 1 fully functional — auto indexing at startup, no manual index needed

---

## Phase 4: User Story 2 - Incremental Indexing (Priority: P2)

**Goal**: The system only processes files changed since the last indexing, not the whole codebase from scratch.

**Independent Test**: Can be tested by measuring the indexing time for a single changed file compared to indexing the entire codebase.

### Implementation for User Story 2

- [X] T024 [US2] Implement file hash comparison logic: compare stored hash with current file hash to detect changes (FR-002, FR-008)
- [X] T025 [US2] Implement code_index entry creation for new files (FR-007)
- [X] T026 [US2] Implement code_index entry update for modified files (FR-008)
- [X] T027 [US2] Implement code_index entry deletion for deleted files (FR-006)
- [X] T028 [US2] Implement incremental processing: only process files with changed hash or new files (FR-002)
- [X] T029 [US2] Implement IndexingRun entity: run_id, started_at, ended_at, files_processed, files_indexed, errors, status
- [X] T030 [US2] Implement FileChange entity: change_id, file_path, change_type, timestamp, indexed_status
- [X] T031 [US2] Integrate auto_indexer with Memory Service code_index collection (FR-003)
- [ ] T032 [US2] Integration test: change one file → only that file reindexed → time < 5 seconds (SC-002)

**Checkpoint**: User Story 2 fully functional — incremental indexing, < 5 seconds per file

---

## Phase 5: User Story 3 - Indexing Completion Notification (Priority: P3)

**Goal**: Every time automatic indexing finishes, the agent receives a concise notification about what was indexed and whether there were errors.

**Independent Test**: Can be tested by triggering a file change and then verifying that the indexing notification appears.

### Implementation for User Story 3

- [X] T033 [US3] Implement notification mechanism: after indexing run completes, emit summary event to the agent (FR-005)
- [X] T034 [US3] Implement notification content: files_processed, files_indexed, errors, status (FR-005)
- [X] T035 [US3] Implement error handling: single file error does not stop indexing of other files (FR-005)
- [X] T036 [US3] Implement `cli/src/main.rs` `hakoagent events` — view indexing events (FR-005)
- [ ] T037 [US3] Integration test: trigger file change → indexing completes → notification received with summary (SC-005)

**Checkpoint**: User Story 3 fully functional — notification after indexing completes

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [P] Documentation updates in `docs/` (auto indexing setup, usage)
- [X] T039 [P] Code cleanup and refactoring across indexer modules
- [X] T040 [P] Performance optimization: startup scan time for small-medium codebase
- [ ] T041 [P] Additional unit tests in `tests/unit/` for indexer modules
- [ ] T042 [P] Security hardening: verify file access permissions, no sensitive files indexed
- [ ] T043 Run `quickstart.md` validation (Test 1–5 pass)

---

## Phase 7: Convergence

- [X] T044 [US2] Implement code_index entry deletion for deleted files (FR-006, SC-004) (missing, HIGH)
- [X] T045 [US2] Implement IndexingRun entity: run_id, started_at, ended_at, files_processed, files_indexed, errors, status (FR-002) (missing, MEDIUM)
- [X] T046 [US2] Implement FileChange entity: change_id, file_path, change_type, timestamp, indexed_status (FR-002) (missing, MEDIUM)
- [ ] T047 [US2] Integration test: change one file → only that file reindexed → time < 5 seconds (SC-002) (partial, MEDIUM)
- [ ] T048 [US3] Implement formal notification mechanism: summary event to the agent after indexing completes (FR-005, SC-005) (partial, LOW)
- [ ] T049 [US1] Additional unit tests for indexer modules: scanner, watcher, auto_indexer (T041) (missing, LOW)
- [ ] T050 [US1] Security hardening: verify file access permissions, no sensitive files indexed (T042) (missing, LOW)
- [ ] T051 [US1] Run `quickstart.md` validation (Test 1–5 pass) (T043) (missing, LOW)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phases 3-5)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (Auto Indexing Startup, P1)**: Can start after Foundational — Depends on T006-T014 (Foundation: memory, planner, CLI)
- **US2 (Incremental Indexing, P2)**: Can start after Foundational — Depends on US1 (auto_indexer module, code_index collection)
- **US3 (Notification, P3)**: Can start after Foundational — Depends on US1, US2 (IndexingRun, notification mechanism)

### Within Each User Story

- Models/services before CLI commands
- Core implementation before integration tests
- Story complete before moving to next priority
- Tests written FIRST, ensure they FAIL before implementation (TDD)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational completes, US1-US3 can start in parallel (subject to dependency chain)
- All [P] tasks within a user story can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: US1 (Auto Indexing Startup)
4. **STOP and VALIDATE**: Test `hakoagent init` → background thread scans codebase → code_index populated without manual `hakoagent index`
5. Deploy/demo if ready (MVP: auto indexing at startup)

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test independently → Deploy/Demo
3. Add US2 → Test independently → Deploy/Demo
4. Add US3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Background thread startup scanning)
   - Developer B: US2 (Incremental indexing, file hash, code_index CRUD)
   - Developer C: US3 (Notification mechanism, events)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Constitution compliance: every task must have target + DoD; every action logged to `events` (append-only); no hakoagent references; all files under `.hakoagent/` or the project root

---

**Tasks ready for implementation. Proceed to `/hakoagent-implement`.**

---

**Convergence assessment complete. 8 tasks appended under Phase 7. Run `/hakoagent-implement` to complete them, then re-run `/hakoagent-converge` to verify.**
