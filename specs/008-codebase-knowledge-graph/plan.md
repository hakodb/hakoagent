# Implementation Plan: Codebase Knowledge Graph (US8)

**Branch**: `008-codebase-knowledge-graph` | **Date**: 2026-10-29 | **Spec**: `specs/008-codebase-knowledge-graph/spec.md`

**Input**: Feature specification from `/specs/008-codebase-knowledge-graph/spec.md`

**Reference**: `/home/web/.claude/skills/codebase-memory/SKILL.md` — Codebase Memory knowledge graph MCP. Adapted to Python-only, non-MCP, embedded hakodb. The MCP skill's 15 tools and Scout/Verify/Auditor tiers are re-implemented using embedded hakodb FFI + Python stdlib, no MCP server.

---

## Summary

Extend hakoagent's existing basic graph (US4) into a full codebase knowledge graph matching the MCP codebase-memory skill's 15 tools. Adds rich edge types (16+), Cypher-like query language, `search_graph` with label/name_pattern/degree filtering, `get_code_snippet`, `get_architecture`, `detect_changes`, `manage_adr`, `ingest_traces`, `list_projects`/`delete_project`, risk-labeled traces, and full Scout/Verify/Auditor evidence tiers with pagination — all implemented with embedded hakodb + Python stdlib, no MCP server.

---

## Technical Context

**Language/Version**: Python 3.11+ (stdlib only, no external dependencies, no build step)

**Primary Dependencies**: Python standard library (`ctypes`, `json`, `hashlib`, `uuid`, `time`, `datetime`, `re`, `math`, `collections`, `heapq`, `pathlib`, `subprocess` for git); prebuilt hakodb shared library via `ctypes`; C ABI header `lib/hakodb.h` (v0.20.0, hash-verified)

**Storage**: Embedded hakodb via FFI for writes/reads, JSON file fallback under `.hakoagent/memory/<collection>/`; new `code_edges` collection for typed edges; index files under `.hakoagent/_indices/`

**Testing**: `test_hakoagent.py` (Python stdlib unittest); new tests for knowledge graph: edge types, graph search, trace with risk labels, Cypher-like queries, detect_changes, code snippet, architecture, ADR, trace ingestion, project lifecycle, evidence tiers

**Target Platform**: Linux (x86_64 glibc2.28-el8), cross-platform Python

**Project Type**: Single Python CLI script (`hakoagent`) at project root

**Performance Goals**: Graph search < 1s; trace depth 3 < 2s; Cypher query < 3s; cache hit ratio ≥ 50%

**Constraints**: No MCP, no Rust, no Cargo, no build step; embedded (no server/daemon); all files under `.hakoagent/` or project root; Python stdlib only; graceful fallback to JSON when hakodb unavailable

**Scale/Scope**: Single project per hakodb file; multiple agents share same `.hakoagent/hakoagent.db` via filesystem; `code_index` + `code_edges` collections; actor-attributed graph entities

---

## Constitution Check

| Prinsip Konstitusi | Status | Catatan |
|-------------------|--------|---------|
| Smart Memory | Terpenuhi | CodeNode + CodeEdge entities via hakodb FFI |
| Anti-Lupa | Terpenuhi | Graph search + recall before structural changes |
| Kronologi & Histori | Terpenuhi | Trace entries + ADR history immutable |
| Consistency | Terpenuhi | JSON return format, standard tool names |
| Cross-Model Consistency | Terpenuhi | Same flow for all LLM models |
| Vigilance | Terpenuhi | detect_changes + coverage detection |
| Clear Target | Terpenuhi | Graph queries with clear targets |
| Codebase Fluency | Terpenuhi | Rich edge types + Cypher + architecture |
| Context Frugality | Terpenuhi | Graph queries reduce code exploration LLM calls |
| Self Skill Improvement | Terpenuhi | ADR + trace ingestion for architectural learning |
| Python Only | Terpenuhi | No MCP, no Rust/Cargo/build; stdlib only |
| Real Hakodb FFI | Terpenuhi | ctypes to libhakodb .so |
| Code Quality | Terpenuhi | Clean Python, no bare except, no hardcoded secrets |
| Testing | Terpenuhi | Unit tests for all new graph functions |
| Maintainability | Terpenuhi | Docs updated with code, no stale references |

No violations. Constitution check PASSED.

---

## Project Structure

### Documentation (this feature)

```text
specs/008-codebase-knowledge-graph/
├── spec.md          # Feature specification (this file's input)
├── plan.md          # Implementation plan (this file)
├── research.md      # Phase 0 output (MCP skill pattern gap analysis)
├── data-model.md    # Phase 1 output (CodeNode, CodeEdge, ADR, Trace, Project)
├── quickstart.md    # Phase 1 output (validation scenarios)
├── contracts/
│   └── codebase-knowledge-graph-interface.md  # Phase 1 output (tool contracts)
└── tasks.md         # Phase 2 output (create via /speckit-tasks)
```

### Source Code (repository root)

```text
hakoagent                      # Python CLI script — extended with knowledge graph functions
lib/
├── libhakodb-x86_64-unknown-linux-glibc2.28-el8.so   # Prebuilt hakodb shared library (v0.20.0)
├── hakodb.h                                               # Hakodb C ABI header (v0.20.0, hash-verified)
└── SHA256SUMS.txt                                         # Release checksums
.hakoagent/                      # Runtime data directory
├── hakoagent.db                 # Hakodb database file (via FFI)
├── memory/                      # JSON files per collection
│   ├── sessions/, events/, decisions/, findings/, code_index/, code_edges/,
│   │   tasks/, context_cache/, skills/, lessons_learned/, revisions/, adrs/, traces/, projects/
├── skills/                      # Skill Markdown files
├── sessions/                    # Session exports (optional)
├── logs/                        # Operation logs (optional)
└── _indices/                    # Index definitions + coverage tracking
    ├── definitions.json         # Index definitions
    ├── coverage.json            # Per-file index coverage status
    ├── ram_indexes.bin          # In-memory index snapshot
    ├── index.log                # Index WAL
    └── snapshots/               # Index snapshots
specs/                         # Feature specs (001-008)
docs/                          # T060 perf, T062 security
examples/
test_hakoagent.py              # Python stdlib unittest (56+ tests)
install.sh                     # Project installer
INSTALL.md                     # Installation guide
AGENTS.md                      # Agent-facing instructions
```

**Structure Decision**: Single project structure (DEFAULT) — one Python CLI script `hakoagent` at project root, extended with knowledge graph functions. All runtime data under `.hakoagent/` or project root. No MCP, no Rust, no Cargo, no separate crate.

---

## Phase 0: Outline & Research

### Unknowns from Technical Context

| Unknown | Status | Resolusi |
|---------|--------|----------|
| Typed edge storage in hakodb | Open | Store edges as JSON in `code_edges` collection or embedded in `code_index.edges` |
| Cypher-like query parser complexity | Open | Implement MATCH/WHERE/RETURN/LIMIT subset in pure Python |
| Git diff parsing for detect_changes | Open | Use `subprocess` to run `git diff --name-only`, map to code_index entries |
| Risk label detection rules | Open | Define rules: high fan-out (>10 deps), circular deps, deep call chains (>5) |
| Row ceiling enforcement | Open | 100k row limit on query_graph results |

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
- **Auditor (Tier 3)**: Bounded-scope full verification, current graph generation, complete pagination, both call directions, explicit unresolved limitations.

Edge types: CALLS, HTTP_CALLS, ASYNC_CALLS, SPAWNS, DATA_FLOWS, IMPORTS, DEFINES, DEFINES_METHOD, OVERRIDE, USAGE, CALL_REFERENCE, CONFIGURES, REFERENCES_FILE, MENTIONS, FILE_CHANGES_WITH, SIMILAR_TO, SEMANTICALLY_RELATED, CONTAINS_FILE, CONTAINS_FOLDER, INFRA_MAPS, DEPENDS_ON, DEPLOYS, CONNECTS_TO

**Gap vs current hakoagent (US4)**:

| MCP capability | Current hakoagent (US4) | Gap to fill (US8) |
|----------------|------------------------|-------------------|
| `index_repository` / `index_status` | `hakoagent index` (basic) | Add edge type extraction during indexing |
| `search_graph(name_pattern=..., label=...)` | `hakoagent recall` (TF-IDF only) | Add `hakoagent graph search` with label+name_pattern+degree |
| `trace_path(direction=..., depth=..., risk_labels=...)` | `hakoagent graph trace` (basic BFS) | Add risk labels, both directions, depth tracking |
| `query_graph` (Cypher) | `hakoagent graph shortest-path` (Dijkstra only) | Add Cypher-like query parser (MATCH/WHERE/RETURN/LIMIT) |
| `detect_changes()` | `hakoagent vigilance` (basic) | Add `hakoagent graph detect-changes` (git diff → symbols) |
| `get_code_snippet(qualified_name=...)` | `hakoagent recall` returns file+symbol+line | Add `hakoagent graph get-snippet` |
| `get_architecture` | `hakoagent graph` + impact (basic) | Add `hakoagent graph architecture` (modules, deps, entry points) |
| `check_index_coverage` | `.hakoagent/_indices/coverage.json` | Already covered in US6, extend with evidence tiers |
| `manage_adr` | Not present | Add `hakoagent graph adr` |
| `ingest_traces` | Not present | Add `hakoagent graph ingest-traces` |
| `list_projects` / `delete_project` | Not present | Add project lifecycle commands |
| Scout/Verify/Auditor tiers | `--tier` accepted on graph commands | Extend with pagination and tier-specific depth |

Output: `research.md` documenting MCP skill pattern gap analysis and non-MCP adaptation plan.

---

## Phase 1: Design & Contracts

### Data Model (`data-model.md`)

Entities from the feature spec:

| Entity | Key Attributes | Relationships |
|--------|---------------|---------------|
| **CodeNode** | `entry_id`, `file_path`, `symbol_name`, `symbol_type`, `label`, `qualified_name`, `line_number`, `file_hash`, `actor` | has outgoing/incoming edges → CodeEdge |
| **CodeEdge** | `edge_id`, `source_id`, `target_id`, `edge_type`, `confidence`, `line_number`, `actor` | source → CodeNode, target → CodeNode |
| **ArchitectureDecision** | `adr_id`, `title`, `status`, `rationale`, `consequences`, `created_at`, `actor` | — |
| **TraceEntry** | `trace_id`, `timestamp`, `span_id`, `parent_span_id`, `operation`, `service`, `duration_ms`, `actor` | — |
| **Project** | `project_name`, `root_path`, `indexed_at`, `node_count`, `edge_count`, `actor` | — |

Edge types (16+): CALLS, HTTP_CALLS, ASYNC_CALLS, SPAWNS, DATA_FLOWS, IMPORTS, DEFINES, DEFINES_METHOD, OVERRIDE, USAGE, CALL_REFERENCE, CONFIGURES, REFERENCES_FILE, MENTIONS, FILE_CHANGES_WITH, SIMILAR_TO, SEMANTICALLY_RELATED, CONTAINS_FILE, CONTAINS_FOLDER, INFRA_MAPS, DEPENDS_ON, DEPLOYS, CONNECTS_TO

Collections added: `code_edges`, `adrs`, `traces`, `projects`

State transitions:
- CodeNode: created → indexed → stale (re-index needed)
- CodeEdge: created → validated → deprecated (symbol removed)
- ADR: proposed → accepted → rejected → superseded
- Project: created → indexed → deleted

### Interface Contracts (`contracts/`)

**File**: `contracts/codebase-knowledge-graph-interface.md`

| Tool | Parameter | Return |
|------|-----------|--------|
| `hakoagent.graph.search` | label, name_pattern, min_degree, max_degree, limit, offset | nodes[], total, has_more |
| `hakoagent.graph.trace` | symbol, direction, depth, risk_labels, tier | visited_nodes[], edges[], risk_flags[] |
| `hakoagent.graph.query` | cypher_like_query, limit | rows[], row_count, truncated |
| `hakoagent.graph.detect-changes` | git_diff_path, tier | affected_symbols[], affected_files[] |
| `hakoagent.graph.get-snippet` | qualified_name, context_lines | file_path, symbol_name, snippet, line_range |
| `hakoagent.graph.architecture` | tier | modules[], dependencies[], entry_points[] |
| `hakoagent.graph.adr` | add/list/get, title, status, rationale | adr_id, status |
| `hakoagent.graph.ingest-traces` | trace_file | trace_count, edge_count |
| `hakoagent.graph.list-projects` | — | projects[] (name, root_path, indexed_at, node_count, edge_count) |
| `hakoagent.graph.delete-project` | project_name | deleted, nodes_removed, edges_removed |
| `hakoagent.graph.coverage` | file_paths[], tier | coverage_status_per_file, gaps[], source_fallback_needed |

Return value always in JSON format for harness agent parsing.

### Quickstart Validation Guide (`quickstart.md`)

**Prerequisites**:
- Python 3 (stdlib only, no external dependencies)
- Prebuilt hakodb library at `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` + header `lib/hakodb.h`
- Write permission in working directory
- Git available (for `detect-changes`)

**Setup commands**:
```bash
# Initialize database
./hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

**Test/run commands**:
```bash
# Index codebase with typed edges
./hakoagent index

# Graph search by label and name pattern (like MCP search_graph)
./hakoagent graph search --label Function --name-pattern ".*Handler.*" --limit 10

# Trace call chain (like MCP trace_path)
./hakoagent graph trace --symbol func_a --direction both --depth 3 --risk-labels

# Shortest path (Dijkstra, like MCP query_graph basic)
./hakoagent graph shortest-path func_a func_c

# Cypher-like query
./hakoagent graph query "MATCH (f:Function)-[:CALLS]->(h:HTTP) RETURN f.name, h.url_path LIMIT 10"

# Detect changes from git diff
./hakoagent graph detect-changes --tier Auditor

# Get code snippet by qualified name
./hakoagent graph get-snippet --qualified-name src.main.func_a

# Architecture overview
./hakoagent graph architecture --tier Verify

# ADR management
./hakoagent graph adr add "Use embedded hakodb" accepted "No MCP server needed" agent-a
./hakoagent graph adr list

# Ingest execution traces
./hakoagent graph ingest-traces ./traces/execution.json

# Project lifecycle
./hakoagent graph list-projects
./hakoagent graph delete-project old-project

# Impact analysis (existing US4)
./hakoagent impact src/main.py

# Index coverage (existing US6)
./hakoagent graph coverage src/main.py --tier Auditor

# Full test suite
python3 test_hakoagent.py
```

**Expected outcomes**:
- `./hakoagent graph search`: Returns nodes matching label + name pattern, with edge types
- `./hakoagent graph trace`: Returns all reachable nodes via typed edges, with risk flags if `--risk-labels`
- `./hakoagent graph query`: Returns Cypher-like query results with row ceiling enforcement
- `./hakoagent graph detect-changes`: Maps git diff to affected symbols/files
- `./hakoagent graph get-snippet`: Returns source code snippet by qualified name
- `./hakoagent graph architecture`: Returns module dependency overview
- `./hakoagent graph adr`: CRUD for Architecture Decision Records
- `./hakoagent graph ingest-traces`: Adds trace nodes/edges to graph
- `./hakoagent graph list-projects`/`delete-project`: Project lifecycle management
- `python3 test_hakoagent.py`: 56+ tests passing (including new US8 tests)

### Re-evaluate Constitution Check (post-design)

| Prinsip Konstitusi | Status Post-Design | Catatan |
|-------------------|-------------------|---------|
| Smart Memory | Terpenuhi | CodeNode + CodeEdge via FFI |
| Anti-Lupa | Terpenuhi | Graph search before structural changes |
| Kronologi & Histori | Terpenuhi | ADR + trace history immutable |
| Consistency | Terpenuhi | JSON return format, standard tool names |
| Cross-Model Consistency | Terpenuhi | Same flow for all LLM models |
| Vigilance | Terpenuhi | detect_changes + coverage |
| Clear Target | Terpenuhi | Graph queries with clear targets |
| Codebase Fluency | Terpenuhi | Rich edge types + Cypher + architecture |
| Context Frugality | Terpenuhi | Graph queries reduce exploration LLM calls |
| Self Skill Improvement | Terpenuhi | ADR + trace ingestion |
| Python Only | Terpenuhi | stdlib only, no MCP/Rust/Cargo |
| Real Hakodb FFI | Terpenuhi | ctypes to libhakodb .so |
| Code Quality | Terpenuhi | No bare except, no hardcoded secrets |
| Testing | Terpenuhi | Unit tests for all new graph functions |
| Maintainability | Terpenuhi | Docs current, no stale references |

No violations. Constitution check PASSED post-design.

---

## Phase 2: Implementation Tasks (see `tasks.md`)

Plan workflow complete. Ready to proceed to `/speckit-tasks`.
