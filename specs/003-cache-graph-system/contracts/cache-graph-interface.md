# Cache & Graph Interface Contract — HakoAgent

**Feature**: 003-cache-graph-system  
**Date**: 2026-10-29  
**Status**: Draft

## Overview

HakoAgent mengekspos antarmuka tool calling untuk caching dan graph traversal. Setiap tool memiliki nama yang diawali dengan `hakoagent.`, parameter yang terdefinisi dengan jelas, dan nilai kembali dalam format JSON untuk kemudahan parsing oleh agen.

## Tool List

| Tool | Deskripsi | Parameter Utama | Return |
|------|-----------|-----------------|--------|
| `hakoagent.cache.get` | Ambil konteks dari cache (HNSW + FTS) | `query` (string), `limit` (integer) | `context_results` (array), `cache_hit` (boolean) |
| `hakoagent.cache.put` | Simpan konteks ke cache | `query` (string), `summary` (string), `ttl_seconds` (integer) | `cache_key` (string), `status` (string) |
| `hakoagent.cache.stats` | Lihat statistik cache | — | `total_hits` (integer), `total_misses` (integer), `eviction_count` (integer), `cache_size` (integer) |
| `hakoagent.graph.traverse` | Traversal graph (BFS/DFS) | `start_node` (string), `direction` (string), `max_depth` (integer) | `visited_nodes` (array), `edges_traversed` (array) |
| `hakoagent.graph.shortest-path` | Jalur terpendek (Dijkstra) | `from_node` (string), `to_node` (string) | `path_nodes` (array), `total_cost` (float) |
| `hakoagent.graph.dependents` | Node yang tergantung pada node tertentu | `node_id` (string) | `dependent_nodes` (array) |
| `hakoagent.graph.dependents-reverse` | Node yang ditergantung oleh node tertentu | `node_id` (string) | `dependent_reverse_nodes` (array) |
| `hakoagent.events` | Lihat histori kronologis termasuk caching dan traversal events | `limit` (integer), `session_id` (string) | `events_list` (array) |

## Response Format

Semua respons dalam format JSON:

```json
{
  "status": "success|error",
  "data": { ... },
  "error": null | { "code": "...", "message": "..." }
}
```

Contoh respons sukses `hakoagent.cache.get`:
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
    "summary": "Gunakan Result<T, E> dengan ? operator untuk propagasi error"
  },
  "error": null
}
```

Contoh respons sukses `hakoagent.graph.traverse`:
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

- Cache TTL default adalah 300 detik (5 menit). Setelah TTL habis, entri dianggap expired.
- Cache menggunakan LRU eviction ketika penuh.
- Graph traversal menggunakan visited set untuk menghindari siklus tak terbatas.
- Setiap operasi caching dan traversal dicatat ke koleksi `events` (append-only).
- Error pada satu node tidak menghentikan traversal node lainnya.

## Integration Example (Pseudocode)

```python
from hakoagent import HakoAgentMemory

agent = HakoAgentMemory(db_path="./.hakoagent/hakoagent.db")

# 1. Coba ambil konteks dari cache
context = agent.cache.get(query="bagaimana implementasi error handling Rust?", limit=5)

if context.cache_hit:
    print("Cache hit! Menggunakan hasil dari cache.")
else:
    print("Cache miss. Memanggil endpoint LLM...")
    # Panggil endpoint LLM dan simpan hasilnya ke cache
    agent.cache.put(
        query="bagaimana implementasi error handling Rust?",
        summary="Gunakan Result<T, E> dengan ? operator...",
        ttl_seconds=300
    )

# 2. Traversal graph codebase
result = agent.graph.traverse(
    start_node="validate_input",
    direction="in",
    max_depth=2
)
print(f"Node yang dikunjungi: {result.visited_nodes}")

# 3. Cari jalur terpendek
path = agent.graph.shortest_path(
    from_node="main",
    to_node="error_handler"
)
print(f"Jalur terpendek: {path.path_nodes}")

# 4. Lihat statistik cache
stats = agent.cache.stats()
print(f"Cache hit ratio: {stats.total_hits / (stats.total_hits + stats.total_misses):.2%}")
```
