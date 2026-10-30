# Research — Hakodb Sync Gap Analysis (US9-US11)

**Feature**: 009-hakodb-sync  
**Date**: 2026-10-29  
**Status**: Draft

## Current State (No Sync)

Hakoagent currently has **no synchronization capability** between agents. Each agent process:
1. Opens its own hakodb engine handle via `hk_engine_open(MEMORY_DIR)`
2. Reads/writes JSON files under `.hakoagent/memory/<collection>/`
3. Dual-writes to hakodb via `hk_engine_insert_json`
4. No cross-process, no cross-machine coordination

## Current Team Sync (Git-based, to be removed)

`hakoagent team sync` runs `git pull --no-rebase` on the project root. This is inappropriate because:
- It pulls the entire `.hakoagent/` directory including the binary `.db` file
- Git cannot merge binary database files — causes corruption or conflicts
- It only pulls, never pushes
- No conflict resolution for concurrent document edits

This will be **removed** per FR-044.

## Hakodb Sync Capabilities (from `lib/hakodb.h` v0.20.0)

The header file declares the following sync-related types and functions:

### Types
- `HK_NetSyncer` — network syncer handle
- `HK_CloudSync` — cloud sync handle (type declared; cloud functions may exist in .so)
- `HK_SocketSync` — socket sync handle (**NOT to be used** per requirements)
- `HK_OnSnapshotCallback` — callback type for watch notifications

### NetSyncer Functions
| Function | Signature | Purpose |
|----------|-----------|---------|
| `hk_net_syncer_new` | `struct HK_NetSyncer *(struct HK_Engine *, const char *, const char *)` | Create syncer with engine, name, room_key |
| `hk_net_syncer_set_discovery` | `int32_t (struct HK_NetSyncer *, int32_t)` | 0=mDNS, 1=UDP broadcast, 2=both |
| `hk_net_syncer_start` | `int32_t (struct HK_NetSyncer *, uint16_t)` | Start listening on port |
| `hk_net_syncer_status` | `char *(struct HK_NetSyncer *)` | Get status as JSON (free with hk_string_free) |

### Config Functions (for sync)
| Function | Signature | Purpose |
|----------|-----------|---------|
| `hk_config_new` | `struct HK_Config *(void)` | Create config |
| `hk_config_free` | `void (struct HK_Config *)` | Free config |
| `hk_engine_open_with_config` | `struct HK_Engine *(const char *, struct HK_Config *)` | Open engine with config |
| `hk_config_set_replication_collections` | `int32_t (struct HK_Config *, const char *)` | JSON array of collections to replicate |
| `hk_config_set_sync_excluded` | `int32_t (struct HK_Config *, const char *)` | JSON array of collections excluded from all sync planes |

### Engine Functions (for sync)
| Function | Signature | Purpose |
|----------|-----------|---------|
| `hk_engine_set_collection_local` | `int32_t (struct HK_Engine *, const char *, int32_t)` | Mark collection local-only (never syncs) |
| `hk_engine_replicate_collection` | `int32_t (struct HK_Engine *, const char *)` | Rejoin collection to replication |
| `hk_engine_get_versioned` | `struct HK_Doc *(struct HK_Engine *, const char *, const char *, uint64_t *)` | Atomic (doc, version) read for conflict detection |
| `hk_engine_watch` | `struct HK_Watch *(struct HK_Engine *, const char *, HK_OnSnapshotCallback, void *)` | Watch collection for changes |
| `hk_watch_free` | `void (struct HK_Watch *)` | Free watch handle |
| `hk_engine_backup` | `int32_t (struct HK_Engine *, const char *)` | Backup database to path |

### Cloud Sync
- `HK_CloudSync` type is declared in header but cloud sync function signatures were **not fully visible** in the header (truncated at line 1273). Will verify against `.so` during implementation. If cloud functions exist, they will be wrapped; if not, cloud sync will return an informative error.

### NOT to be used (per requirements)
- `HK_SocketSync` / socket sync functions
- Any socket-based sync mechanism

## Adaptation Plan

| MCP/git approach | Hakodb sync approach |
|------------------|---------------------|
| `git pull --no-rebase` | `hk_net_syncer_*` + record-level replication |
| Entire directory sync | Per-collection replication control |
| No conflict detection | `hk_engine_get_versioned` for version-aware reads |
| No change notification | `hk_engine_watch` for local change reaction |
| Push/pull via Git | Manual `sync enable/disable/sync-now` |
| Binary .db corruption risk | Hakodb-native record-level sync |

## Output

`research.md` documents the hakodb sync API analysis and adaptation plan.
