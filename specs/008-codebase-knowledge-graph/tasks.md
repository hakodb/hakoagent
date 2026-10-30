# Tasks: Codebase Knowledge Graph (US8)

**Input**: Design documents from `specs/008-codebase-knowledge-graph/` (spec.md, plan.md, research.md, data-model.md, contracts/)

**Prerequisites**: spec.md (required), plan.md (required)

**Organization**: Tasks are grouped by phase (P0-P2) corresponding to the plan.md phases.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US8, US9, US10, US11)
- Include exact file paths in descriptions

---

## Phase 0: Research (Shared Infrastructure)

- [ ] T001 [P] [US8-US11] Verify gap analysis: list all 15 MCP codebase-memory tools vs current hakoagent capabilities
- [ ] T002 [P] [US8-US11] Verify Python 3 stdlib has `re`, `subprocess`, `math`, `heapq`, `collections` for Cypher parser + git diff
- [ ] T003 [P] [US8-US11] Confirm `.hakoagent/_indices/` structure supports graph coverage (coverage.json, definitions.json)

---

## Phase 1: Data Model & Contracts

- [ ] T004 [P] [US8] Add `code_edges` collection to COLLECTIONS list in hakoagent
- [ ] T005 [P] [US8] Add `adrs`, `traces`, `projects` collections to COLLECTIONS list in hakoagent
- [ ] T006 [P] [US8] Define CodeNode schema (entry_id, file_path, symbol_name, symbol_type, label, qualified_name, line_number, file_hash, actor, edges)
- [ ] T007 [P] [US8] Define CodeEdge schema (edge_id, source_id, target_id, edge_type, confidence, line_number, actor)
- [ ] T008 [P] [US8] Define ArchitectureDecision schema (adr_id, title, status, rationale, consequences, created_at, actor)
- [ ] T009 [P] [US8] Define TraceEntry schema (trace_id, timestamp, span_id, parent_span_id, operation, service, duration_ms, actor)
- [ ] T010 [P] [US8] Define Project schema (project_name, root_path, indexed_at, node_count, edge_count, actor)
- [ ] T011 [P] [US8] Define 16+ edge type constants (CALLS, HTTP_CALLS, ASYNC_CALLS, SPAWNS, DATA_FLOWS, IMPORTS, DEFINES, DEFINES_METHOD, OVERRIDE, USAGE, CALL_REFERENCE, CONFIGURES, REFERENCES_FILE, MENTIONS, FILE_CHANGES_WITH, SIMILAR_TO, SEMANTICALLY_RELATED, CONTAINS_FILE, CONTAINS_FOLDER, INFRA_MAPS, DEPENDS_ON, DEPLOYS, CONNECTS_TO)

---

## Phase 2: US8 - Graph Search (search_graph)

- [ ] T012 [US8] Implement `_graph_search_collection(label, name_pattern, min_degree, max_degree, limit, offset)` — TF-IDF + degree filter over code_index + code_edges
- [ ] T013 [US8] Implement `cmd_graph_search(args)` CLI command with --label, --name-pattern, --min-degree, --max-degree, --limit, --offset, --tier
- [ ] T014 [US8] Add test: graph search by label returns correct nodes
- [ ] T015 [US8] Add test: graph search by name_pattern regex returns matching symbols
- [ ] T016 [US8] Add test: graph search with degree filtering (min_degree/max_degree)
- [ ] T017 [US8] Add test: graph search pagination (limit/offset)
- [ ] T018 [US8] Add test: graph search returns edge_types and degree per node

---

## Phase 3: US9 - Graph Trace (trace_path)

- [ ] T019 [US9] Extend `_bfs()` to support `--direction both` (currently only outbound)
- [ ] T020 [US9] Implement risk label detection: high_fan_out (>10 deps), circular_dep, deep_chain (>5)
- [ ] T021 [US9] Implement `cmd_graph_trace(args)` CLI command with --symbol, --direction, --depth, --risk-labels, --tier
- [ ] T022 [US9] Add test: trace outbound returns correct reachable nodes
- [ ] T023 [US9] Add test: trace inbound returns correct caller nodes
- [ ] T024 [US9] Add test: trace both directions returns union of inbound+outbound
- [ ] T025 [US9] Add test: trace with --risk-labels annotates high fan-out edges
- [ ] T026 [US9] Add test: trace depth limit prevents infinite traversal

---

## Phase 4: US10 - Cypher-like Query (query_graph)

- [ ] T027 [US10] Implement Cypher-like query parser (MATCH/WHERE/RETURN/LIMIT subset) in pure Python
- [ ] T028 [US10] Implement row ceiling enforcement (100k rows max) with truncation warning
- [ ] T029 [US10] Implement `cmd_graph_query(args)` CLI command
- [ ] T030 [US10] Add test: Cypher MATCH query returns correct rows
- [ ] T031 [US10] Add test: Cypher WHERE clause filters results
- [ ] T032 [US10] Add test: Cypher LIMIT caps result count
- [ ] T033 [US10] Add test: Row ceiling enforced (query > 100k rejected/truncated)

---

## Phase 5: US10 - Detect Changes

- [ ] T034 [US10] Implement `_detect_changes(git_diff_path)` — parse `git diff --name-only`, map to code_index entries
- [ ] T035 [US10] Implement `cmd_graph_detect_changes(args)` CLI command with --diff-path, --tier
- [ ] T036 [US10] Add test: detect-changes maps changed files to affected symbols
- [ ] T037 [US10] Add test: detect-changes with tier=Verifier returns both directions

---

## Phase 6: US10 - Code Snippet & Architecture

- [ ] T038 [US10] Implement `_get_code_snippet(qualified_name, context_lines)` — read source file by qualified name
- [ ] T039 [US10] Implement `cmd_graph_get_snippet(args)` CLI command
- [ ] T040 [US10] Implement `_get_architecture(tier)` — modules, dependencies, entry points, circular deps
- [ ] T041 [US10] Implement `cmd_graph_architecture(args)` CLI command
- [ ] T042 [US10] Add test: get-snippet returns source by qualified name
- [ ] T043 [US10] Add test: architecture returns module dependency overview

---

## Phase 7: US11 - ADR Management

- [ ] T044 [US11] Implement `_adr_add(title, status, rationale, consequences, actor)` — create ADR
- [ ] T045 [US11] Implement `_adr_list()` — list all ADRs
- [ ] T046 [US11] Implement `_adr_get(adr_id)` — get specific ADR
- [ ] T047 [US11] Implement `cmd_graph_adr(args)` CLI command (add/list/get)
- [ ] T048 [US11] Add test: ADR create returns adr_id
- [ ] T049 [US11] Add test: ADR list returns all ADRs
- [ ] T050 [US11] Add test: ADR get returns specific ADR

---

## Phase 8: US11 - Trace Ingestion & Project Lifecycle

- [ ] T051 [US11] Implement `_ingest_traces(trace_file, actor)` — parse trace JSON, add TraceEntry + CodeEdge
- [ ] T052 [US11] Implement `cmd_graph_ingest_traces(args)` CLI command
- [ ] T053 [US11] Implement `_list_projects()` — list indexed projects
- [ ] T054 [US11] Implement `_delete_project(project_name)` — remove project + graph data
- [ ] T055 [US11] Implement `cmd_graph_list_projects(args)` and `cmd_graph_delete_project(args)`
- [ ] T056 [US11] Add test: trace ingestion adds TraceEntry and edges
- [ ] T057 [US11] Add test: list-projects returns project metadata
- [ ] T058 [US11] Add test: delete-project removes nodes and edges

---

## Phase 9: Evidence Tiers & Coverage (US10)

- [ ] T059 [US10] Implement evidence tier depth on graph commands: Scout (provisional), Verify (task-directed), Auditor (full both-directions + limitations)
- [ ] T060 [US10] Extend `graph coverage` with `--tier` flag and edge_type coverage gaps
- [ ] T061 [US10] Add test: Scout tier returns provisional results with fewer calls
- [ ] T062 [US10] Add test: Auditor tier returns both call directions + unresolved limitations

---

## Phase 10: Polish (US8-US11)

- [ ] T063 [US8-US11] Run full test suite: 56+ tests passing
- [ ] T064 [US8-US11] Verify no MCP/Rust/Cargo references in new code
- [ ] T065 [US8-US11] Update AGENTS.md with new graph commands (search, trace, query, detect-changes, get-snippet, architecture, adr, ingest-traces, list-projects, delete-project, coverage --tier)
- [ ] T066 [US8-US11] Run `hakoagent bug_scan` on new graph code
- [ ] T067 [US8-US11] Run `hakoagent vigilance` — constitution check pass

---

**Design artifacts ready**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/codebase-knowledge-graph-interface.md`, `quickstart.md`

Plan workflow complete. Ready to proceed to `/speckit-implement`.
