# Implementation Plan: HakoAgent Memory, Context & History System (Non-MCP, Embedded Hakodb)

**Branch**: `007-hakodb-memory-context-history` | **Date**: 2026-10-29 | **Spec**: `specs/007-hakodb-memory-context-history/spec.md`

**Input**: Feature specification from `/specs/007-hakodb-memory-context-history/spec.md`

**Reference**: `/home/web/.claude/skills/codebase-memory/SKILL.md` — Codebase Memory knowledge graph MCP. Adapted to Python-only, non-MCP, embedded hakodb. The MCP skill's 15 tools and Scout/Verify/Auditor tiers are re-implemented using embedded hakodb FFI + Python stdlib, no MCP server.

## Summary

Extend the Python-only HakoAgent into a strong, smart memory, context, and history system backed by the embedded prebuilt hakodb shared library via ctypes FFI — **no MCP server, no external plugin**. Incorporates patterns from the MCP codebase-memory skill: knowledge graph trace (inbound/outbound/both), search by name pattern, shortest-path, impact analysis, index coverage check, and Scout/Verify/Auditor evidence tiers — all implemented with embedded hakodb + Python stdlib. Collections: sessions, events, decisions, findings, code_index, tasks, context_cache, skills, lessons_learned, revisions. All runtime data under `.hakoagent/` or project root.

## Technical Context

**Language/Version**: Python 3.11+ (stdlib only, no external dependencies, no build step)

**Primary Dependencies**: Python standard library (`ctypes`, `json`, `hashlib`, `uuid`, `time`, `datetime`, `re`, `math`, `collections`, `heapq`, `pathlib`); prebuilt hakodb shared library (`lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so`) via `ctypes`; C ABI header `lib/hakodb.h` (v0.20.0, hash-verified)

**Storage**: Embedded hakodb via FFI for writes/reads, JSON file fallback under `.hakoagent/memory/<collection>/` (11 collections including `revisions`), index files under `.hakoagent/_indices/`

**Testing**: `test_hakoagent.py` (Python stdlib unittest, 31+ tests); new tests for FFI, append-only guard, context cache, revisions, graph trace, shortest-path, impact, coverage

**Target Platform**: Linux (x86_64 glibc2.28-el8), cross-platform Python

**Project Type**: Single Python CLI script (`hakoagent`) at project root

**Performance Goals**: Single-agent write/read via FFI < 1s; cache hit ratio ≥ 50%; cache hit response < 100ms; LLM calls reduced by ≥ N% per task

**Constraints**: No MCP, no Rust, no Cargo, no build step; embedded (no server/daemon); all files under `.hakoagent/` or project root; Python stdlib only; graceful fallback to JSON when hakodb unavailable

**Scale/Scope**: Single project per hakodb file; multiple agents share same `.hakoagent/hakoagent.db` via filesystem; 11 collections; actor-attributed documents

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Status | Notes |
|-----------------------|--------|-------|
| Smart Memory | Met | Sessions, events, decisions, findings, tasks, skills, revisions via hakodb FFI |
| Anti-Lupa | Met | Query findings + skills + revisions via recall before new tasks |
| Chronology & History | Met | Append-only events with ISO 8601 + immutable revisions (history) |
| Consistency | Met | Template output, naming, error handling consistent across agents |
| Cross-Model Consistency | Met | Flow identical regardless of LLM model |
| Vigilance | Met | Existing vigilance checker + revision + coverage detection |
| Clear Target | Met | Task with target + DoD |
| Codebase Fluency | Met | Code_index + graph trace/shortest-path/impact |
| Context Frugality | Met | Context cache TTL + recall reduces LLM calls |
| Self Skill Improvement | Met | Skills collection + skill engine + bug-fix skill extraction (US7) |
| Python Only | Met | No MCP, no Rust/Cargo/build; stdlib only |
| Real Hakodb FFI | Met | libhakodb .so + hakodb.h via ctypes |
| Code Quality | Met | Clean Python, no bare except, no hardcoded secrets |
| Testing | Met | Unit tests for all new FFI/graph functions |
| Maintainability | Met | Docs updated with code, no stale references |

No violations. Constitution check PASSED.

## Project Structure

### Documentation (this feature)

```text
specs/007-hakodb-memory-context-history/
├── spec.md          # Feature specification
├── plan.md          # Implementation plan (this file)
├── research.md      # Phase 0 output (MCP skill pattern analysis)
├── data-model.md    # Phase 1 output (entities, collections, schemas)
├── quickstart.md    # Phase 1 output (validation scenarios)
├── contracts/       # Phase 1 output (tool contracts)
└── tasks.md         # Phase 2 output (create via /speckit-tasks)
```

### Source Code (repository root)

```text
hakoagent                      # Python CLI script (stdlib only) — extended with FFI + graph functions
lib/
├── libhakodb-x86_64-unknown-linux-glibc2.28-el8.so   # Prebuilt hakodb shared library (v0.20.0)
├── hakodb.h                                               # Hakodb C ABI header (v0.20.0, hash-verified)
└── SHA256SUMS.txt                                         # Release checksums
.hakoagent/                      # Runtime data directory
├── hakoagent.db                 # Hakodb database file (via FFI)
├── memory/                      # JSON files per collection (fallback / dual-write)
│   ├── sessions/, events/, decisions/, findings/, code_index/,
│   │   tasks/, context_cache/, skills/, lessons_learned/, revisions/
├── skills/                      # Skill Markdown files
├── sessions/                    # Session exports (optional)
├── logs/                        # Operation logs (optional)
└── _indices/                    # Index definitions + coverage tracking
    ├── definitions.json         # Index definitions (secondary, fts, composite, vector)
    ├── coverage.json            # Per-file index coverage status
    ├── ram_indexes.bin          # In-memory index snapshot
    ├── index.log                # Index WAL
    └── snapshots/               # Index snapshots
specs/                         # Feature specs (001-007)
docs/                          # T057 perf, T059 security
examples/
└── performance_benchmark.rs
test_hakoagent.py              # Python stdlib unittest (31+ tests)
install.sh                     # Project installer
INSTALL.md                     # Installation guide
AGENTS.md                      # Agent-facing instructions
```

**Structure Decision**: Single project structure (DEFAULT) — one Python CLI script `hakoagent` at project root, extended with real hakodb FFI + graph functions. All runtime data under `.hakoagent/` or project root. No MCP, no Rust, no Cargo, no separate crate.

## Phase 0: Outline & Research

### Unknowns from Technical Context

| Unknown | Status | Resolution |
|---------|--------|----------|
| Hakodb FFI signatures confirmed vs real .so | Resolved | Verified `hk_engine_insert_json`, `hk_engine_get_json`, `hk_engine_delete`, `hk_engine_open`, `hk_engine_free`, `hk_string_free` |
| MCP skill patterns adapted to non-MCP | Resolved | 15 MCP tools → Python FFI functions; Scout/Verify/Auditor tiers → evidence depth levels |
| Context efficiency measurement | Resolved | `llm_calls_saved` per cache entry + aggregate stats |
| Multi-agent sync without MCP | Resolved | Shared filesystem hakodb + `actor` attribution |
| Graph trace/shortest-path over code_index | Resolved | BFS/Dijkstra over `code_index` dependency edges |
| Index coverage + source fallback | Resolved | `.hakoagent/_indices/coverage.json` + read/grep fallback |
| Fallback when library missing | Resolved | Graceful fallback to JSON files |

### Research Findings

**MCP codebase-memory skill analysis** (`/home/web/.claude/skills/codebase-memory/SKILL.md`):

The MCP skill exposes 15 tools for codebase knowledge graph queries:
- Index management: `index_repository`, `index_status`, `list_projects`, `delete_project`
- Graph queries: `search_graph`, `search_code`, `trace_path`, `detect_changes`, `query_graph`
- Schema/architecture: `get_graph_schema`, `get_code_snippet`, `get_architecture`
- Coverage: `check_index_coverage`
- Other: `manage_adr`, `ingest_traces`

Evidence tiers:
- **Scout (Tier 1)**: Fast positive lookup, few graph calls, targeted source checks. Provisional results only.
- **Verify (Tier 2, default)**: Task-directed searches, relevant trace directions, exact snippets for material claims.
- **Auditor (Tier 3)**: Bounded-scope full verification, current graph generation, complete pagination, both call directions, explicit limitations.

Edge types: CALLS, HTTP_CALLS, ASYNC_CALLS, SPAWNS, DATA_FLOWS, IMPORTS, DEFINES, DEFINES_METHOD, OVERRIDE, USAGE, CALL_REFERENCE, CONFIGURES, REFERENCES_FILE, MENTIONS, FILE_CHANGES_WITH, SIMILAR_TO, SEMANTICALLY_RELATED, CONTAINS_FILE, CONTAINS_FOLDER, INFRA_MAPS, DEPENDS_ON, DEPLOYS, CONNECTS_TO

**Adaptation to embedded hakodb (non-MCP)**:

| MCP capability | HakoAgent adaptation (Python + hakodb FFI) |
|----------------|--------------------------------------------|
| `index_repository` / `index_status` | `hakoagent index` → builds `code_index` + `coverage.json` |
| `search_graph(name_pattern=...)` | `hakoagent recall <query>` + TF-IDF over `code_index` |
| `trace_path(direction=...)` | `hakoagent graph trace <node> <dir> <depth>` — BFS over `code_index.dependensi` |
| `query_graph` (Cypher) | `hakoagent graph shortest-path <from> <to>` — Dijkstra |
| `detect_changes()` | `hakoagent vigilance` + revision tracking |
| `get_code_snippet` | `hakoagent recall` returns file_path + symbol + line |
| `get_architecture` | `hakoagent graph` + impact analysis (blast radius) |
| `check_index_coverage` | `.hakoagent/_indices/coverage.json` + source grep fallback |
| Scout/Verify/Auditor tiers | Evidence depth parameter on graph commands |

No MCP server or plugin — all via embedded hakodb FFI + Python stdlib, filesystem-level multi-agent sharing.

Output: `research.md` documenting MCP skill pattern analysis and non-MCP adaptation.

## Phase 1: Design & Contracts

### Data Model (`data-model.md`)

Entities from the feature spec:

| Entity | Key Attributes | Relationships |
|--------|---------------|---------------|
| Session | session_id, started_at, ended_at, status, summary, model_used, actor | 1:N with Event |
| Event | event_id, timestamp (ISO 8601), session_id, actor, action, target, change_type, metadata | session_id → Session |
| Decision | decision_id, title, rationale, consequences, event_id, actor | event_id → Event |
| Finding | finding_id, content, finding_type, file, event_id, actor | event_id → Event |
| Task | task_id, title, target, definition_of_done, priority, status, dod_verified, actor | — |
| Skill | skill_id, name, description, context_tags, success_count, failure_count, status, actor | — |
| CodeIndex | entry_id, file_path, symbol_name, symbol_type, dependensi, line_number, file_hash, actor | — |
| Revision (History) | revision_id, doc_id, doc_collection, previous_content, new_content, changed_by (actor), changed_at (ISO 8601), immutable | doc_id → source document |
| ContextCacheEntry | cache_key, query, summary, source_documents, created_at, ttl_seconds, hit_count, llm_calls_saved | — |
| IndexCoverage | file_path, indexed, last_indexed_at, coverage_gaps, source_fallback | — |

State transitions:
- Session: active → ended (ended_at set)
- Task: todo → in-progress → done (dod_verified=true) / blocked
- Skill: active → deprecated / archived
- Event: append-only (create only)
- Revision: immutable (create only)

Validation rules:
- Event: event_id unique; append-only guard rejects duplicates
- Task: target and definition_of_done not empty
- All documents: actor field present
- ContextCacheEntry: cache_key unique; ttl_seconds > 0
- Revision: immutable — cannot be updated/deleted

### Interface Contracts (`contracts/`)

**File**: `contracts/hakodb-memory-context-interface.md`

| Tool | Parameter | Return |
|------|-----------|--------|
| `hakoagent.init` | db_path, collections | status, collections_created |
| `hakoagent.event_log` | action, target, actor, session_id, change_type, metadata | event_id, timestamp |
| `hakoagent.recall` | query, limit, actor, collection | context_results, cache_hit (bool), llm_calls_saved |
| `hakoagent.cache.stats` | — | total_hits, total_misses, eviction_count, cache_size, llm_calls_saved |
| `hakoagent.cache.get` | query | summary, cache_hit (bool) |
| `hakoagent.cache.put` | query, summary, ttl_seconds | cache_key, status |
| `hakoagent.task.create` | title, target, definition_of_done, priority, actor | task_id, status |
| `hakoagent.task.complete` | task_id, dod_verified, actor | status, completed_at |
| `hakoagent.skill.add` | name, content (Markdown), actor | skill_id, status |
| `hakoagent.skill.list` | — | skills_list (name, id, status, success, failure) |
| `hakoagent.events` | limit, session_id, actor | events_list |
| `hakoagent.index` | root_path | indexed_count |
| `hakoagent.graph.trace` | node, direction, max_depth | visited_nodes, edges_traversed |
| `hakoagent.graph.shortest-path` | from_node, to_node | path_nodes, total_cost |
| `hakoagent.graph.dependents` | node_id | dependent_nodes |
| `hakoagent.graph.dependents-reverse` | node_id | dependent_reverse_nodes |
| `hakoagent.graph.impact` | file_path | blast_radius_nodes |
| `hakoagent.graph.coverage` | file_paths | coverage_status_per_file |
| `hakoagent.vigilance` | root_path | vigilance_report |
| `hakoagent.revision.list` | doc_id, doc_collection | revisions_list |

Return value always in JSON format for harness agent parsing.

### Quickstart Validation Guide (`quickstart.md`)

**Prerequisites**:
- Python 3 (stdlib only, no external dependencies)
- Prebuilt hakodb library at `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` + header `lib/hakodb.h`
- Write permission in working directory

**Setup commands**:
```bash
# Initialize database
./hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

**Test/run commands**:
```bash
# Single-agent memory write + read
./hakoagent event_log "code_read" "src/main.py" "agent-a" "info" '{"file": "src/main.py"}'
./hakoagent recall "main.py" --limit 5

# Context efficiency: second identical query within TTL → cache hit (no LLM call)
./hakoagent recall "main.py" --limit 5
./hakoagent cache stats

# Multi-agent context sharing: agent-a writes, agent-b reads
./hakoagent event_log "decision" "use Python FFI" "agent-a" "info" '{"rationale": "stdlib only"}'
./hakoagent recall "Python FFI" --limit 5  # agent-b sees agent-a's event

# Graph trace (like MCP trace_path)
./hakoagent graph trace func_a out 3
./hakoagent graph trace func_a in 2

# Shortest path (like MCP query_graph)
./hakoagent graph shortest-path func_a func_c

# Impact analysis (blast radius)
./hakoagent impact src/main.py

# Index coverage (like MCP check_index_coverage)
./hakoagent graph coverage src/main.py src/utils.py

# Task
./hakoagent task create "Implement memory system" "Embedded hakodb memory works" "All tests pass" P1 "agent-a"
./hakoagent task list

# Events (history)
./hakoagent events

# Full test suite
python3 test_hakoagent.py
```

**Expected outcomes**:
- `./hakoagent event_log`: Creates append-only event with unique event_id and ISO 8601 timestamp
- `./hakoagent recall`: Returns relevant context ranked by similarity; second identical query within TTL is cache hit (no LLM call)
- Multi-agent: Document written by agent-A readable by agent-B via same hakodb
- `./hakoagent graph trace`: Returns all nodes reachable via dependencies (inbound/outbound/both)
- `./hakoagent graph shortest-path`: Returns shortest dependency chain
- `./hakoagent impact`: Returns blast radius (transitive dependents)
- `./hakoagent graph coverage`: Returns per-file coverage status with source fallback
- `./hakoagent cache stats`: Shows hits, misses, hit rate, cache size, eviction count, llm_calls_saved
- `python3 test_hakoagent.py`: 31+ tests passing

### Re-evaluate Constitution Check (post-design)

| Constitution Principle | Status Post-Design | Notes |
|-----------------------|-------------------|-------|
| Smart Memory | Met | 11 collections via FFI + JSON fallback |
| Anti-Lupa | Met | Recall queries findings + skills + revisions |
| Chronology & History | Met | Append-only events + immutable revisions |
| Consistency | Met | JSON return format, standard tool names |
| Cross-Model Consistency | Met | Same flow for all LLM models |
| Vigilance | Met | Existing vigilance + revision + coverage detection |
| Clear Target | Met | Task with target + DoD |
| Codebase Fluency | Met | Code_index + graph trace/shortest-path/impact |
| Context Frugality | Met | Context cache TTL + recall reduces LLM calls |
| Self Skill Improvement | Met | Skills + lessons_learned + bug-fix skill extraction (US7) |
| Python Only | Met | stdlib only, no MCP/Rust/Cargo |
| Real Hakodb FFI | Met | ctypes to libhakodb .so |
| Code Quality | Met | No bare except, no hardcoded secrets |
| Testing | Met | 31+ tests passing |
| Maintainability | Met | Docs current, no stale references |

No violations. Constitution check PASSED post-design.

---

**Design artifacts ready**: `research.md`, `data-model.md`, `contracts/hakodb-memory-context-interface.md`, `quickstart.md`

Plan workflow complete. Ready to proceed to `/speckit-tasks`.
