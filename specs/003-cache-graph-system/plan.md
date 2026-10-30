# Implementation Plan: System Caching and Graph Traversal Tools

**Branch**: `003-cache-graph-system` | **Date**: 2026-10-29 | **Spec**: `specs/003-cache-graph-system/spec.md`

**Input**: Feature specification from `/specs/003-cache-graph-system/spec.md`

## Summary

System Caching and Graph Traversal Tools is a feature that lets HakoAgent store context search results in a cache (reducing LLM endpoint calls) and explore codebase dependencies through graph traversal (BFS, Dijkstra, dependents lookup). This feature rounds out HakoAgent with context frugality and a deeper understanding of the codebase.

## Technical Context

**Language/Version**: Python 3.11+ (stdlib only, no external dependencies, no build step)

**Primary Dependencies**: Python standard library only; prebuilt HakoDB shared library (`lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so`) loaded via `ctypes`, C ABI header `lib/hakodb.h` (v0.20.0)

**Storage**: JSON files under `.hakoagent/memory/<collection>/` (9 collections: sessions, events, decisions, findings, code_index, tasks, context_cache, skills, lessons_learned), with optional HakoDB FFI passthrough via the prebuilt shared library

**Testing**: `test_hakoagent.py` (Python stdlib unittest, 31 tests)

**Target Platform**: Linux (x86_64 glibc2.28-el8), cross-platform Python

**Project Type**: Single Python CLI script (`hakoagent`) at project root

**Performance Goals**: Cache hit ratio ≥ 50%, cache hit response time < 100ms, graph traversal up to 10 levels deep

**Constraints**: No build step; embedded (no server/daemon); frugal with context and endpoint requests; all files under `.hakoagent/` or the project root; no references to hakoagent; skills in Markdown format under `.hakoagent/skills/`

**Scale/Scope**: Single project per database; `context_cache` collection for caching, `code_index` for the graph; source code files (.py, .js, .ts, .go, .rs, etc.)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Status | Notes |
|-------------------|--------|---------|
| Smart Memory | Met | Caching and graph traversal results stored in HakoDB |
| Anti-Lupa | Met | Cache stays stored for reuse |
| Kronologi & Histori | Met | Every caching and traversal operation recorded as an append-only event |
| Consistency | Met | Standard output template for caching and traversal notifications |
| Cross-Model Consistency | Met | Same caching and traversal flow for all LLM models |
| Vigilance | Met | Detects expired caches, graph cycles, deleted files |
| Clear Target | Met | Every caching and traversal task has a target and DoD |
| Codebase Fluency | Met | Graph traversal for codebase navigation |
| Context Frugality | Met | Cache reduces LLM endpoint calls |
| Self Skill Improvement | Met | Successful caching and traversal patterns can be extracted as skills |

No violations. Constitution check PASSED.

## Project Structure

### Documentation (this feature)

```text
specs/003-cache-graph-system/
├── spec.md          # Feature specification (/hakoagent.specify output)
├── plan.md          # Technical plan (this file, /hakoagent.plan output)
├── research.md      # Phase 0 output (/hakoagent.plan command)
├── data-model.md    # Phase 1 output (/hakoagent.plan command)
├── quickstart.md    # Phase 1 output (/hakoagent.plan command)
├── contracts/       # Phase 1 output (/hakoagent.plan command)
└── tasks.md         # Phase 2 output (/hakoagent.tasks command - NOT created by /hakoagent.plan)
```

### Source Code (repository root)

```text
.hakoagent/                      # HakoAgent data directory (runtime data)
├── hakoagent.db                 # HakoDB database (single file, via FFI)
├── skills/                      # Skill files in Markdown format
├── sessions/                    # Session exports (optional)
├── logs/                        # Operation logs (optional)
└── memory/                      # JSON files per collection (9 collections)

lib/
├── libhakodb-x86_64-unknown-linux-glibc2.28-el8.so   # Prebuilt HakoDB shared library (v0.20.0)
├── hakodb.h                                               # HakoDB C ABI header (v0.20.0)
└── SHA256SUMS.txt                                         # Release checksums

hakoagent                      # Python CLI script (stdlib only, project root)
lib/                           # HakoDB prebuilt lib + header
specs/                         # Feature specs (001-005)
docs/                          # T057 perf, T059 security
examples/
├── performance_benchmark.rs
test_hakoagent.py              # Python stdlib unittest (31 tests)
install.sh                     # Project installer
INSTALL.md                     # Installation guide
AGENTS.md                      # Agent-facing instructions
```

**Structure Decision**: Single project structure (DEFAULT) — one Python CLI script `hakoagent` at project root, stdlib only, no build step. HakoDB prebuilt shared library + C header live in `lib/`. All runtime data stays under `.hakoagent/` or project root.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations. This section is left empty.

---

## Phase 0: Outline & Research

### Unknowns from Technical Context

No NEEDS CLARIFICATION items remain. All parameters were determined through the spec and prior clarifications:

| Unknown | Status | Resolution |
|---------|--------|----------|
| Default cache TTL | Resolved | 300 seconds (5 minutes) (Clarification Session 2026-10-29) |

### Research Findings (research.md)

No research task is required because all unknowns have been resolved. `research.md` is recorded as "no unresolved clarifications".

**Output**: `research.md` noting that all NEEDS CLARIFICATION items were resolved previously.

---

## Phase 1: Design & Contracts

### Data Model (`data-model.md`)

Entities extracted from the feature spec:

| Entity | Key Attributes | Relationships |
|---------|--------------|----------|
| CacheEntry | cache_key, query, summary, source_documents, created_at, ttl_seconds, hit_count | — |
| GraphNode | node_id, node_type (file/function/class/trait), file_path, symbol_name | — |
| GraphEdge | edge_id, from_node, to_node, edge_type (import/call/depends_on), weight | — |
| GraphTraversalResult | traversal_id, start_node, visited_nodes, edges_traversed, timestamp, status | — |
| CacheStats | total_hits, total_misses, eviction_count, cache_size | — |

State transitions:
- CacheEntry: created → hit (on retrieval) → expired (after TTL) → evicted (LRU)
- GraphTraversalResult: started → completed / failed
- GraphNode: created → updated (when file changes) → deleted (when file removed)

Validation rules:
- CacheEntry: cache_key must be unique, ttl_seconds must be > 0
- GraphEdge: from_node and to_node must be valid (exist in GraphNode)
- GraphTraversalResult: start_node must be valid, status must be one of started/completed/failed

### Interface Contracts (`contracts/`)

HakoAgent exposes a tool calling interface for caching and graph traversal. The following contracts are defined:

**File**: `contracts/cache-graph-interface.md`

| Tool | Parameters | Return |
|------|-----------|--------|
| `hakoagent.cache.get` | query, limit | context_results, cache_hit (bool) |
| `hakoagent.cache.put` | query, summary, ttl_seconds | cache_key, status |
| `hakoagent.cache.stats` | — | total_hits, total_misses, eviction_count, cache_size |
| `hakoagent.graph.traverse` | start_node, direction, max_depth | visited_nodes, edges_traversed |
| `hakoagent.graph.shortest-path` | from_node, to_node | path_nodes, total_cost |
| `hakoagent.graph.dependents` | node_id | dependent_nodes |
| `hakoagent.graph.dependents-reverse` | node_id | dependent_reverse_nodes |
| `hakoagent.events` | limit, session_id | events_list (including caching and traversal events) |

Return values are always in JSON format for easy parsing by the harness agent.

### Quickstart Validation Guide (`quickstart.md`)

**Prerequisites**:
- Python 3 (stdlib only, no external dependencies)
- Write permission in the project working directory
- HakoDB database initialized (`./hakoagent init --db ./.hakoagent/hakoagent.db --collections all`)
- Prebuilt HakoDB library available at `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` + header `lib/hakodb.h`

**Setup commands**:
```bash
# Initialize the database
./hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

**Test/run commands**:
```bash
# Test cache
./hakoagent recall "error handling Rust"  # First call - LLM call
./hakoagent recall "error handling Rust"  # Second call - cache hit
./hakoagent cache stats                   # View cache statistics

# Test graph traversal
./hakoagent graph traverse func_a out 3
./hakoagent graph shortest-path func_a func_c
./hakoagent graph dependents n2
./hakoagent graph dependents-reverse n1

# Run the entire test suite
python3 test_hakoagent.py
```

**Expected outcomes**:
- `./hakoagent recall`: Same query twice → cache hit (no LLM call)
- `./hakoagent cache stats`: Shows total_hits, total_misses, eviction_count
- `./hakoagent graph traverse`: Returns all nodes connected from start_node
- `./hakoagent graph shortest-path`: Returns the shortest path from from_node to to_node
- `./hakoagent graph dependents`: Returns all files importing a given file
- `python3 test_hakoagent.py`: 31 tests passing

### Re-evaluate Constitution Check (post-design)

| Constitution Principle | Post-Design Status | Notes |
|-------------------|-------------------|---------|
| Smart Memory | Met | Caching and traversal results stored in HakoDB |
| Anti-Lupa | Met | Cache stays stored for reuse |
| Kronologi & Histori | Met | Every operation recorded as an append-only event |
| Consistency | Met | Standard output template |
| Cross-Model Consistency | Met | Same caching and traversal flow for all LLMs |
| Vigilance | Met | Detects expired caches, graph cycles |
| Clear Target | Met | Every caching and traversal task has a target and DoD |
| Codebase Fluency | Met | Graph traversal for codebase navigation |
| Context Frugality | Met | Cache reduces LLM endpoint calls |
| Self Skill Improvement | Met | Caching and traversal patterns can be extracted as skills |

No violations. Constitution check PASSED post-design.

---

**Design artifacts ready: `research.md`, `data-model.md`, `contracts/cache-graph-interface.md`, `quickstart.md`**

Plan workflow complete. Ready to proceed to `/hakoagent-tasks`.
