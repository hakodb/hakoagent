# Tasks: HakoAgent Enhancement (Vector + Graph + Multi-Agent)

**Input**: specs/005-enhancements/spec.md (spec), specs/005-enhancements/plan.md (plan)
**Prerequisites**: specs/003-cache-graph-system/ (existing caching + graph), specs/004-team-context/ (team context)

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Vector Search & Typed Graph Edges (Week 1)

### US1: Vector Search (P1)

- [ ] T001 [US1] Create `context_cache` entries with `vector_id` field (link to code_vectors)
- [ ] T002 [US1] Implement `_vectorize_query()` using TF-IDF (placeholder until hakodb HNSW)
- [ ] T003 [US1] Implement `_vector_search()` using cosine similarity with query vector
- [ ] T004 [US1] Update `cmd_recall()` to use vector search + keyword scoring hybrid
- [ ] T005 [US1] Add `--semantic` flag to `hakoagent recall` command
- [ ] T006 [US1] Integration test: query "error handling" returns code with `try/catch` even without word "error"

### US2: Typed Graph Edges (P1)

- [ ] T007 [US2] Create `graph_edges` collection with fields: edge_id, from_node, to_node, edge_type, weight
- [ ] T008 [US2] Edge types: `imports`, `calls`, `depends_on`, `data_flows`, `test_of`, `defines`
- [ ] T009 [US2] Update `cmd_index()` to extract and store typed edges during indexing
- [ ] T010 [US2] Implement `graph traverse <node> <dir> <depth> [--edge-type <type>]` — filter by edge type
- [ ] T011 [US2] Implement `graph shortest-path <from> <to> [--weighted]` — Dijkstra with edge weights
- [ ] T012 [US2] Implement `graph dependents <node> [--edge-type <type>]` — filter by edge type
- [ ] T013 [US2] Implement `graph dependents-reverse <node> [--edge-type <type>]` — filter by edge type
- [ ] T014 [US2] Integration test: `graph traverse src/main.rs out 3 --edge-type calls` returns only call edges

### US3: Change Stream / Auto-Index (P2)

- [ ] T015 [US3] Implement `watch_collection("code_index")` — detect file changes
- [ ] T016 [US3] Auto-reindex changed files on change event
- [ ] T017 [US3] Update graph edges when dependencies change (add/remove edges)
- [ ] T018 [US3] Integration test: modify a file, `hakoagent index` not needed, graph updates automatically

---

## Phase 2: Hakodb FFI Integration (Week 2)

### US4: Hakodb FFI Binding Layer (P2)

- [ ] T019 [US4] Add `hakodb = { version = "0.20", features = ["net-sync"] }` dependency
- [ ] T020 [US4] Create `hakodb_binding.py` with C ABI: `hk_engine_open`, `hk_engine_put`, `hk_engine_get`, `hk_engine_delete`, `hk_engine_watch_collection`
- [ ] T021 [US4] Replace `save_doc/load_doc/delete_doc/scan_docs` with hakodb FFI calls
- [ ] T022 [US4] Fallback to JSON files if hakodb .so not available (ponytail: graceful degradation)
- [ ] T023 [US4] Migrate `context_cache` collection to hakodb
- [ ] T024 [US4] Migrate `code_index` collection to hakodb
- [ ] T025 [US4] Migrate `skills` collection to hakodb
- [ ] T026 [US4] Migrate `tasks` collection to hakodb
- [ ] T027 [US4] Migrate `events` collection to hakodb

### US5: Vector Search via hakodb HNSW (P2)

- [ ] T028 [US5] Replace TF-IDF with hakodb native HNSW vector search
- [ ] T029 [US5] Add `vector_id` field to code_index entries
- [ ] T030 [US5] Implement `hk_vector_search` via C ABI or Python wrapper
- [ ] T031 [US5] Integration test: `hakoagent recall "error handling"` returns code with `try/catch` blocks even without word "error"

---

## Phase 3: Multi-Agent Sync (Week 3)

### US5: Notification System (P2)

- [ ] T032 [US5] Implement `hakoagent cache stats --format table` — table format output
- [ ] T033 [US5] Implement `hakoagent skill list --format table` — table format output
- [ ] T034 [US5] Implement `hakoagent task list --format table` — table format output
- [ ] T035 [US5] Implement `hakoagent events --format table` — table format output
- [ ] T036 [US5] Implement `hakoagent graph dependents <node> --format table` — table format output

### US6: Multi-Agent Sync (P2)

- [ ] T037 [US6] `hakoagent team sync --push` — push local changes to remote
- [ ] T038 [US6] `hakoagent team sync --pull` — pull remote changes
- [ ] T039 [US6] `hakoagent team sync` — both push and pull (default)
- [ ] T040 [US6] Real-time event streaming via `watch_collection("events")`

---

## Phase 4: Polish & Testing (Week 4)

### T041 [US1-US6] Additional unit tests

- [ ] T041 [US1] Test graph traversal with typed edges
- [ ] T042 [US2] Test vector search with mock vectors
- [ ] T043 [US3] Test cache hit/miss tracking
- [ ] T044 [US4] Test skill dedup/eviction
- [ ] T045 [US5] Test graph shortest path with weighted edges

### T046 [US1-US6] Update documentation

- [ ] T046 [US1] Update `INSTALL.md` with new commands
- [ ] T047 [US2] Update `AGENTS.md` with new skill commands
- [ ] T048 [US3] Update `.opencode/skills/hakoagent/SKILL.md` with new commands
- [ ] T049 [US4] Update `specs/005-enhancements/tasks.md` — this file

---

## Execution Order

1. Phase 1 (US1-US3): Vector search + typed graph edges — core feature
2. Phase 2 (US4-US5): Hakodb FFI integration — enables vector search & concurrency
3. Phase 3 (US5-US6): Multi-agent sync — team collaboration
4. Phase 4 (T041-T048): Tests + documentation — quality assurance

## Dependencies

| Task | Depends On |
|------|------------|
| T002 | T001 |
| T003 | T001, T002 |
| T004 | T002, T003 |
| T005 | T001 |
| T006 | T001 |
| T007 | T001, T006 |
| T008 | T006 |
| T009 | T007 |
| T010 | T007 |
| T011 | T007 |
| T012 | T007 |
| T013 | T007 |
| T014 | T010-T013 |
| T015 | T001 |
| T016 | T015 |
| T017 | T015 |
| T018 | T015-T017 |
| T019 | — (external dep: hakodb crate) |
| T020 | T019 |
| T021 | T020 |
| T022-T027 | T021 |
| T028-T031 | T021 |
| T032-T036 | — |
| T037-T039 | T019, T021 |
| T040 | T037-T039 |
| T041-T045 | T001-T040 |
| T046-T048 | T001-T045 |

## Success Criteria

- `hakoagent recall <query>` returns semantically relevant results (not just keyword match)
- `hakoagent graph traverse <node> out --edge-type calls` returns only call edges
- `hakoagent graph shortest-path <from> <to> --weighted` returns weighted shortest path
- `hakoagent index` automatically indexes and builds graph edges
- `hakoagent team sync --push/pull` syncs with remote (when hakodb net-sync available)
- All 31+ existing tests still pass

---

**End of tasks.md.**