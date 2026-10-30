# Implementation Plan: HakoAgent Enhancement (Vector + Graph + Multi-Agent)

**Spec**: specs/005-enhancements/spec.md  
**Status**: Draft  
**Build**: `python3 hakoagent <command>` (stdlib only, no build step)  
**Optional dependency**: `hakodb = "0.20"` with `net-sync` feature flag (optional, for Phase 2)

## Overview

This plan implements the enhancements from spec.md:
1. **Vector search** (HNSW via hakodb) — replace TF-IDF keyword scoring
2. **Typed graph edges** — replace single `dependinsi` with typed edges
3. **Change stream** — `watch_collection()` for real-time file watching
4. **Multi-agent sync** — `net-sync` / `cloud-sync` for team collaboration
5. **Auto-init** — no manual `init` required, auto-detects if DB exists

## Phase 1: Vector Search & Typed Graph Edges (Week 1)

### T001: Add `graph_edges` collection & vector storage

- [ ] Create `context_cache` entries with `vector_id` field
- [ ] Create `graph_edges` collection with fields: edge_id, from_node, to_node, edge_type, weight
- [ ] Edge types: `imports`, `calls`, `depends_on`, `data_flows`, `test_of`, `defines`, `imports_type`, `imports_value`
- [ ] Update `code_index` entries with `vector_id` field (link to code_vectors)

### T002: Implement vector search (TF-IDF fallback, later HNSW)

- [ ] Implement `cache_put_internal()` with vector embedding storage
- [ ] Implement `cache_get_internal(query)` with cosine similarity scoring
- [ ] Add `_vectorize_query()` using existing TF-IDF (placeholder until hakodb HNSW)
- [ ] Update `cmd_recall()` to use vector search + keyword scoring hybrid

### T003: Implement typed graph traversal

- [ ] `graph traverse <node> <dir> <depth> [--edge-type <type>]` — filter by edge type
- [ ] `graph shortest-path <from> <to> [--weighted]` — Dijkstra with edge weights
- [ ] `graph dependents <node> [--edge-type <type>]` — filter by edge type
- [ ] `graph dependents-reverse <node> [--edge-type <type>]` — filter by edge type

### T004: File change watcher (auto-reindex)

- [ ] `watch_collection("code_index")` — detect file changes
- [ ] Auto-reindex changed files on change event
- [ ] Update graph edges when dependencies change

---

## Phase 2: Hakodb FFI Integration (Week 2)

### T005: Add hakodb FFI binding layer

- [ ] Add `hakodb = { version = "0.20", features = ["net-sync"] }` dependency
- [ ] Create `hakodb_binding.py` with C ABI calls: `hk_engine_open`, `hk_engine_put`, `hk_engine_get`, `hk_engine_delete`, `hk_engine_watch_collection`
- [ ] Replace `save_doc/load_doc/delete_doc/scan_docs` with hakodb FFI calls
- [ ] Fallback to JSON files if hakodb .so not available

### T006: Migrate collections to hakodb

- [ ] Migrate `context_cache` to hakodb collections
- [ ] Migrate `code_index` to hakodb collections  
- [ ] Migrate `skills` to hakodb collections
- [ ] Migrate `tasks` to hakodb collections
- [ ] Migrate `events` to hakodb collections
- [ ] Migrate `indexing_run` to hakodb collections

### T007: Vector search via hakodb HNSW

- [ ] Replace TF-IDF with hakodb native HNSW vector search
- [ ] Add `vector_id` field to code_index entries
- [ ] Implement `hk_vector_search` via C ABI or Python wrapper

---

## Phase 3: Multi-Agent Sync (Week 3)

### T005: Add `hakoagent team sync` command

- [ ] `hakoagent team sync --push` — push local changes to remote
- [ ] `hakoagent team sync --pull` — pull remote changes
- `hakoagent team sync` — both push and pull

### T006: Implement notification system

- [ ] `hakoagent events` — view chronological history (already exists)
- [ ] Add `hakoagent notify` — emit notification event
- [ ] Real-time event streaming via `watch_collection("events")`

---

## Phase 4: Polish & Testing (Week 4)

### T007: Add unit tests

- [ ] Test graph traversal with typed edges
- [ ] Test vector search with mock vectors
- [ ] Test cache hit/miss tracking
- [ ] Test skill dedup/eviction
- [ ] Test graph shortest path with weighted edges

### T008: Update documentation

- [ ] Update `INSTALL.md` with new commands
- [ ] Update `AGENTS.md` with new skill commands
- [ ] Update `.opencode/skills/hakoagent/SKILL.md` with new commands

---

## Dependencies

| Dependency | Purpose | Optional |
|------------|---------|----------|
| `hakodb = "0.20"` | Embedded document database with HNSW + graph | Yes (optional, stdlib fallback) |
| `cbindgen` | C ABI header generation | Yes (if building from source) |

## Implementation Order

1. Complete Phase 1 (vector search + typed graph edges) — core feature
2. Phase 2 (hakodb FFI) — enables vector search & concurrency
3. Phase 3 (multi-agent sync) — team collaboration
4. Phase 4 (tests + docs) — quality assurance

## Success Criteria

- `hakoagent recall <query>` returns semantically relevant results (not just keyword match)
- `hakoagent graph traverse <node> out --edge-type calls` returns only call edges
- `hakoagent graph shortest-path <from> <to> --weighted` returns weighted shortest path
- `hakoagent index` automatically indexes and builds graph edges
- `hakoagent team sync --push/pull` syncs with remote (when hakodb net-sync available)
- All 31+ existing tests still pass

---

**End of plan.md.** Next: tasks.md with detailed task list.