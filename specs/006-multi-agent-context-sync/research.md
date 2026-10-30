# Research Findings — HakoAgent Multi-Agent Context Sync

**Feature**: 006-multi-agent-context-sync  
**Date**: 2026-10-29  
**Status**: Complete

## Unknowns Resolution

| Unknown | Resolution | Source |
|---------|-----------|--------|
| HakoDB FFI function signatures | Verified via `nm -D` on prebuilt `.so` | `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` |
| Multi-agent sync mechanism | Shared filesystem HakoDB + `actor` attribution field | Constitution principle 12 (Real Hakodb FFI) |
| Fallback when library missing | Graceful fallback to JSON files under `.hakoagent/memory/` | Existing `hakoagent` dual-write pattern |

## Technology Choices

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Python 3 (stdlib only) | No build step, easy to maintain, ctypes-compatible | Rust (requires cargo build, toolchain) |
| Prebuilt HakoDB `.so` via ctypes | Real library used directly, `hakodb.h` as ABI reference | Build from source with Rust/cargo |
| Shared filesystem for multi-agent sync | No network server needed; agents share `.hakoagent/hakoagent.db` | Network sync server (complex, out of scope) |
| `actor` attribution field | Enables cross-agent document ownership tracking | No attribution (cannot distinguish agents) |
| TTL-based context_cache (default 300s) | Reduces redundant LLM calls | No cache (every query hits LLM) |
| Append-only event guard (`event_id` uniqueness) | Prevents overwrites, supports time-travel | Mutable events (loses history) |

## FFI Symbol Verification

The prebuilt `libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` (v0.20.0) exports the following functions verified via `nm -D`:

| Function | Signature (from `hakodb.h`) | Status |
|----------|---------------------------|--------|
| `hk_engine_open` | `struct HK_Engine *hk_engine_open(const char *path)` | ✅ Exported |
| `hk_engine_free` | `void hk_engine_free(struct HK_Engine *engine)` | ✅ Exported |
| `hk_engine_insert_json` | `int32_t hk_engine_insert_json(engine, collection, doc_id, json)` | ✅ Exported |
| `hk_engine_get_json` | `char *hk_engine_get_json(engine, collection, doc_id)` | ✅ Exported |
| `hk_engine_delete` | `int32_t hk_engine_delete(engine, collection, doc_id)` | ✅ Exported |
| `hk_string_free` | `void hk_string_free(char *value)` | ✅ Exported |

The current Python FFI wrapper in `hakoagent` has been updated:
- `hk_engine_put` → uses `hk_engine_insert_json` (was incorrectly using `hk_engine_insert` with 4 string args)
- `hk_engine_get` → uses `hk_engine_get_json` with `c_void_p` restype + `ctypes.string_at()` + `hk_string_free` (was incorrectly returning `c_char_p`)

## Integration Patterns

- **FFI via ctypes**: Load `libhakodb-...so`, call `hk_engine_insert_json`, `hk_engine_get_json`, `hk_engine_delete`, `hk_string_free`
- **Header reference**: `lib/hakodb.h` (v0.20.0, hash-verified) as source of truth for C ABI signatures
- **Dual-write**: All `save_doc`/`load_doc`/`delete_doc` write to both JSON files (fallback) and HakoDB FFI
- **Multi-agent sync**: Shared `.hakoagent/hakoagent.db` on filesystem; `actor` field on every document
- **CLI integration**: `./hakoagent init`, `./hakoagent event_log`, `./hakoagent recall`, `./hakoagent cache stats`

## Best Practices

- Every document stored includes an `actor` field for multi-agent attribution
- Event log is append-only — `event_id` uniqueness checked before write
- Timestamps are ISO 8601
- All runtime data under `.hakoagent/` or project root
- No Rust, Cargo, or build step (Python stdlib only)
- Graceful fallback to JSON when HakoDB library unavailable
