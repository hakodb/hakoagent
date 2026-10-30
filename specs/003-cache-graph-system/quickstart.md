# Quickstart Validation Guide — System Caching and Graph Traversal

**Feature**: 003-cache-graph-system  
**Date**: 2026-10-29  
**Status**: Draft

## Purpose

End-to-end validation documentation proving the caching and graph traversal features work according to the specification and the HakoAgent constitution. This guide contains runnable scenarios, not full implementation code.

## Prerequisites

- Python 3 (stdlib only, no external dependencies)
- Write permission in the project working directory
- Prebuilt HakoDB library available at `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` + header `lib/hakodb.h`
- Codebase already indexed via `hakoagent index`

## Setup Commands

```bash
# 1. Initialize the HakoDB database and all collections
./hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

Expected output:
```
HakoAgent database initialized at: ./.hakoagent/hakoagent.db
Collections: ["sessions", "events", "decisions", "findings", "code_index", "tasks", "context_cache", "skills", "lessons_learned"]
```

Run `./hakoagent index` to scan the codebase and build `code_index`.

## Test/Run Commands

### Test 1: Cache miss and store (FR-001, FR-002)

```bash
# First time query - must call the LLM endpoint
./hakoagent recall "bagaimana implementasi error handling Python?"

# Second time same query - must come from cache
./hakoagent recall "bagaimana implementasi error handling Python?"

# View cache statistics
./hakoagent cache stats
```

**Expected**:
- First query: LLM endpoint call, result stored in cache
- Second query: cache hit, no LLM endpoint call
- `./hakoagent cache stats`: shows total_hits ≥ 1, total_misses ≥ 1

### Test 2: Cache expiry (FR-001, SC-004)

```bash
# Wait until the TTL elapses (5 minutes) or manipulate the TTL for testing
./hakoagent recall "bagaimana implementasi error handling Python?"
```

**Expected**: After the TTL elapses, the system calls the LLM endpoint again and refreshes the cache.

### Test 3: Graph traversal BFS (FR-003, FR-007)

```bash
# Traverse from the symbol in the in direction (who calls it)
./hakoagent graph traverse validate_input in 2
```

**Expected**: Returns all nodes reachable from `validate_input` within depth 2, without unbounded cycles.

### Test 4: Shortest path Dijkstra (FR-004)

```bash
# Find the shortest path from main to error_handler
./hakoagent graph shortest-path main error_handler
```

**Expected**: Returns the shortest dependency chain from `main` to `error_handler`.

### Test 5: Dependents lookup (FR-005, FR-006)

```bash
# See who uses the utils.rs file
./hakoagent graph dependents src/utils.rs

# See what is called by the utils.rs file
./hakoagent graph dependents-reverse src/utils.rs
```

**Expected**: Returns the list of nodes that depend on `src/utils.rs` and the nodes called by `src/utils.rs`.

### Test 6: Indexing notification (FR-008, SC-005)

```bash
# View event history including caching and traversal
./hakoagent events
```

**Expected**: The agent receives a concise notification about the number of files indexed and the success/error status.

## Expected Outcomes (Success Criteria)

| SC | Target | Expected Result |
|----|--------|----------------------|
| SC-001 | Cache hit ratio ≥ 50% | Repeated queries served ≥ 50% from cache |
| SC-002 | Context retrieval time < 100ms (cache hit) | Cache hit response < 100ms |
| SC-003 | Graph traversal depth ≤ 10 | Traversal never exceeds depth 10 without degradation |
| SC-004 | 0 expired cache entries | No expired entries still in use |
| SC-005 | 0 references to "hakoagent" | No occurrence of "hakoagent" in source/documentation |
| SC-006 | All files under `.hakoagent/` or root | All hakoagent-related files in the correct location |

## Validation Steps

1. Run all the Setup commands above
2. Run Test 1 through Test 6 in order
3. Verify the Expected Outcomes against the table above
4. If everything passes, the caching and graph traversal features are considered ready

## References

- Feature specification: `spec.md`
- Data model: `data-model.md`
- Interface contract: `contracts/cache-graph-interface.md`
- Constitution: `.specify/memory/constitution.md`
