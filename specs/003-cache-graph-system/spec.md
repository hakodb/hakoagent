# Feature Specification: System Caching and Graph Traversal Tools

**Feature Branch**: `003-cache-graph-system`

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "implement system caching, graph traversal features and tools"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agent uses context caching to reduce LLM endpoint calls (Priority: P1)

The system automatically stores context search results and summaries in a cache so the agent does not need to call the LLM endpoint repeatedly for the same or similar queries.

**Why this priority**: Reduces LLM endpoint cost and latency, and improves the agent's response speed.

**Independent Test**: Can be tested independently by performing the same query twice and verifying that the second call is served from the cache, not the LLM endpoint.

**Acceptance Scenarios**:

1. **Given** the cache is empty, **When** the agent performs a query for the first time, **Then** the system calls the LLM endpoint and stores the result in the cache
2. **Given** the cache already holds the query result, **When** the agent performs the same query, **Then** the system returns the result from the cache without calling the LLM endpoint
3. **Given** the cache entry has expired (TTL elapsed), **When** the agent performs the same query, **Then** the system calls the LLM endpoint again and refreshes the cache

---

### User Story 2 - Agent explores the codebase dependency graph (Priority: P1)

The agent can navigate and trace dependencies between symbols, files, and components in the codebase using graph traversal (BFS, Dijkstra, dependents lookup).

**Why this priority**: Understanding codebase structure and change impact is critical for safe and efficient development.

**Independent Test**: Can be tested independently by starting a traversal from a specific symbol and verifying that all connected nodes are found correctly.

**Acceptance Scenarios**:

1. **Given** the codebase is indexed, **When** the agent requests the dependents of file X, **Then** the system returns all files that import or use file X
2. **Given** two symbols in the codebase, **When** the agent searches for the shortest path between them, **Then** the system returns the shortest dependency chain
3. **Given** a starting symbol and a maximum depth, **When** the agent performs a BFS traversal, **Then** the system returns all nodes reachable within that depth

---

### User Story 3 - Agent receives notifications and reports after caching and graph traversal operations (Priority: P2)

Every time a caching or graph traversal operation finishes, the agent receives a concise notification about what was processed and whether there were errors.

**Why this priority**: Gives the agent visibility into internal operation status without manual checking.

**Independent Test**: Can be tested independently by triggering a file change or a cache query and verifying that the notification appears.

**Acceptance Scenarios**:

1. **Given** a cache hit occurs, **When** the operation finishes, **Then** the agent receives a concise notification (number of files, success/error status)
2. **Given** graph traversal finishes, **When** the operation finishes, **Then** the agent receives a summary of the number of nodes and edges explored
3. **Given** an operation fails, **Then** the agent receives an error notification for that operation without other operations being stopped

---

### Edge Cases

- Cache full: the system must evict the oldest entry (LRU eviction)
- Graph with cycles: traversal must not get stuck in an infinite loop
- File deleted while the graph is being traversed: the system must handle graceful degradation
- Empty or invalid query: the system returns an informative error
- Directory does not exist: the system gives a clear error
- File with an unsupported extension: skipped during graph indexing

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST store context search results and summaries in the `context_cache` collection with a configurable TTL. The default TTL is 300 seconds (5 minutes). After the TTL elapses, the cache entry is considered expired and the system must refetch from the LLM endpoint.
- **FR-002**: The system MUST perform a cache lookup before calling the LLM endpoint for the same or similar queries
- **FR-003**: The system MUST provide graph traversal (BFS/DFS) to trace codebase dependencies from the `code_index` collection
- **FR-004**: The system MUST provide shortest path (Dijkstra) between two symbols in the codebase
- **FR-005**: The system MUST provide dependents lookup (who imports/uses file or function X)
- **FR-006**: The system MUST provide dependents reverse (what is called by file or function X)
- **FR-007**: The system MUST handle cycles in the graph without getting stuck in an infinite loop (visited set)
- **FR-008**: The system MUST notify the agent after every caching and graph traversal operation completes or fails
- **FR-009**: The system MUST contain no references to external tools such as hakoagent in any code or documentation
- **FR-010**: The system MUST store all hakoagent-related files under the `.hakoagent/` directory or the project root

### Key Entities *(include if feature involves data)*

- **CacheEntry**: A cache entry with cache_key, query, summary, source_documents, created_at, ttl_seconds, hit_count
- **GraphNode**: A node in the codebase graph with node_id, node_type (file/function/class/trait), file_path, symbol_name
- **GraphEdge**: An edge in the graph with edge_id, from_node, to_node, edge_type (import/call/depends_on), weight
- **GraphTraversalResult**: A traversal result with traversal_id, start_node, visited_nodes, edges_traversed, timestamp, status
- **CacheStats**: Cache statistics with total_hits, total_misses, eviction_count, cache_size

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cache hit ratio ≥ 50% for frequently repeated queries
- **SC-002**: Cache hit response time < 100ms
- **SC-003**: Graph traversal up to a maximum depth of 10 levels without significant performance degradation
- **SC-004**: 0 expired cache entries still in use
- **SC-005**: 0 references to "hakoagent" found across all source files, documentation, and project configuration
- **SC-006**: All hakoagent-related files stored under the `.hakoagent/` directory or the project root

## Assumptions

- HakoDB is initialized before caching and graph traversal run
- The codebase has been indexed through the auto codebase indexing feature (feature 002)
- A file system watcher is available to detect codebase changes
- Supported file formats for graph traversal are source code (.rs, .py, .js, .ts, .go, etc.)

---

## Clarifications

### Session 2026-10-29

- Q: How many seconds is the default expiration time (TTL) for a context cache entry before the system must refetch from the LLM endpoint? → A: 300 seconds (5 minutes)

---
