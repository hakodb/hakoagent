# Tasks: Speckit Addon (HakoDB Agent Memory & Skill Engine)

**Input**: Design documents from `/specs/hakoagent-addon/` (spec.md, plan.md)

**Prerequisites**: plan.md (required), spec.md (required)

**Organization**: Tasks are grouped by user story (US1-US7) corresponding to the 7 modules from plan.md.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure per plan.md

- [X] T001 Create project structure per implementation plan (hakoagent-core/, cli/, bindings/, tests/, examples/)
- [X] T002 Initialize Rust project (hakoagent-core/Cargo.toml, cli/Cargo.toml) with hakodb 0.19 dependency (`--no-default-features`)
- [ ] T003 [P] Configure linting and formatting tools (clippy, rustfmt)
- [X] T004 [P] Create `.hakoagent/skill.yaml` for harness agent integration
- [ ] T005 [P] Create `examples/python/` integration example skeleton

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement `build.rs` with cbindgen for `hakodb.h` generation per target (Linux/macOS/Windows)
- [X] T007 Create `hakoagent-core/src/lib.rs` crate entry point with module declarations
- [X] T008 Create `hakoagent-core/src/binding/` C ABI / FFI wrapper (HK_Engine, HK_Doc, HK_Query, HK_Batch, HK_Transaction, HK_Watch, HK_ResultSet handles)
- [X] T009 [P] Create `hakoagent-core/src/memory/mod.rs` module declaration
- [X] T010 Create `hakoagent-core/src/memory/events.rs` — append-only event log with timestamp ISO 8601, no edit/delete
- [X] T011 [P] Create `hakoagent-core/src/memory/sessions.rs` — session boundary (started_at, ended_at, status)
- [X] T012 Create `hakoagent-core/src/memory/decisions.rs` — keputusan arsitektur + referensi event_id asal
- [X] T013 [P] Create `hakoagent-core/src/memory/findings.rs` — temuan codebase, bug, pola
- [X] T014 [P] Create `hakoagent-core/src/memory/code_index.rs` — simbol, file, dependensi
- [X] T015 [P] Create `hakoagent-core/src/memory/tasks.rs` — task dengan target + DoD
- [X] T016 [P] Create `hakoagent-core/src/memory/context_cache.rs` — cache konteks ringkas
- [X] T017 [P] Create `hakoagent-core/src/memory/skills.rs` — skill store (self-improvement)
- [X] T018 [P] Create `hakoagent-core/src/memory/lessons_learned.rs` — pelajaran dari kegagalan
- [X] T019 Create `cli/src/main.rs` — CLI entry point with subcommands: init, index, recall, skill, task, events, vigilance

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Hakodb Binding Layer (Priority: P1) 🎯 MVP

**Goal**: HakoDB shared library dan C ABI wrapper dapat dibangun dan dipakai dari bahasa host

**Independent Test**: `cargo build --release --no-default-features` produces `libhakodb.so`/`.dylib`/`.dll` + `hakodb.h`; CLI `hakoagent init` creates database successfully

### Implementation for User Story 1

- [ ] T020 [US1] Implement `hakoagent-core/src/binding/engine.rs` — HK_Engine handle (open/put/get/delete/query)
- [ ] T021 [US1] Implement `hakoagent-core/src/binding/doc.rs` — HK_Doc handle (insert/read/delete document)
- [ ] T022 [US1] Implement `hakoagent-core/src/binding/query.rs` — HK_Query handle (where/orderBy/limit)
- [ ] T023 [US1] Implement `hakoagent-core/src/binding/batch.rs` — HK_Batch handle (write_batch)
- [ ] T024 [US1] Implement `hakoagent-core/src/binding/transaction.rs` — HK_Transaction handle (serializable transaction)
- [ ] T025 [US1] Implement `hakoagent-core/src/binding/watch.rs` — HK_Watch handle (watch_collection change stream)
- [ ] T026 [US1] Implement `hakoagent-core/src/binding/result_set.rs` — HK_ResultSet handle
- [ ] T027 [US1] Implement `cli/src/main.rs` `hakoagent init --db <path> --collections all` command
- [ ] T028 [US1] Add unit tests for C ABI binding (contract test against `hakodb.h`)
- [ ] T029 [US1] Verify shared library builds on Linux (`.so`), macOS (`.dylib`), Windows (`.dll`)

**Checkpoint**: User Story 1 should be fully functional — binding layer builds and `hakoagent init` works

---

## Phase 4: User Story 2 - Memory Service (Priority: P1)

**Goal**: Semua 9 koleksi HakoDB dapat diakses melalui Memory Service dengan event append-only

**Independent Test**: CRUD operasi pada setiap koleksi berhasil; event tidak dapat di-overwrite (append-only verified)

### Tests for User Story 2

- [ ] T030 [P] [US2] Unit test: append-only event log rejects edit/delete operations
- [ ] T031 [P] [US2] Unit test: session boundary (started_at/ended_at) enforced

### Implementation for User Story 2

- [ ] T032 [US2] Implement `hakoagent-core/src/memory/sessions.rs` — full CRUD with session lifecycle
- [ ] T033 [US2] Implement `hakoagent-core/src/memory/events.rs` — append-only enforcement, causal reference to event_id
- [ ] T034 [US2] Implement `hakoagent-core/src/memory/decisions.rs` — decision CRUD with rationale + konsekuensi
- [ ] T035 [US2] Implement `hakoagent-core/src/memory/findings.rs` — finding CRUD (bug, pola, error notes)
- [ ] T036 [US2] Implement `hakoagent-core/src/memory/code_index.rs` — symbol/file/dependency index CRUD
- [ ] T037 [US2] Implement `hakoagent-core/src/memory/tasks.rs` — task CRUD with target + DoD
- [ ] T038 [US2] Implement `hakoagent-core/src/memory/context_cache.rs` — cache read/write with TTL
- [ ] T039 [US2] Implement `hakoagent-core/src/memory/skills.rs` — skill CRUD with success/failure counters
- [ ] T040 [US2] Implement `hakoagent-core/src/memory/lessons_learned.rs` — lesson CRUD from failures
- [ ] T041 [US2] Integration test: full CRUD cycle on all 9 collections

**Checkpoint**: Memory Service fully functional — all 9 collections CRUD verified, append-only enforced

---

## Phase 5: User Story 3 - Codebase Indexer (Priority: P2)

**Goal**: Scanner repository dan update inkremental `code_index` via `watch_collection`

**Independent Test**: `hakoagent index` produces `code_index` entries; file changes detected via watch stream

### Implementation for User Story 3

- [ ] T042 Create `hakoagent-core/src/indexer/mod.rs` module declaration
- [ ] T043 [P] [US3] Implement `hakoagent-core/src/indexer/scanner.rs` — scan repository for symbols, files, dependencies
- [ ] T044 [US3] Implement `hakoagent-core/src/indexer/watcher.rs` — `watch_collection` integration for inkremental updates
- [ ] T045 [US3] Implement `cli/src/main.rs` `hakoagent index` command
- [ ] T046 [US3] Implement diff-based change tracking (not snapshot-only)
- [ ] T047 [US3] Integration test: index a sample repository, modify a file, verify `code_index` updates

**Checkpoint**: Codebase Indexer functional — `hakoagent index` produces `code_index`, watch detects changes

---

## Phase 6: User Story 4 - Context Retriever (Priority: P2)

**Goal**: HNSW + FTS pencarian konteks, rangkuman sebelum endpoint, `context_cache` untuk mengurangi panggilan LLM

**Independent Test**: `hakoagent recall <query>` returns relevant context within target time; cache hit reduces endpoint calls

### Implementation for User Story 4

- [ ] T048 Create `hakoagent-core/src/retriever/mod.rs` module declaration
- [ ] T049 [P] [US4] Implement `hakoagent-core/src/retriever/hnsw.rs` — HNSW vector search (KNN)
- [ ] T050 [P] [US4] Implement `hakoagent-core/src/retriever/fts.rs` — Full-text search
- [ ] T051 [US4] Implement `hakoagent-core/src/retriever/summarizer.rs` — rangkuman hasil pencarian sebelum kirim ke endpoint
- [ ] T052 [US4] Implement `hakoagent-core/src/retriever/cache.rs` — `context_cache` with TTL and hit/miss tracking
- [ ] T053 [US4] Implement `cli/src/main.rs` `hakoagent recall <query>` command
- [ ] T054 [US4] Integration test: recall returns relevant context; second identical query served from cache

**Checkpoint**: Context Retriever functional — HNSW+FTS search, summarization, cache hit reduces endpoint calls

---

## Phase 7: User Story 5 - Task Planner (Priority: P2)

**Goal**: Setiap task punya target + DoD terukur; flow konsisten lintas model LLM

**Independent Test**: Task created with target + DoD; flow identical across 2+ different LLM models

### Implementation for User Story 5

- [ ] T055 Create `hakoagent-core/src/planner/mod.rs` module declaration
- [ ] T056 [P] [US5] Implement `hakoagent-core/src/planner/task.rs` — task struct with target + definition_of_done
- [ ] T057 [US5] Implement `hakoagent-core/src/planner/flow.rs` — standard flow: Ambil konteks → Rencanakan → Eksekusi → Verifikasi → Rifleksi → Simpan
- [ ] T058 [US5] Implement `cli/src/main.rs` `hakoagent task list` command
- [ ] T059 [US5] Implement template output standard (no variation per model)
- [ ] T060 [US5] Cross-model consistency test: same task produces structurally identical output on 2+ LLM models

**Checkpoint**: Task Planner functional — target+DoD enforced, flow consistent across models

---

## Phase 8: User Story 6 - Skill Engine (Priority: P3)

**Goal**: Rifleksi pasca-tugas, ekstraksi skill, `lessons_learned`, reuse skill untuk tugas baru

**Independent Test**: Skill extracted from completed task; new similar task retrieves and applies skill

### Implementation for User Story 6

- [ ] T061 Create `hakoagent-core/src/skill_engine/mod.rs` module declaration
- [ ] T062 [P] [US6] Implement `hakoagent-core/src/skill_engine/reflector.rs` — rifleksi pasca-tugas (apa berhasil/gagal/pola)
- [ ] T063 [US6] Implement `hakoagent-core/src/skill_engine/extractor.rs` — ekstraksi pola sukses sebagai skill baru
- [ ] T064 [US6] Implement `hakoagent-core/src/skill_engine/registry.rs` — skill registry with success/failure counters
- [ ] T065 [US6] Implement skill retrieval via semantic search (HNSW) on `skills` collection
- [ ] T066 [US6] Implement `cli/src/main.rs` `hakoagent skill list` and `hakoagent skill add <name>` commands
- [ ] T067 [US6] Implement skill revision/archive for ineffective skills
- [ ] T068 [US6] Integration test: extract skill from task, reuse on similar task, verify performance improvement

**Checkpoint**: Skill Engine functional — skill extracted, stored, and reused on similar tasks

---

## Phase 9: User Story 7 - Vigilance Checker + CLI Polish (Priority: P3)

**Goal**: Deteksi regresi, file terlupakan, TODO tertinggal; integrasi CLI penuh

**Independent Test**: `hakoagent vigilance` reports at least one detectable issue in test repository

### Implementation for User Story 7

- [ ] T067 Create `hakoagent-core/src/vigilance/mod.rs` module declaration
- [ ] T068 [P] [US7] Implement `hakoagent-core/src/vigilance/unused_file.rs` — deteksi file yang diubah tapi tidak diuji
- [ ] T069 [P] [US7] Implement `hakoagent-core/src/vigilance/todo_detector.rs` — deteksi TODO yang belum disentuh
- [ ] T070 [US7] Implement `hakoagent-core/src/vigilance/regression.rs` — deteksi regresi terhadap prinsip konstitusi
- [ ] T071 [US7] Implement `cli/src/main.rs` `hakoagent events` and `hakoagent vigilance` commands
- [ ] T072 [US7] CLI polish: all subcommands (init, index, recall, skill, task, events, vigilance) working
- [ ] T073 [US7] End-to-end integration test: full flow init → index → recall → task → skill → vigilance
- [ ] T074 [US7] Verify constitution compliance: every task has DoD, every action logged to `events`

**Checkpoint**: Vigilance Checker + CLI complete — all subcommands working, constitution compliance verified

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T075 [P] Documentation updates in `docs/` (installation, usage, API reference)
- [ ] T076 [P] Code cleanup and refactoring across all modules
- [ ] T077 [P] Performance optimization: context retrieval < X seconds target
- [ ] T078 [P] Additional unit tests in `tests/unit/` for all modules
- [ ] T079 Security hardening: verify WAL durability, encryption at rest option
- [ ] T080 Run `quickstart.md` validation (if created)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phases 3-9)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (Hakodb Binding Layer, P1)**: Can start after Foundational — No dependencies on other stories
- **US2 (Memory Service, P1)**: Can start after Foundational — Depends on US1 (binding layer)
- **US3 (Codebase Indexer, P2)**: Can start after Foundational — Depends on US2 (Memory Service for code_index)
- **US4 (Context Retriever, P2)**: Can start after Foundational — Depends on US2 (Memory Service), US3 (code_index)
- **US5 (Task Planner, P2)**: Can start after Foundational — Depends on US2 (Memory Service for tasks)
- **US6 (Skill Engine, P3)**: Can start after Foundational — Depends on US2 (Memory Service for skills/lessons_learned)
- **US7 (Vigilance Checker, P3)**: Can start after Foundational — Depends on all previous stories

### Within Each User Story

- Models/services before CLI commands
- Core implementation before integration tests
- Story complete before moving to next priority
- Tests written FIRST, ensure they FAIL before implementation (TDD)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational completes, US1-US7 can start in parallel (subject to dependency chain)
- All [P] tasks within a user story can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: US1 (Hakodb Binding Layer)
4. Complete Phase 4: US2 (Memory Service)
5. **STOP and VALIDATE**: Test `hakoagent init` + CRUD on all 9 collections independently
6. Deploy/demo if ready (MVP: database + memory service)

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test independently → Deploy/Demo
3. Add US2 → Test independently → Deploy/Demo
4. Add US3-US7 → Each tested independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Binding Layer)
   - Developer B: US2 (Memory Service)
   - Developer C: US3 (Indexer) + US4 (Retriever)
   - Developer D: US5 (Planner) + US6 (Skill Engine)
   - Developer E: US7 (Vigilance) + CLI polish
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
- Constitution compliance: every task must have target + DoD; every action logged to `events` (append-only)

---

## Phase 11: Convergence

- [X] T081 Enforce append-only at all write paths per Constitution "Kronologi & Histori" (contradicts, CRITICAL)
- [X] T082 Implement standard 6-step flow per Constitution "Cross-Model Consistency" (contradicts, CRITICAL)
- [X] T083 Implement skill engine per Constitution "Self Skill Improvement" (contradicts, CRITICAL)
- [X] T084 Connect binding layer to HakoDB native API instead of file-based JSON per FR-1.1, FR-2.1 (missing, HIGH)
- [X] T085 Add append-only guard on event write paths per FR-2.2 (missing, HIGH)
- [X] T086 Implement codebase scanner + watch_collection per FR-3.1, FR-3.2 (missing, HIGH)
- [X] T087 Implement HNSW + FTS + summarizer + context_cache per FR-4.1 to FR-4.4 (missing, HIGH)
- [X] T088 Implement task + DoD + consistent cross-model flow per FR-5.1 to FR-5.4 (missing, HIGH)
- [X] T089 Implement skill engine reflection + extraction + registry per FR-6.1 to FR-6.5 (missing, HIGH)
- [X] T090 Implement vigilance checker: untested files, TODO detector, regression per FR-7.1 to FR-7.4 (missing, HIGH)
- [X] T091 Wire CLI subcommands (index, recall, skill, task, events, vigilance) to real modules per CLI partial (partial, HIGH)
- [ ] T092 Verify cross-platform shared library builds (.so, .dylib, .dll) per FR-1.3 (partial, MEDIUM)
- [ ] T093 Complete polish phase: docs, cleanup, unit tests, security hardening per T075–T080 (low, LOW)

---

**Convergence assessment complete. 13 tasks appended under Phase 11. Run `/hakoagent-implement` to complete them, then re-run `/hakoagent-converge` to verify.**
