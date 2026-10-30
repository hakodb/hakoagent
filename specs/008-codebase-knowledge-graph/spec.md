# Feature Specification: Codebase Knowledge Graph (US8)

**Feature Branch**: `008-codebase-knowledge-graph`

**Created**: 2026-10-29

**Status**: Draft

**Input**: Gap analysis vs `/home/web/.claude/skills/codebase-memory/SKILL.md` — hakoagent currently has basic graph trace/shortest-path/impact over `code_index` dependencies but lacks the full MCP codebase-memory knowledge graph capabilities: rich edge types (16+), Cypher-like queries, `search_graph` with label/name_pattern/degree filtering, `get_code_snippet`, `get_architecture`, `detect_changes`, `manage_adr`, `ingest_traces`, `list_projects`/`delete_project`, risk-labeled traces, and full Scout/Verify/Auditor evidence tiers with pagination.

**Reference**: `/home/web/.claude/skills/codebase-memory/SKILL.md` — Codebase Memory knowledge graph MCP (15 tools). Adapted to **Python-only, non-MCP, embedded hakodb** — no MCP server, no external plugin.

---

## User Scenarios & Testing *(mandatory)*

### User Story 8 - Agent queries codebase knowledge graph with rich edge types (Priority: P1)

A harness agent explores codebase structure using a knowledge graph with 16+ edge types (CALLS, HTTP_CALLS, ASYNC_CALLS, SPAWNS, DATA_FLOWS, IMPORTS, DEFINES, DEFINES_METHOD, OVERRIDE, USAGE, CALL_REFERENCE, CONFIGURES, REFERENCES_FILE, MENTIONS, FILE_CHANGES_WITH, SIMILAR_TO, SEMANTICALLY_RELATED, CONTAINS_FILE, CONTAINS_FOLDER, INFRA_MAPS, DEPENDS_ON, DEPLOYS, CONNECTS_TO). Each `code_index` entry carries typed edges instead of a single `dependensi` list.

**Why this priority**: The MCP codebase-memory skill's core value is structural code queries with typed relationships — adapting it to embedded hakodb gives the same capability without an MCP server.

**Independent Test**: Index a codebase with typed edges, run `hakoagent graph search --label Function --name-pattern ".*Handler.*"`, verify matching symbols returned. Run `hakoagent graph trace --symbol func_a --direction both --depth 3 --risk-labels`, verify trace with risk labels.

**Acceptance Scenarios**:

1. **Given** codebase indexed with typed edges, **When** agent searches by label and name pattern, **Then** matching symbols/files returned with edge types
2. **Given** typed edges exist, **When** agent traces symbol with `--direction both --depth 3`, **Then** all reachable nodes via typed edges returned
3. **Given** risk labels enabled, **When** agent traces path, **Then** edges annotated with risk labels (e.g., "high fan-out", "circular dependency")

---

### User Story 9 - Agent runs Cypher-like queries over codebase graph (Priority: P1)

A harness agent runs declarative graph queries using a Python-based Cypher-like query language (simplified subset: MATCH, WHERE, RETURN, LIMIT) over the embedded hakodb knowledge graph — adapted from MCP `query_graph` (100k row ceiling, Cypher).

**Why this priority**: Declarative queries enable complex structural analysis that BFS/Dijkstra alone cannot express — e.g., "find all functions that call HTTP endpoints and are not tested."

**Independent Test**: Run `hakoagent graph query "MATCH (f:Function)-[:CALLS]->(h:HTTP) RETURN f.name, h.url_path LIMIT 10"`, verify results returned.

**Acceptance Scenarios**:

1. **Given** graph populated, **When** agent runs Cypher-like query, **Then** matching nodes/edges returned
2. **Given** query exceeds safety limit, **When** agent runs query, **Then** query rejected with row ceiling warning
3. **Given** query with LIMIT, **When** results exceed limit, **Then** only LIMIT rows returned

---

### User Story 10 - Agent detects changes and analyzes impact like MCP Auditor tier (Priority: P1)

A harness agent maps git diff to affected symbols using `detect_changes()` pattern, runs impact analysis with full Auditor-tier verification (both call directions, complete pagination, explicit limitations), and checks index coverage before relying on results.

**Why this priority**: The MCP skill's evidence-tier system ensures reliable structural queries — adapting it ensures the hakodb knowledge graph is trustworthy for impact analysis and change detection.

**Independent Test**: Make a code change, run `hakoagent graph detect-changes`, verify affected symbols identified. Run coverage check, verify gaps reported with source fallback.

**Acceptance Scenarios**:

1. **Given** git diff available, **When** agent runs change detection, **Then** affected symbols/files mapped from diff
2. **Given** impact analysis requested, **When** tier=Auditor, **Then** both call directions traced, full pagination, unresolved limitations listed
3. **Given** coverage gap found, **When** agent falls back to source grep, **Then** missing info retrieved from source files

---

### User Story 11 - Agent manages architecture records and ingests traces (Priority: P2)

A harness agent manages Architecture Decision Records (ADRs) via `manage_adr`, ingests execution traces via `ingest_traces`, and lists/deletes indexed projects via `list_projects`/`delete_project`.

**Why this priority**: Architecture decisions and execution traces provide long-term context for the knowledge graph — essential for team-wide architectural governance.

**Independent Test**: Create an ADR via `hakoagent graph adr add <title> <status>`, verify ADR stored. Ingest a trace via `hakoagent graph ingest-traces <trace-file>`, verify trace nodes/edges added to graph.

**Acceptance Scenarios**:

1. **Given** ADR title and status, **When** agent creates ADR, **Then** ADR stored with ID, timestamp, status
2. **Given** trace file, **When** agent ingests traces, **Then** trace nodes/edges added to knowledge graph
3. **Given** project indexed, **When** agent lists projects, **Then** project name and root_path returned
4. **Given** project to remove, **When** agent deletes project, **Then** project and all its graph data removed

---

## Edge Cases

- **Unknown symbol in trace**: Return informative message, suggest `search_graph` first
- **Circular dependencies**: Visited set prevents infinite loops (already in BFS/Dijkstra)
- **Empty graph**: Return "no graph data — run `hakoagent index` first"
- **Cypher syntax error**: Clear error message with example syntax
- **Row ceiling exceeded**: Query rejected, suggest adding LIMIT
- **Missing edge type**: Unknown edge type treated as generic DEPENDS_ON
- **Concurrent index updates**: File-level locking, retry on conflict

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-020**: System MUST support 16+ edge types in `code_index` (CALLS, HTTP_CALLS, ASYNC_CALLS, SPAWNS, DATA_FLOWS, IMPORTS, DEFINES, DEFINES_METHOD, OVERRIDE, USAGE, CALL_REFERENCE, CONFIGURES, REFERENCES_FILE, MENTIONS, FILE_CHANGES_WITH, SIMILAR_TO, SEMANTICALLY_RELATED, CONTAINS_FILE, CONTAINS_FOLDER, INFRA_MAPS, DEPENDS_ON, DEPLOYS, CONNECTS_TO)
- **FR-021**: System MUST support `hakoagent graph search --label <label> --name-pattern <regex> [--limit N]` — find nodes by label and name pattern
- **FR-022**: System MUST support `hakoagent graph trace --symbol <name> --direction <inbound\|outbound\|both> --depth <N> [--risk-labels]` — trace call chains with optional risk labels
- **FR-023**: System MUST support `hakoagent graph query <cypher-like>` — declarative graph queries (MATCH/WHERE/RETURN/LIMIT subset)
- **FR-024**: System MUST support `hakoagent graph detect-changes` — map git diff to affected symbols
- **FR-025**: System MUST support `hakoagent graph get-snippet --qualified-name <name>` — return code snippet by qualified symbol name
- **FR-026**: System MUST support `hakoagent graph architecture` — return architecture overview (modules, dependencies, entry points)
- **FR-027**: System MUST support `hakoagent graph adr <add\|list\|get>` — manage Architecture Decision Records
- **FR-028**: System MUST support `hakoagent graph ingest-traces <trace-file>` — ingest execution traces into graph
- **FR-029**: System MUST support `hakoagent graph list-projects` and `hakoagent graph delete-project <name>` — project lifecycle
- **FR-030**: System MUST support evidence tiers (Scout/Verify/Auditor) with `--tier` flag on graph commands
- **FR-031**: System MUST enforce row ceiling (100k) on graph queries with warning
- **FR-032**: System MUST support pagination (offset/limit) on search results

### Key Entities

| Entity | Key Attributes | Relationships |
|--------|---------------|---------------|
| **CodeNode** | `entry_id`, `file_path`, `symbol_name`, `symbol_type`, `label`, `qualified_name`, `line_number`, `file_hash`, `actor` | has edges → CodeEdge |
| **CodeEdge** | `edge_id`, `source_id`, `target_id`, `edge_type` (16+ types), `confidence`, `line_number`, `actor` | source → CodeNode, target → CodeNode |
| **ArchitectureDecision** | `adr_id`, `title`, `status`, `rationale`, `consequences`, `created_at`, `actor` | — |
| **TraceEntry** | `trace_id`, `timestamp`, `span_id`, `parent_span_id`, `operation`, `service`, `duration_ms`, `actor` | — |
| **Project** | `project_name`, `root_path`, `indexed_at`, `node_count`, `edge_count`, `actor` | — |

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-014**: Graph search by label+name pattern returns correct nodes < 1s
- **SC-015**: Trace path with `--direction both --depth 3` returns all reachable nodes
- **SC-016**: Cypher-like query returns correct results with row ceiling enforcement
- **SC-017**: `detect_changes` maps git diff to affected symbols
- **SC-018**: `get_code_snippet` returns source snippet by qualified name
- **SC-019**: `get_architecture` returns module dependency overview
- **SC-020**: Evidence tiers (Scout/Verify/Auditor) produce different verification depths
- **SC-021**: Row ceiling (100k) enforced on graph queries
- **SC-022**: 0 references to MCP / Rust / Cargo / build in new code
- **SC-023**: All existing 56 tests continue to pass
- **SC-024**: New tests for knowledge graph functions pass

---

## Assumptions

- Prebuilt hakodb shared library supports typed edge storage (or edges stored as JSON in `code_index` metadata)
- Python 3 stdlib only — Cypher-like query parser implemented in pure Python
- Git available for `detect_changes` (graceful degradation if not)
- Edge types stored as JSON arrays in `code_index.edges` field or separate `code_edges` collection
- Multiple agents share same `.hakoagent/` directory (filesystem-level, no MCP server)

---
