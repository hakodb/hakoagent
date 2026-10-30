# Context Cache - Caching untuk HakoAgent

**Fitur**: 003-cache-graph-system  
**Tanggal**: 2026-10-29  
**Status**: Implementasi  
**Status**: Draft

## Overview

Context Cache menyimpan hasil pencarian konteks (HNSW + FTS) dan rangkuman untuk mengurangi panggilan endpoint LLM. Cache menggunakan TTL (Time To Live) dan LRU eviction untuk manajemen memori.

## File yang Terlibat

- `hakoagent` - Python CLI script (fungsi `cache_put_internal`, `cache_get_internal`, `cache_put`, `cache_get`, `cache_stats`)
- `.hakoagent/memory/context_cache/` - Penyimpanan file cache (JSON per entri)
- `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` - Prebuilt HakoDB shared library (opsional, via FFI)
- `lib/hakodb.h` - C ABI header (referensi tanda tangan fungsi)

## Schema Koleksi `context_cache`

| Field | Tipe | Deskripsi | Validasi |
|-------|------|-----------|----------|
| cache_key | String | Kunci cache unik (hash dari query) | Harus unik |
| query | String | Query asli yang dicari | Tidak boleh kosong |
| summary | String | Rangkuman hasil pencarian | Tidak boleh kosong |
| source_documents | Array<String> | Daftar dokumen sumber yang digunakan | Harus berupa array |
| created_at | String (ISO 8601) | Waktu entri dibuat | Format ISO 8601 |
| ttl_seconds | u64 | Waktu kedaluwarsa dalam detik | Harus > 0 |
| hit_count | u64 | Jumlah kali cache diakses | Default 0 |

## State Transitions

| Entity | From | To | Kondisi |
|--------|------|-----|---------|
| CacheEntry | created | hit | Cache diakses kembali (hit_count ditambah) |
| CacheEntry | created | expired | TTL habis, entri tidak valid lagi |
| CacheEntry | created | evicted | Cache penuh, entri terlama di-hapus (LRU) |

## Aturan Validasi

1. **Cache key uniqueness**: cache_key harus unik per query. Jika query sama dengan cache yang ada, hit_count ditambah.
2. **TTL validation**: ttl_seconds harus > 0. Jika TTL habis, entri dianggap expired dan harus di-requery ke endpoint LLM.
3. **LRU eviction**: Jika cache penuh, entri terlama (least recently used) di-hapus.

## Endpoint LLM Cache Logic

```
function retrieve_context(query):
    cache_key = hash(query)
    cached = cache.get(cache_key)
    
    if cached and not cached.expired:
        cached.hit_count += 1
        return cached.summary  # Cache hit
    
    # Cache miss - query ke endpoint LLM
    result = llm_endpoint.query(query)
    summary = summarize(result)
    
    cache.put(cache_key, query, summary, ttl_seconds=300)
    return summary
```

## CLI Commands

### `hakoagent cache stats`
Menampilkan statistik cache: total hits, total misses, eviction count, cache size.

### `hakoagent cache recall <query>`
Ambil konteks dari cache. Jika cache hit, kembalikan hasil. Jika cache miss atau expired, kirim ke endpoint LLM.

## Dependencies

- Python standard library only (`json`, `hashlib`, `uuid`, `time`, `ctypes`)
- Prebuilt HakoDB shared library (`lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so`) via ctypes

## Contoh Penggunaan

```bash
# Ambil konteks dari cache (atau LLM jika cache miss)
./hakoagent recall "bagaimana implementasi error handling Python?"

# Lihat statistik cache
./hakoagent cache stats
```
