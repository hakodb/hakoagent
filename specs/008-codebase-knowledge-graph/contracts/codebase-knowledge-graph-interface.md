# Interface Contract — Codebase Knowledge Graph (US8)

**Feature**: 008-codebase-knowledge-graph  
**Date**: 2026-10-29  
**Status**: Draft

All tool returns are in JSON format for harness agent parsing.

---

## 1. `hakoagent graph search`

Find graph nodes by label and/or name pattern, with optional degree filtering and pagination.

**Usage**: `hakoagent graph search --label <label> --name-pattern <regex> [--min-degree N] [--max-degree N] [--limit N] [--offset N] [--tier scout|verify|auditor]`

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--label` | string | No | Node label filter (e.g., "Function", "File", "Folder") |
| `--name-pattern` | string | No | Regex pattern to match `symbol_name` or `file_path` |
| `--min-degree` | int | No | Minimum total edge degree |
| `--max-degree` | int | No | Maximum total edge degree |
| `--limit` | int | No | Max results (default: 50) |
| `--offset` | int | No | Pagination offset (default: 0) |
| `--tier` | string | No | Evidence tier: scout/verify/auditor (default: verify) |

**Returns**:
```json
{
  "nodes": [
    {
      "entry_id": "code_001",
      "file_path": "src/handler.py",
      "symbol_name": "AuthHandler",
      "symbol_type": "class",
      "label": "Function",
      "qualified_name": "src.handler.AuthHandler",
      "line_number": 42,
      "edge_types": ["CALLS", "IMPORTS", "DEFINES_METHOD"],
      "degree": 12,
      "actor": "agent-a"
    }
  ],
  "total": 1,
  "has_more": false,
  "tier": "verify"
}
```

---

## 2. `hakoagent graph trace`

Trace call chains from a symbol in a given direction with depth limit and optional risk labels.

**Usage**: `hakoagent graph trace --symbol <name> --direction <inbound\|outbound\|both> --depth <N> [--risk-labels] [--tier scout|verify|auditor]`

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--symbol` | string | Yes | Symbol name to start tracing from |
| `--direction` | string | Yes | `inbound`, `outbound`, or `both` |
| `--depth` | int | Yes | Max traversal depth |
| `--risk-labels` | flag | No | Annotate edges with risk labels |
| `--tier` | string | No | Evidence tier (default: verify) |

**Returns**:
```json
{
  "symbol": "func_a",
  "direction": "both",
  "depth": 3,
  "visited_nodes": [
    {
      "entry_id": "code_001",
      "symbol_name": "func_a",
      "file_path": "src/main.py",
      "label": "Function"
    },
    {
      "entry_id": "code_002",
      "symbol_name": "func_b",
      "file_path": "src/utils.py",
      "label": "Function"
    }
  ],
  "edges": [
    {
      "edge_id": "edge_001",
      "source_id": "code_001",
      "target_id": "code_002",
      "edge_type": "CALLS",
      "risk_label": null
    }
  ],
  "risk_flags": ["high_fan_out: func_a has 15 outgoing calls"],
  "edges_traversed": 1,
  "tier": "verify"
}
```

---

## 3. `hakoagent graph query`

Run a Cypher-like declarative query over the knowledge graph.

**Usage**: `hakoagent graph query "<cypher-like>" [--limit N]`

**Supported syntax** (Python-based subset):
- `MATCH (n:Label)-[:EDGE_TYPE]->(m:Label2)`
- `WHERE n.property = 'value' OR n.property =~ 'regex'`
- `RETURN n.name, m.name`
- `LIMIT N`

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Cypher-like query string |
| `--limit` | int | No | Max rows (default: 100, ceiling: 100000) |

**Returns**:
```json
{
  "query": "MATCH (f:Function)-[:CALLS]->(h:HTTP) RETURN f.name, h.url_path LIMIT 10",
  "rows": [
    {"f.name": "fetch_data", "h.url_path": "https://api.example.com/data"}
  ],
  "row_count": 1,
  "truncated": false,
  "ceiling": 100000
}
```

---

## 4. `hakoagent graph detect-changes`

Map git diff to affected symbols in the knowledge graph.

**Usage**: `hakoagent graph detect-changes [--diff-path <path>] [--tier scout|verify|auditor]`

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--diff-path` | string | No | Path to git diff file (default: `git diff --name-only`) |
| `--tier` | string | No | Evidence tier (default: verify) |

**Returns**:
```json
{
  "changed_files": ["src/main.py", "src/utils.py"],
  "affected_symbols": [
    {
      "entry_id": "code_001",
      "symbol_name": "func_a",
      "file_path": "src/main.py",
      "change_type": "modified"
    }
  ],
  "affected_files": ["src/main.py", "src/utils.py"],
  "tier": "verify"
}
```

---

## 5. `hakoagent graph get-snippet`

Return source code snippet by qualified symbol name.

**Usage**: `hakoagent graph get-snippet --qualified-name <name> [--context-lines N]`

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--qualified-name` | string | Yes | Fully qualified symbol name (e.g., "src.main.func_a") |
| `--context-lines` | int | No | Lines of context before/after (default: 5) |

**Returns**:
```json
{
  "qualified_name": "src.main.func_a",
  "file_path": "src/main.py",
  "symbol_name": "func_a",
  "symbol_type": "function",
  "snippet": "def func_a(x, y):\n    return x + y",
  "line_range": [10, 12],
  "actor": "agent-a"
}
```

---

## 6. `hakoagent graph architecture`

Return architecture overview: modules, dependencies, entry points.

**Usage**: `hakoagent graph architecture [--tier scout|verify|auditor]`

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--tier` | string | No | Evidence tier (default: verify) |

**Returns**:
```json
{
  "modules": [
    {"name": "src.main", "type": "module", "file_path": "src/main.py", "symbol_count": 5}
  ],
  "dependencies": [
    {"from": "src.main", "to": "src.utils", "edge_type": "IMPORTS", "strength": 3}
  ],
  "entry_points": ["src.main.main"],
  "circular_dependencies": [],
  "tier": "verify"
}
```

---

## 7. `hakoagent graph adr`

Manage Architecture Decision Records.

**Usage**: `hakoagent graph adr <add\|list\|get> [--title <title>] [--status <status>] [--rationale <text>] [--consequences <text>] [--actor <actor>] [adr_id]`

**Subcommands**:

| Subcommand | Parameters | Description |
|------------|-----------|-------------|
| `add` | `--title`, `--status`, `--rationale`, `--consequences`, `--actor` | Create new ADR |
| `list` | — | List all ADRs |
| `get` | `adr_id` | Get specific ADR details |

**Returns (add)**:
```json
{
  "adr_id": "adr_001",
  "title": "Use embedded hakodb",
  "status": "accepted",
  "created_at": "2026-10-29T08:00:00Z",
  "actor": "agent-a"
}
```

**Returns (list)**:
```json
{
  "adrs": [
    {
      "adr_id": "adr_001",
      "title": "Use embedded hakodb",
      "status": "accepted",
      "created_at": "2026-10-29T08:00:00Z",
      "actor": "agent-a"
    }
  ],
  "total": 1
}
```

---

## 8. `hakoagent graph ingest-traces`

Ingest execution trace entries into the knowledge graph.

**Usage**: `hakoagent graph ingest-traces <trace-file> [--actor <actor>]`

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| trace-file | string | Yes | Path to trace JSON file |
| `--actor` | string | No | Actor attribution |

**Returns**:
```json
{
  "trace_file": "./traces/execution.json",
  "trace_count": 42,
  "edge_count": 15,
  "actor": "agent-a"
}
```

---

## 9. `hakoagent graph list-projects`

List all indexed projects.

**Usage**: `hakoagent graph list-projects`

**Returns**:
```json
{
  "projects": [
    {
      "project_name": "bimbingan",
      "root_path": "/home/web/bimbingan",
      "indexed_at": "2026-10-29T08:00:00Z",
      "node_count": 1500,
      "edge_count": 3200,
      "actor": "agent-a"
    }
  ],
  "total": 1
}
```

---

## 10. `hakoagent graph delete-project`

Delete a project and all its graph data.

**Usage**: `hakoagent graph delete-project <project_name>`

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| project_name | string | Yes | Name of project to delete |

**Returns**:
```json
{
  "project_name": "old-project",
  "deleted": true,
  "nodes_removed": 1500,
  "edges_removed": 3200
}
```

---

## 11. `hakoagent graph coverage`

Check index coverage per file with evidence tier depth.

**Usage**: `hakoagent graph coverage <file_path> [file_path ...] [--tier scout|verify|auditor]`

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_path | string+ | Yes | One or more file paths to check |
| `--tier` | string | No | Evidence tier (default: verify) |

**Returns**:
```json
{
  "files": [
    {
      "file_path": "src/main.py",
      "indexed": true,
      "last_indexed_at": "2026-10-29T08:00:00Z",
      "coverage_gaps": [],
      "source_fallback": false,
      "node_count": 5,
      "edge_count": 8,
      "edge_types": ["CALLS", "IMPORTS", "DEFINES"]
    }
  ],
  "tier": "verify"
}
```

---
