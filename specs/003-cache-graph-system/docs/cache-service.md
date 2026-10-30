# Context Cache - Caching for HakoAgent

**Feature**: 003-cache-graph-system  
**Date**: 2026-10-29  
**Status**: Implemented  
**Status**: Draft

## Overview

Context Cache stores context search results (HNSW + FTS) and summaries to reduce LLM endpoint calls. The cache uses TTL (Time To Live) and LRU eviction for memory management.

## Files Involved

- `hakoagent` - Python CLI script (functions `cache_put_internal`, `cache_get_internal`, `cache_put`, `cache_get`, `cache_stats`)
- `.hakoagent/memory/context_cache/` - Cache file storage (JSON per entry)
- `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` - Prebuilt HakoDB shared library (optional, via FFI)
- `lib/hakodb.h` - C ABI header (function signature reference)

## `context_cache` Collection Schema

| Field | Type | Description | Validation |
|-------|------|-----------|----------|
| cache_key | String | Unique cache key (hash of the query) | Must be unique |
| query | String | The original query being searched | Must not be empty |
| summary | String | Summary of search results | Must not be empty |
| source_documents | Array<String> | List of source documents used | Must be an array |
| created_at | String (ISO 8601) | When the entry was created | ISO 8601 format |
| ttl_seconds | u64 | Expiration time in seconds | Must be > 0 |
| hit_count | u64 | Number of times the cache was accessed | Default 0 |

## State Transitions

| Entity | From | To | Condition |
|--------|------|-----|---------|
| CacheEntry | created | hit | Cache accessed again (hit_count incremented) |
| CacheEntry | created | expired | TTL elapsed, entry no longer valid |
| CacheEntry | created | evicted | Cache full, oldest entry removed (LRU) |

## Validation Rules

1. **Cache key uniqueness**: cache_key must be unique per query. If the query matches an existing cache entry, hit_count is incremented.
2. **TTL validation**: ttl_seconds must be > 0. If the TTL elapses, the entry is considered expired and must be re-queried to the LLM endpoint.
3. **LRU eviction**: If the cache is full, the oldest (least recently used) entry is removed.

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
Shows cache statistics: total hits, total misses, eviction count, cache size.

### `hakoagent cache recall <query>`
Retrieve context from the cache. On a cache hit, return the result. On a cache miss or expiry, send to the LLM endpoint.

## Dependencies

- Python standard library only (`json`, `hashlib`, `uuid`, `time`, `ctypes`)
- Prebuilt HakoDB shared library (`lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so`) via ctypes

## Usage Example

```bash
# Ambil konteks dari cache (atau LLM jika cache miss)
./hakoagent recall "bagaimana implementasi error handling Python?"

# Lihat statistik cache
./hakoagent cache stats
```
