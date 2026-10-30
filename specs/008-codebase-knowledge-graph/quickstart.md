# Quickstart — Codebase Knowledge Graph (US8)

**Feature**: 008-codebase-knowledge-graph  
**Date**: 2026-10-29  
**Status**: Draft

## Prerequisites

- Python 3 (stdlib only, no external dependencies)
- Prebuilt hakodb library at `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` + header `lib/hakodb.h`
- Write permission in working directory
- Git available (for `detect-changes`)

## Setup

```bash
# Initialize database with all collections (includes code_edges, adrs, traces, projects)
./hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

## Validation Scenarios

### 1. Index codebase with typed edges

```bash
./hakoagent index
```
**Expected**: Indexed N file(s) into code_index collection. M edge(s) into code_edges collection.

### 2. Graph search by label and name pattern (like MCP search_graph)

```bash
./hakoagent graph search --label Function --name-pattern ".*Handler.*" --limit 10
```
**Expected**: Returns nodes matching label "Function" and name matching ".*Handler.*", with edge types and degree.

### 3. Trace call chain (like MCP trace_path)

```bash
# Outbound: what does func_a call?
./hakoagent graph trace --symbol func_a --direction outbound --depth 3

# Inbound: who calls func_a?
./hakoagent graph trace --symbol func_a --direction inbound --depth 2

# Both directions with risk labels
./hakoagent graph trace --symbol func_a --direction both --depth 3 --risk-labels
```
**Expected**: Returns all reachable nodes via typed edges, with risk flags if `--risk-labels` (e.g., "high_fan_out").

### 4. Shortest path (Dijkstra)

```bash
./hakoagent graph shortest-path func_a func_c
```
**Expected**: Returns shortest dependency chain between two symbols.

### 5. Cypher-like query

```bash
./hakoagent graph query "MATCH (f:Function)-[:CALLS]->(h:HTTP) RETURN f.name, h.url_path LIMIT 10"
```
**Expected**: Returns query results with row count, truncated flag, and ceiling warning if applicable.

### 6. Detect changes from git diff

```bash
./hakoagent graph detect-changes --tier Auditor
```
**Expected**: Maps git diff to affected symbols and files.

### 7. Get code snippet by qualified name

```bash
./hakoagent graph get-snippet --qualified-name src.main.func_a --context-lines 5
```
**Expected**: Returns source code snippet with line range.

### 8. Architecture overview

```bash
./hakoagent graph architecture --tier Verify
```
**Expected**: Returns modules, dependencies, entry points, circular dependencies.

### 9. ADR management

```bash
# Create ADR
./hakoagent graph adr add --title "Use embedded hakodb" --status accepted --rationale "No MCP server needed" --consequences "Simpler deployment" --actor agent-a

# List ADRs
./hakoagent graph adr list

# Get specific ADR
./hakoagent graph adr get adr_001
```

### 10. Ingest execution traces

```bash
./hakoagent graph ingest-traces ./traces/execution.json --actor agent-a
```
**Expected**: Returns trace count and edge count added to graph.

### 11. Project lifecycle

```bash
# List projects
./hakoagent graph list-projects

# Delete project
./hakoagent graph delete-project old-project
```

### 12. Index coverage with evidence tier

```bash
./hakoagent graph coverage src/main.py src/utils.py --tier Auditor
```
**Expected**: Returns per-file coverage status with gaps and source fallback info.

### 13. Full test suite

```bash
python3 test_hakoagent.py
```
**Expected**: 56+ tests passing (including new US8 knowledge graph tests).

---
