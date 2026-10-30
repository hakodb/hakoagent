# Data Model — System Caching dan Graph Traversal

**Feature**: 003-cache-graph-system  
**Date**: 2026-10-29  
**Status**: Draft

## Entities

### CacheEntry

Entri cache yang disimpan di koleksi `context_cache` HakoDB.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| cache_key | string | Kunci cache unik (hash dari query) | Harus unik |
| query | string | Query asli yang dicari | Tidak boleh kosong |
| summary | string | Rangkuman hasil pencarian | Tidak boleh kosong |
| source_documents | array of string | Daftar dokumen sumber yang digunakan | Harus berupa array |
| created_at | string (ISO 8601) | Waktu entri dibuat | Format ISO 8601 |
| ttl_seconds | u64 | Waktu kedaluwarsa dalam detik | Harus > 0 |
| hit_count | u64 | Jumlah kali cache diakses | Default 0 |

**Constraint**: cache_key harus unik. Jika query sama dengan cache yang ada, hit_count ditambahkan.

### GraphNode

Node dalam graph codebase yang disimpan di koleksi `code_index`.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| node_id | string | ID unik node | Harus unik |
| node_type | string | Tipe node (file/function/class/trait) | Tidak boleh kosong |
| file_path | string | Path file relatif dari root proyek | Tidak boleh kosong |
| symbol_name | string | Nama simbol (fungsi, class, struct, dll.) | Tidak boleh kosong |

### GraphEdge

Edge dalam graph yang mewakili hubungan antar node.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| edge_id | string | ID unik edge | Harus unik |
| from_node | string | ID node asal | Harus ada di GraphNode |
| to_node | string | ID node tujuan | Harus ada di GraphNode |
| edge_type | string | Tipe edge (import/call/depends_on) | Tidak boleh kosong |
| weight | f64 | Bobot edge (default 1.0) | Harus > 0 |

### GraphTraversalResult

Hasil traversal yang disimpan di koleksi events.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| traversal_id | string | ID unik traversal | Harus unik |
| start_node | string | Node awal traversal | Harus ada di GraphNode |
| visited_nodes | array of string | Daftar node yang dikunjungi | Harus berupa array |
| edges_traversed | array of string | Daftar edge yang dilalui | Harus berupa array |
| timestamp | string (ISO 8601) | Waktu traversal dilakukan | Format ISO 8601 |
| status | string | Status (started/completed/failed) | Harus salah satu dari nilai yang valid |

### CacheStats

Statistik cache yang disimpan di koleksi `context_cache`.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| total_hits | u64 | Jumlah cache hit | Default 0 |
| total_misses | u64 | Jumlah cache miss | Default 0 |
| eviction_count | u64 | Jumlah entri yang di-evict (LRU) | Default 0 |
| cache_size | u64 | Jumlah entri saat ini | Harus >= 0 |

## Relationships

- GraphNode 1:N GraphEdge (satu node dapat memiliki banyak edge keluar)
- GraphEdge N:1 GraphNode (satu edge terhubung ke dua node)
- CacheEntry 1:N event (satu entri cache dapat menghasilkan banyak event hit/miss)

## Validation Rules

1. **Cache key uniqueness**: cache_key harus unik per query. Jika query sama dengan cache yang ada, hit_count ditambahkan dan last_accessed diupdate.
2. **TTL validation**: ttl_seconds harus > 0. Jika TTL habis, entri dianggap expired dan harus di-requery ke endpoint LLM.
3. **Edge validity**: from_node dan to_node harus ada di GraphNode sebelum edge dibuat.
4. **Graph cycle prevention**: Traversal harus menggunakan visited set untuk menghindari loop tak terbatas.
5. **Required fields**: Semua field yang tidak boleh kosong harus diisi saat create.

## State Transitions

| Entity | From | To | Condition |
|--------|------|-----|-----------|
| CacheEntry | created | hit | Cache diakses kembali (hit_count ditambah) |
| CacheEntry | created | expired | TTL habis, entri tidak valid lagi |
| CacheEntry | created | evicted | Cache penuh, entri terlama di-hapus (LRU) |
| GraphTraversalResult | started | completed | Semua node dalam depth maksimum telah dijelajahi |
| GraphTraversalResult | started | failed | Error saat traversal (misalnya: start_node tidak ditemukan) |
