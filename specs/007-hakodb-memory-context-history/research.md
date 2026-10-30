# Research Findings — HakoAgent Memory, Context & History System (Non-MCP, Embedded Hakodb)

**Feature**: 007-hakodb-memory-context-history  
**Date**: 2026-10-29  
**Status**: Complete

## Source: `/home/web/.claude/skills/codebase-memory/` (MCP codebase-memory skill)

Explored with sudo access. Key files:

| Path | Description |
|------|-------------|
| `/home/web/.claude/skills/codebase-memory/SKILL.md` | Skill definition — Codebase Memory knowledge graph tools |
| `/home/web/.claude/agents/codebase-memory.md` | Tier 2 Verify agent (default) |
| `/home/web/.claude/agents/codebase-memory-auditor.md` | Tier 3 Auditor agent |
| `/home/web/.claude/agents/codebase-memory-scout.md` | Tier 1 Scout agent |

## MCP Skill: 15 Tools

| Category | Tools |
|----------|-------|
| Index management | `index_repository`, `index_status`, `list_projects`, `delete_project` |
| Graph queries | `search_graph`, `search_code`, `trace_path`, `detect_changes`, `query_graph` |
| Schema/architecture | `get_graph_schema`, `get_code_snippet`, `get_architecture` |
| Coverage | `check_index_coverage` |
| Other | `manage_adr`, `ingest_traces` |

## MCP Skill: Evidence Tiers

| Tier | Name | Depth | Use case |
|------|------|-------|----------|
| Tier 1 | Scout | Fast positive lookup, few calls, provisional | Exploration, discovery |
| Tier 2 | Verify | Task-directed, relevant traces, exact snippets | Default verification |
| Tier 3 | Auditor | Bounded-scope full verification, both directions, explicit limitations | Audit, compliance |

## MCP Skill: Edge Types

CALLS, HTTP_CALLS, ASYNC_CALLS, SPAWNS, DATA_FLOWS, IMPORTS, DEFINES, DEFINES_METHOD, OVERRIDE, USAGE, CALL_REFERENCE, CONFIGURES, REFERENCES_FILE, MENTIONS, FILE_CHANGES_WITH, SIMILAR_TO, SEMANTICALLY_RELATED, CONTAINS_FILE, CONTAINS_FOLDER, INFRA_MAPS, DEPENDS_ON, DEPLOYS, CONNECTS_TO

## Adaptation to Embedded Hakodb (Non-MCP)

| MCP capability | HakoAgent adaptation (Python + hakodb FFI) |
|----------------|--------------------------------------------|
| `index_repository` / `index_status` | `hakoagent index` → builds `code_index` + `coverage.json` |
| `search_graph(name_pattern=...)` | `hakoagent recall <query>` + TF-IDF over `code_index` |
| `trace_path(direction=inbound\|outbound\|both)` | `hakoagent graph trace <node> <dir> <depth>` — BFS over `code_index.dependensi` |
| `query_graph` (Cypher) | `hakoagent graph shortest-path <from> <to>` — Dijkstra over dependencies |
| `detect_changes()` | `hakoagent vigilance` + revision tracking in `revisions` collection |
| `get_code_snippet(qualified_name=...)` | `hakoagent recall` returns file_path + symbol_name + line_number |
| `get_architecture` | `hakoagent graph impact <file>` — blast radius via transitive dependents |
| `check_index_coverage(file_paths)` | `.hakoagent/_indices/coverage.json` + source read/grep fallback |
| Scout/Verify/Auditor tiers | Evidence depth parameter on graph commands (`--tier scout\|verify\|auditor`) |

## FFI Symbol Verification

The prebuilt `libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` (v0.20.0) exports verified via `nm -D`:

| Function | Status |
|----------|--------|
| `hk_engine_open` | ✅ Exported |
| `hk_engine_free` | ✅ Exported |
| `hk_engine_insert_json` | ✅ Exported |
| `hk_engine_get_json` | ✅ Exported |
| `hk_engine_delete` | ✅ Exported |
| `hk_string_free` | ✅ Exported |

Python FFI wrapper verified working against real `.so`: Insert → Get (returns JSON with `_time`) → Delete → Free, all successful.

## MCP Check

The hakobackend binary strings contain "MCPN" but these are mangled Rust symbol names, **NOT Model Context Protocol**. hakobackend is a custom HTTP/WebSocket server, not MCP. HakoAgent is explicitly **non-MCP** — all context sharing via embedded hakodb FFI + filesystem-level sharing of `.hakoagent/hakoagent.db`.

## Best Practices for HakoAgent

1. Every document stored includes an `actor` field for multi-agent attribution
2. Event log is append-only — `event_id` uniqueness checked before write
3. Immutable revisions — previous document versions preserved on update
4. Soft-delete — mark with `deleted_at`, exclude from recall, recoverable
5. Timestamps are ISO 8601
6. All runtime data under `.hakoagent/` or project root
7. No MCP, no Rust, Cargo, or build step (Python stdlib only)
8. Graceful fallback to JSON when hakodb library unavailable
9. Context efficiency: cache hit avoids LLM endpoint call; `llm_calls_saved` tracked per cache entry
10. Graph trace over `code_index` dependency edges (inbound/outbound/both, with depth limit)
11. Evidence tiers: Scout (provisional), Verify (task-directed), Auditor (bounded-scope full)
