# Cache & Graph Interface Contract — HakoAgent

**Feature**: 003-cache-graph-system  
**Date**: 2026-10-29  
**Status**: Draft

## Overview

HakoAgent exposes a tool calling interface for caching and graph traversal. Each tool has a name prefixed with `hakoagent.`, clearly defined parameters, and a return value in JSON format for easy parsing by the agent.

## Tool List

| Tool | Description | Main Parameters | Return |
|------|-----------|-----------------|--------|
| `hakoagent.cache.get` | Retrieve context from cache (HNSW + FTS) | `query` (string), `limit` (integer) | `context_results` (array), `cache_hit` (boolean) |
| `hakoagent.cache.put` | Store context in the cache | `query` (string), `summary` (string), `ttl_seconds` (integer) | `cache_key` (string), `status` (string) |
| `hakoagent.cache.stats` | View cache statistics | — | `total_hits` (integer), `total_misses` (integer), `eviction_count` (integer), `cache_size` (integer) |
| `hakoagent.graph.traverse` | Graph traversal (BFS/DFS) | `start_node` (string), `direction` (string), `max_depth` (integer) | `visited_nodes` (array), `edges_traversed` (array) |
| `hakoagent.graph.shortest-path` | Shortest path (Dijkstra) | `from_node` (string), `to_node` (string) | `path_nodes` (array), `total_cost` (float) |
| `hakoagent.graph.dependents` | Nodes that depend on a given node | `node_id` (string) | `dependent_nodes` (array) |
| `hakoagent.graph.dependents-reverse` | Nodes that a given node depends on | `node_id` (string) | `dependent_reverse_nodes` (array) |
| `hakoagent.events` | View chronological history including caching and traversal events | `limit` (integer), `session_id` (string) | `events_list` (array) |

## Response Format

All responses are in JSON format:

```json
{
  "status": "success|error",
  "data": { ... },
  "error": null | { "code": "...", "message": "..." }
}
```

Example success response for `hakoagent.cache.get`:
```json
{
  "status": "success",
  "data": {
    "query": "error handling Rust",
    "cache_hit": true,
    "context_results": [
      {
        "file_path": "src/error_handling.rs",
        "symbol_name": "handle_error",
        "symbol_type": "function",
        "relevance_score": 0.95
      }
    ],
    "summary": "Use Result<T, E> with the ? operator for error propagation"
  },
  "error": null
}
```

Example success response for `hakoagent.graph.traverse`:
```json
{
  "status": "success",
  "data": {
    "start_node": "validate_input",
    "direction": "in",
    "max_depth": 2,
    "visited_nodes": [
      "process_request",
      "handle_http",
      "validate_batch"
    ],
    "edges_traversed": [
      "process_request -> validate_input",
      "handle_http -> process_request",
      "validate_batch -> validate_input"
    ]
  },
  "error": null
}
```

## Integration Notes

- The default cache TTL is 300 seconds (5 minutes). After the TTL elapses, the entry is considered expired.
- The cache uses LRU eviction when full.
- Graph traversal uses a visited set to avoid unbounded cycles.
- Every caching and traversal operation is recorded in the `events` collection (append-only).
- An error on one node does not stop traversal of other nodes.

## Integration Example (Pseudocode)

```python
from hakoagent import HakoAgentMemory

agent = HakoAgentMemory(db_path="./.hakoagent/hakoagent.db")

# 1. Try to retrieve context from the cache
context = agent.cache.get(query="bagaimana implementasi error handling Rust?", limit=5)

if context.cache_hit:
    print("Cache hit! Using the cached results.")
else:
    print("Cache miss. Memanggil endpoint LLM...")
    # Call the LLM endpoint and store the result in the cache
    agent.cache.put(
        query="bagaimana implementasi error handling Rust?",
        summary="Use Result<T, E> with the ? operator...",
        ttl_seconds=300
    )

# 2. Traverse the codebase graph
result = agent.graph.traverse(
    start_node="validate_input",
    direction="in",
    max_depth=2
)
print(f"Visited nodes: {result.visited_nodes}")

# 3. Find the shortest path
path = agent.graph.shortest_path(
    from_node="main",
    to_node="error_handler"
)
print(f"Jalur terpendek: {path.path_nodes}")

# 4. View cache statistics
stats = agent.cache.stats()
print(f"Cache hit ratio: {stats.total_hits / (stats.total_hits + stats.total_misses):.2%}")
```
