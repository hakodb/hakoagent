# Data Model — System Caching and Graph Traversal

**Feature**: 003-cache-graph-system  
**Date**: 2026-10-29  
**Status**: Draft

## Entities

### CacheEntry

A cache entry stored in the `context_cache` collection of HakoDB.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| cache_key | string | Unique cache key (hash of the query) | Must be unique |
| query | string | The original query being searched | Must not be empty |
| summary | string | Summary of search results | Must not be empty |
| source_documents | array of string | List of source documents used | Must be an array |
| created_at | string (ISO 8601) | When the entry was created | ISO 8601 format |
| ttl_seconds | u64 | Expiration time in seconds | Must be > 0 |
| hit_count | u64 | Number of times the cache was accessed | Default 0 |

**Constraint**: cache_key must be unique. If the query matches an existing cache entry, hit_count is incremented.

### GraphNode

A node in the codebase graph stored in the `code_index` collection.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| node_id | string | Unique node ID | Must be unique |
| node_type | string | Node type (file/function/class/trait) | Must not be empty |
| file_path | string | File path relative to the project root | Must not be empty |
| symbol_name | string | Symbol name (function, class, struct, etc.) | Must not be empty |

### GraphEdge

An edge in the graph representing a relationship between nodes.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| edge_id | string | Unique edge ID | Must be unique |
| from_node | string | Source node ID | Must exist in GraphNode |
| to_node | string | Destination node ID | Must exist in GraphNode |
| edge_type | string | Edge type (import/call/depends_on) | Must not be empty |
| weight | f64 | Edge weight (default 1.0) | Must be > 0 |

### GraphTraversalResult

A traversal result stored in the events collection.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| traversal_id | string | Unique traversal ID | Must be unique |
| start_node | string | Starting node of the traversal | Must exist in GraphNode |
| visited_nodes | array of string | List of visited nodes | Must be an array |
| edges_traversed | array of string | List of edges traversed | Must be an array |
| timestamp | string (ISO 8601) | When the traversal was performed | ISO 8601 format |
| status | string | Status (started/completed/failed) | Must be one of the valid values |

### CacheStats

Cache statistics stored in the `context_cache` collection.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| total_hits | u64 | Number of cache hits | Default 0 |
| total_misses | u64 | Number of cache misses | Default 0 |
| eviction_count | u64 | Number of evicted entries (LRU) | Default 0 |
| cache_size | u64 | Current number of entries | Must be >= 0 |

## Relationships

- GraphNode 1:N GraphEdge (a node can have many outgoing edges)
- GraphEdge N:1 GraphNode (an edge connects two nodes)
- CacheEntry 1:N event (one cache entry can produce many hit/miss events)

## Validation Rules

1. **Cache key uniqueness**: cache_key must be unique per query. If the query matches an existing cache entry, hit_count is incremented and last_accessed is updated.
2. **TTL validation**: ttl_seconds must be > 0. If the TTL elapses, the entry is considered expired and must be re-queried to the LLM endpoint.
3. **Edge validity**: from_node and to_node must exist in GraphNode before an edge is created.
4. **Graph cycle prevention**: Traversal must use a visited set to avoid infinite loops.
5. **Required fields**: All fields that must not be empty must be filled at create time.

## State Transitions

| Entity | From | To | Condition |
|--------|------|-----|-----------|
| CacheEntry | created | hit | Cache accessed again (hit_count incremented) |
| CacheEntry | created | expired | TTL elapsed, entry no longer valid |
| CacheEntry | created | evicted | Cache full, oldest entry removed (LRU) |
| GraphTraversalResult | started | completed | All nodes within the maximum depth explored |
| GraphTraversalResult | started | failed | Error during traversal (e.g.: start_node not found) |
