# Tasks: Refactor HakoAgent to Constitution

**Input**: Design documents from `/specs/001-refactor-hakoagent/` (spec.md, plan.md, data-model.md, contracts/, research.md)

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story (US1-US4) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure per plan.md

- [X] T001 Create project structure per implementation plan (.hakoagent/, hakoagent-core/, cli/, tests/, examples/)
- [X] T002 Initialize Rust project (hakoagent-core/Cargo.toml, cli/Cargo.toml) with hakodb 0.19 dependency (`--no-default-features`)
- [X] T003 [P] Configure linting and formatting tools (clippy, rustfmt)
- [X] T004 [P] Create `.hakoagent/` directory with subdirectories: skills/, sessions/, logs/
- [X] T005 [P] Update `.gitignore` to exclude `.hakoagent/hakoagent.db`, `target/`, `*.db`, `__pycache__/`, `.venv/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement `build.rs` with cbindgen for `hakodb.h` generation per target (Linux/macOS/Windows)
- [X] T007 Create `hakoagent-core/src/lib.rs` crate entry point with module declarations (binding, memory, indexer, retriever, planner, skill_engine, vigilance)
- [X] T008 Create `hakoagent-core/src/binding/` C ABI / FFI wrapper (HK_Engine, HK_Doc, HK_Query, HK_Batch, HK_Transaction, HK_Watch, HK_ResultSet handles)
- [X] T009 [P] Create `hakoagent-core/src/memory/mod.rs` module declaration
- [X] T010 Create `hakoagent-core/src/memory/events.rs` — append-only event log with timestamp ISO 8601, application-level guard checking event_id before write (FR-004)
- [X] T011 [P] Create `hakoagent-core/src/memory/sessions.rs` — session boundary (started_at, ended_at, status, model_used)
- [X] T012 [P] Create `hakoagent-core/src/memory/decisions.rs` — architecture decisions + rationale + consequences + reference to the originating event_id
- [X] T013 [P] Create `hakoagent-core/src/memory/findings.rs` — codebase findings, bugs, patterns, error notes
- [X] T014 [P] Create `hakoagent-core/src/memory/code_index.rs` — symbols, files, dependencies
- [X] T015 [P] Create `hakoagent-core/src/memory/tasks.rs` — task with target + DoD (FR-006)
- [X] T016 [P] Create `hakoagent-core/src/memory/context_cache.rs` — concise context cache
- [X] T017 [P] Create `hakoagent-core/src/memory/skills.rs` — skill data model (skill_id, name, description, context_tags, success_count, failure_count, status)
- [X] T018 [P] Create `hakoagent-core/src/memory/lessons_learned.rs` — lessons from failures
- [X] T019 Create `cli/src/main.rs` — CLI entry point with subcommands: init, index, recall, skill, task, events, vigilance

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - HakoAgent Tool Calling for Memory and Skills (Priority: P1) 🎯 MVP

**Goal**: The AI agent in the harness can call HakoAgent tools to save events, search context, create tasks, and manage skills through a consistent and measurable interface.

**Independent Test**: Can be tested independently by calling each HakoAgent tool (init, recall, event_log, skill_add, task_create, etc.) and verifying that files under `.hakoagent/` are created or updated correctly.

### Implementation for User Story 1

- [X] T020 [US1] Implement `hakoagent-core/src/binding/engine.rs` — HK_Engine handle (open/put/get/delete/query, write_batch, transactions, watch)
- [X] T021 [US1] Implement `hakoagent-core/src/binding/doc.rs` — HK_Doc handle (insert/read/delete document)
- [X] T022 [US1] Implement `hakoagent-core/src/binding/query.rs` — HK_Query handle (where/orderBy/limit)
- [X] T023 [US1] Implement `hakoagent-core/src/binding/batch.rs` — HK_Batch handle (write_batch)
- [X] T024 [US1] Implement `hakoagent-core/src/binding/transaction.rs` — HK_Transaction handle (serializable transaction)
- [X] T025 [US1] Implement `hakoagent-core/src/binding/watch.rs` — HK_Watch handle (watch_collection change stream)
- [X] T026 [US1] Implement `hakoagent-core/src/binding/result_set.rs` — HK_ResultSet handle
- [X] T027 [US1] Implement `cli/src/main.rs` `hakoagent init --db <path> --collections all` command (FR-002, FR-003)
- [X] T028 [US1] Implement `cli/src/main.rs` `hakoagent recall <query>` command with HNSW + FTS search (FR-007)
- [X] T029 [US1] Implement `cli/src/main.rs` `hakoagent events` command to view event history (FR-004)
- [X] T030 [US1] Verify no "hakoagent" references in all source files, documentation, and configuration (FR-009, SC-003)
- [X] T031 [US1] Integration test: full cycle init → recall → event_log → task_create → skill_add → task_complete < 30 seconds (SC-001)

**Checkpoint**: User Story 1 should be fully functional — binding layer builds, CLI init/recall/events work, no hakoagent references

---

## Phase 4: User Story 2 - Skills in Markdown Format (Priority: P2)

**Goal**: Every success pattern or lesson learned from tasks is saved as a Markdown skill file under `.hakoagent/skills/`, searchable, and reusable for similar tasks in the future.

**Independent Test**: Can be tested by creating a Markdown skill file, then finding it via `hakoagent.skill_list` or `hakoagent.skill_get`, and verifying the returned content.

### Implementation for User Story 2

- [X] T032 [US2] Create `hakoagent-core/src/skill_engine/mod.rs` module declaration
- [X] T033 [P] [US2] Implement `hakoagent-core/src/skill_engine/reflector.rs` — post-task reflection (what succeeded, failed, patterns)
- [X] T034 [P] [US2] Implement `hakoagent-core/src/skill_engine/extractor.rs` — extraction of success patterns as new skills
- [X] T035 [US2] Implement `hakoagent-core/src/skill_engine/registry.rs` — skill registry with success/failure counters
- [X] T036 [US2] Implement skill file writer — save skill as Markdown file to `.hakoagent/skills/` with metadata header (skill_id, name, status, tags, success_count, failure_count) (FR-005, SC-004)
- [X] T037 [US2] Implement `cli/src/main.rs` `hakoagent skill list` command — list all active skills from `.hakoagent/skills/`
- [X] T038 [US2] Implement `cli/src/main.rs` `hakoagent skill add <name>` command — add new skill as Markdown file
- [X] T039 [US2] Implement `cli/src/main.rs` `hakoagent skill get <skill_id>` command — retrieve skill content in Markdown format
- [X] T040 [US2] Integration test: create skill Markdown file, list skills, retrieve skill content, verify Markdown format

**Checkpoint**: User Story 2 fully functional — skill stored as Markdown, retrievable via CLI

---

## Phase 5: User Story 3 - Task with Target and DoD (Priority: P2)

**Goal**: Every task the agent works on has a target and Definition of Done recorded in the `tasks` collection, so progress can be verified and stays consistent across LLM models.

**Independent Test**: Can be tested by creating a new task via `hakoagent.task_create`, then verifying via `hakoagent.task_list` that the target and DoD are recorded correctly.

### Implementation for User Story 3

- [X] T041 [US3] Create `hakoagent-core/src/planner/mod.rs` module declaration
- [X] T042 [P] [US3] Implement `hakoagent-core/src/planner/task.rs` — Task struct with target + definition_of_done (FR-006)
- [X] T043 [P] [US3] Implement `hakoagent-core/src/planner/flow.rs` — standard 6-step flow: Retrieve context → Plan → Execute → Verify → Reflect → Save (Cross-Model Consistency)
- [X] T044 [US3] Implement `cli/src/main.rs` `hakoagent task list` command — list tasks from `tasks` collection
- [X] T045 [US3] Implement `cli/src/main.rs` `hakoagent task create <title>` command — create task with target + DoD
- [X] T046 [US3] Implement `cli/src/main.rs` `hakoagent task complete <id>` command — mark task complete with dod_verified
- [X] T047 [US3] Validate every task has non-empty target and definition_of_done before marking done (Clear Target principle)
- [X] T048 [US3] Integration test: create task with target+DoD, list tasks, complete task with dod_verified=true, verify status change

**Checkpoint**: User Story 3 fully functional — task with target+DoD, flow consistent across models

---

## Phase 6: User Story 4 - Vigilance Checker (Priority: P3)

**Goal**: The Vigilance Checker automatically detects files that were changed but not tested, untouched TODOs, and regressions against constitution principles.

**Independent Test**: Can be tested by running `hakoagent.vigilance` on the project directory and verifying the generated report.

### Implementation for User Story 4

- [X] T049 [US4] Create `hakoagent-core/src/vigilance/mod.rs` module declaration
- [X] T050 [P] [US4] Implement `hakoagent-core/src/vigilance/unused_file.rs` — detect files changed but not tested (FR-008)
- [X] T051 [P] [US4] Implement `hakoagent-core/src/vigilance/todo_detector.rs` — detect untouched TODOs (FR-008)
- [X] T052 [US4] Implement `hakoagent-core/src/vigilance/regression.rs` — detect regressions against constitution principles (FR-008)
- [X] T053 [US4] Implement `cli/src/main.rs` `hakoagent vigilance` command — run all vigilance checks
- [X] T054 [US4] Integration test: run vigilance on test repository, verify unused files, TODO items, and constitution regression detected

**Checkpoint**: User Story 4 fully functional — vigilance detects untested files, TODO items, constitution regressions

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T055 [P] Documentation updates in `docs/` (installation, usage, API reference)
- [X] T056 [P] Code cleanup and refactoring across all modules (renamed hakoagent → hakoagent, updated paths)
- [X] T057 [P] Performance optimization: context retrieval < X seconds target (SC-001)
- [X] T058 [P] Additional unit tests in `tests/unit/` for all modules
- [X] T059 [P] Security hardening: verify WAL durability, encryption at rest option
- [X] T060 Run `quickstart.md` validation (all 6 test scenarios pass)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (Tool Calling Memory & Skill, P1)**: Can start after Foundational — Depends on T006-T019 (Binding Layer + Memory Service)
- **US2 (Skill Markdown, P2)**: Can start after Foundational — Depends on T010 (events), T017 (skills collection), US1 (binding layer)
- **US3 (Task + DoD, P2)**: Can start after Foundational — Depends on T015 (tasks collection), US1 (binding layer)
- **US4 (Vigilance Checker, P3)**: Can start after Foundational — Depends on all previous stories

### Within Each User Story

- Models/services before CLI commands
- Core implementation before integration tests
- Story complete before moving to next priority
- Tests written FIRST, ensure they FAIL before implementation (TDD)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational completes, US1-US4 can start in parallel (subject to dependency chain)
- All [P] tasks within a user story can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: US1 (Tool Calling Memory & Skill)
4. **STOP and VALIDATE**: Test `hakoagent init` + CRUD on all 9 collections independently
5. Deploy/demo if ready (MVP: database + memory service + tool calling)

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test independently → Deploy/Demo
3. Add US2 → Test independently → Deploy/Demo
4. Add US3 → Test independently → Deploy/Demo
5. Add US4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Binding Layer + CLI init/recall/events)
   - Developer B: US2 (Skill Engine + Markdown skill files)
   - Developer C: US3 (Task Planner + flow + CLI task commands)
   - Developer D: US4 (Vigilance Checker + CLI vigilance command)
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
- Constitution compliance: every task must have target + DoD; every action logged to `events` (append-only); skill must be Markdown format; no hakoagent references

---

**Tasks ready for implementation. Proceed to `/hakoagent-implement`.**
