# Tasks: HakoAgent - Caching & Graph Traversal (Python)

**Status**: All user stories implemented. Task list reflects current state of `hakoagent` (Python, stdlib only).

## Implemented (all verified with `test_hakoagent.py` — 31 tests passing)

### Phase 1: Setup — DONE
- [x] Python script `hakoagent` at project root (stdlib only, no build step)
- [x] Installed to `~/.local/bin/hakoagent`
- [x] `.hakoagent/` directory with `memory/` collections, `skills/`, `sessions/`, `logs/`

### Phase 2: Foundational — DONE
- [x] Storage layer: JSON files under `.hakoagent/memory/<collection>/` (save/load/delete/scan)
- [x] Event log: append-only events to `events` collection
- [x] Current session management (auto-started at import)

### Phase 3: User Story 1 - Context Cache — DONE
- [x] `hakoagent cache stats` — hits, size, eviction count
- [x] `hakoagent cache get <query>` — TTL-valid cache retrieval
- [x] `hakoagent cache put <query> <summary> [ttl]` — store with default TTL 300s
- [x] `hakoagent recall <query> [--limit N]` — cache check first, then FTS-style search, store result in cache
- [x] Active eviction: TTL expiry + LRU (lowest hit_count) when cache exceeds MAX_CACHE_SIZE (100)
- [x] Eviction counter persisted to disk

### Phase 4: User Story 2 - Graph Traversal — DONE
- [x] `hakoagent index` — scans codebase, extracts dependencies (import/use/require/include), resolves to entry IDs
- [x] `hakoagent graph traverse <node> <direction> <max_depth>` — BFS with depth limit
- [x] `hakoagent graph shortest-path <from> <to>` — Dijkstra weighted shortest path
- [x] `hakoagent graph dependents <node>` — incoming edges (who depends on this)
- [x] `hakoagent graph dependents-reverse <node>` — outgoing edges (this depends on whom)

### Phase 5: User Story 3 - Notifications — DONE
- [x] Every command logs to `events` collection (append-only)
- [x] `hakoagent events` — view chronological history

### CLI Commands — DONE
- [x] `hakoagent init --db <path> --collections all`
- [x] `hakoagent skill list | skill add <name> | skill get <skill_id>`
- [x] `hakoagent task list | task create <title> <target> <dod> [priority] | task complete <task_id>`
- [x] `hakoagent vigilance` — unused files, TODO/FIXME/XXX, constitution regression

## Remaining (nice-to-have, not blocking)

- [ ] `recall --limit` flag default is 5; verified working
- [ ] Add `recall --limit` documentation to INSTALL.md
- [ ] Persistent cache miss counter (currently always 0 in stats)
- [ ] Background auto-indexing (currently manual `hakoagent index`)

---

**Note**: Previous Rust implementation (`speckit-core/`, `cli/`) was removed — superseded by Python `hakoagent` script. All references to `hakodb`, `cbindgen`, `notify`, `ordered-float`, `cargo build` removed from docs.
