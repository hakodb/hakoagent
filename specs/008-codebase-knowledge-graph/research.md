# Research — Codebase Knowledge Graph Gap Analysis (US8)

**Feature**: 008-codebase-knowledge-graph  
**Date**: 2026-10-29  
**Status**: Draft

## MCP codebase-memory skill analysis

**Source**: `/home/web/.claude/skills/codebase-memory/SKILL.md` (79 lines)

### 15 MCP Tools

| # | Tool | Purpose | Current hakoagent equivalent | Gap |
|---|------|---------|------------------------------|-----|
| 1 | `index_repository` | Index a project into the graph | `hakoagent index` (basic, single edge type) | Need typed edge extraction during indexing |
| 2 | `index_status` | Check indexing progress | Not present | Need project status tracking |
| 3 | `list_projects` | List indexed projects | Not present | Need `projects` collection + list command |
| 4 | `delete_project` | Remove a project from graph | Not present | Need delete command |
| 5 | `search_graph` | Find nodes by label/name/degree | `hakoagent recall` (TF-IDF only, no label/degree) | Need `graph search` with label+name_pattern+degree |
| 6 | `search_code` | Text/code search | `hakoagent recall` (partial) | Need dedicated code search |
| 7 | `trace_path` | Trace call chains (inbound/outbound/both) | `hakoagent graph trace` (outbound only, basic BFS) | Need both directions, depth tracking, risk labels |
| 8 | `detect_changes` | Map git diff to affected symbols | `hakoagent vigilance` (basic) | Need `graph detect-changes` with git diff parsing |
| 9 | `query_graph` | Cypher queries (100k row ceiling) | `hakoagent graph shortest-path` (Dijkstra only) | Need Cypher-like parser (MATCH/WHERE/RETURN/LIMIT) |
| 10 | `get_graph_schema` | Understand node/edge types | Not present | Need schema introspection |
| 11 | `get_code_snippet` | Read source by qualified name | `hakoagent recall` (returns file+symbol+line only) | Need `graph get-snippet` |
| 12 | `get_architecture` | Architecture overview | `hakoagent graph` + impact (basic) | Need `graph architecture` (modules, deps, entry points) |
| 13 | `check_index_coverage` | Check graph coverage gaps | `.hakoagent/_indices/coverage.json` (basic) | Need `--tier` flag + edge_type coverage |
| 14 | `manage_adr` | Architecture decision records | Not present | Need `graph adr` commands |
| 15 | `ingest_traces` | Ingest execution traces | Not present | Need `graph ingest-traces` |

### Evidence Tiers

| Tier | MCP Behavior | Current hakoagent | Gap |
|------|-------------|-------------------|-----|
| Scout (Tier 1) | Fast positive lookup, few graph calls, targeted source checks, provisional results | `--tier` accepted but not differentiated | Need tier-specific depth logic |
| Verify (Tier 2, default) | Task-directed searches, relevant trace directions, exact snippets | `--tier` accepted but not differentiated | Need tier-specific depth logic |
| Auditor (Tier 3) | Bounded-scope full verification, current graph generation, complete pagination, both call directions, explicit limitations | `--tier` accepted but not differentiated | Need tier-specific depth logic |

### Edge Types (MCP)

CALLS, HTTP_CALLS, ASYNC_CALLS, SPAWNS, DATA_FLOWS, IMPORTS, DEFINES, DEFINES_METHOD, OVERRIDE, USAGE, CALL_REFERENCE, CONFIGURES, REFERENCES_FILE, MENTIONS, FILE_CHANGES_WITH, SIMILAR_TO, SEMANTICALLY_RELATED, CONTAINS_FILE, CONTAINS_FOLDER, INFRA_MAPS, DEPENDS_ON, DEPLOYS, CONNECTS_TO

**Current hakoagent**: Only `dependinsi` (single dependency list, no types). **Gap**: Need 16+ typed edges.

### Gotchas (MCP)

1. `search_graph(relationship=...)` filters nodes by degree — use `query_graph` with Cypher to see actual edges
2. `query_graph` has 100k row ceiling — add Cypher `LIMIT` for broad queries
3. `trace_path` needs exact names — use `search_graph(name_pattern=...)` first
4. `direction="outbound"` misses cross-service callers — use `direction="both"`
5. `search_graph` results default to 50 per page — check `has_more` and use `offset`

## Adaptation to Embedded Hakodb (Non-MCP)

| MCP capability | HakoAgent adaptation (Python + hakodb FFI) |
|----------------|--------------------------------------------|
| `index_repository` / `index_status` | `hakoagent index` → builds `code_index` + `code_edges` + `coverage.json` |
| `list_projects` / `delete_project` | `hakoagent graph list-projects` / `delete-project` → `projects` collection |
| `search_graph(label=, name_pattern=, min_degree=, max_degree=)` | `hakoagent graph search` → TF-IDF + degree filter over `code_index` + `code_edges` |
| `search_code` | `hakoagent recall` + TF-IDF over code collections |
| `trace_path(direction=, depth=, risk_labels=)` | `hakoagent graph trace` → BFS over `code_edges` with typed edges, risk label detection |
| `detect_changes()` | `hakoagent graph detect-changes` → `git diff --name-only` → map to `code_index` entries |
| `query_graph` (Cypher) | `hakoagent graph query` → pure Python MATCH/WHERE/RETURN/LIMIT parser, 100k row ceiling |
| `get_graph_schema` | `hakoagent graph schema` → introspect `code_index` + `code_edges` collections |
| `get_code_snippet(qualified_name=)` | `hakoagent graph get-snippet` → read source file by qualified name |
| `get_architecture` | `hakoagent graph architecture` → modules, dependencies, entry points, circular deps |
| `check_index_coverage` | `.hakoagent/_indices/coverage.json` + `--tier` + `source_fallback` |
| `manage_adr` | `hakoagent graph adr` → `adrs` collection (add/list/get) |
| `ingest_traces` | `hakoagent graph ingest-traces` → `traces` collection + `code_edges` |
| Scout/Verify/Auditor tiers | `--tier` flag with tier-specific depth logic on all graph commands |

No MCP server or plugin — all via embedded hakodb FFI + Python stdlib, filesystem-level multi-agent sharing.

## Output

`research.md` documents the complete MCP skill pattern gap analysis and non-MCP adaptation plan.
