# Research Findings — Auto Codebase Indexing

**Feature**: 003-cache-graph-system  
**Date**: 2026-10-29  
**Status**: Complete

## Unknowns Resolution

No NEEDS CLARIFICATION items remain. All parameters were determined through the spec and prior clarifications:

| Unknown | Resolution | Source |
|---------|----------|--------|
| Default TTL for the context cache | 300 seconds (5 minutes) | Clarification Session 2026-10-29 |

## Technology Choices

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Python 3 (stdlib only) as the implementation language | No build step, easy to maintain, compatible with ctypes FFI to HakoDB | Rust (requires cargo build, external toolchain) |
| Prebuilt HakoDB shared library (`libhakodb-...so`) via ctypes | The native HakoDB library is used directly, `hakodb.h` as the ABI reference | Build from source with Rust/cargo (requires a Rust toolchain) |
| HakoDB embedded (via prebuilt .so) | Light footprint, no server/daemon needed, suits an in-process agent | SQLite (no native vector/graph support), PostgreSQL (requires a server) |
| LRU eviction for the cache | Standard for cache management, memory efficient | FIFO (simpler but less optimal), LFU (more complex) |
| BFS for graph traversal | Fits level-by-level dependency exploration | DFS (goes deeper but can get stuck in the wrong branch) |
| Dijkstra for shortest path | Standard for weighted shortest path | BFS (only for unweighted), A* (needs a heuristic) |
| Manual indexing (`hakoagent index`) | Simple, no extra process management | Background thread / file watcher (requires process management, more complex) |

## Integration Patterns

- **FFI via ctypes**: Load `libhakodb-...so` and call C ABI functions such as `hk_engine_insert_json`, `hk_engine_get_json`, `hk_engine_delete`
- **Header reference**: `lib/hakodb.h` (v0.20.0, hash-verified) as the source of truth for C function signatures
- **HakoDB integration**: Memory Service for read/write of the `context_cache` and `code_index` collections via FFI or JSON files
- **CLI integration**: `./hakoagent init` to initialize the database, `./hakoagent index` to scan the codebase

## Best Practices

- Every indexed file is recorded as an append-only event in the `events` collection
- File hashes are used to detect changes (avoid re-indexing the same file)
- Ignored directories: node_modules, .git, target, .hakoagent, build output
- An error on one file does not stop indexing of other files
- A concise notification is sent to the agent after every indexing session finishes
- Cache TTL of 300 seconds to balance freshness against reduced LLM calls
- Graph traversal with a visited set to avoid unbounded cycles
