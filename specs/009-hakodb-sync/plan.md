# Implementation Plan: Hakodb Sync (Optional, Mesh Default)

**Branch**: `009-hakodb-sync` | **Date**: 2026-10-29 | **Spec**: `specs/009-hakodb-sync/spec.md`

**Input**: Feature specification from `/specs/009-hakodb-sync/spec.md`

**Reference**: `lib/hakodb.h` (v0.20.0) — `hk_net_syncer_*`, `hk_config_set_replication_collections`, `hk_config_set_sync_excluded`, `hk_engine_set_collection_local`, `hk_engine_replicate_collection`, `hk_engine_get_versioned`, `hk_engine_watch`, `hk_engine_backup`, `HK_CloudSync`

---

## Summary

Add optional hakodb-native synchronization to hakoagent, replacing the git-based `team sync` push/pull logic. Sync is user-triggered via `hakoagent sync <enable|disable|status|sync-now|backup>` commands. Default: sync off, mesh type. Cloud sync optional with `--server` + `--token`. No socket_sync. No Git push/pull.

---

## Technical Context

**Language/Version**: Python 3.6.8 (stdlib only, no external dependencies)

**Primary Dependencies**: Python standard library (`ctypes`, `json`, `uuid`, `time`, `datetime`, `subprocess`); prebuilt hakodb shared library via `ctypes`; C ABI header `lib/hakodb.h` (v0.20.0)

**New FFI Functions Needed** (from `lib/hakodb.h`):
- `hk_net_syncer_new(engine, name, room_key)` → `HK_NetSyncer*`
- `hk_net_syncer_set_discovery(syncer, mode)` → int32_t (0=mDNS, 1=UDP, 2=both)
- `hk_net_syncer_start(syncer, port)` → int32_t
- `hk_net_syncer_status(syncer)` → char* (JSON)
- `hk_config_set_replication_collections(config, collections_json)` → int32_t
- `hk_config_set_sync_excluded(config, collections_json)` → int32_t
- `hk_engine_set_collection_local(engine, collection, local)` → int32_t
- `hk_engine_replicate_collection(engine, collection)` → int32_t
- `hk_engine_get_versioned(engine, collection, doc_id, out_version)` → HK_Doc*
- `hk_engine_watch(engine, collection, callback, user_data)` → HK_Watch*
- `hk_watch_free(watch)` → void
- `hk_engine_backup(engine, path)` → int32_t
- `hk_config_new()` → HK_Config*
- `hk_config_free(config)` → void
- `hk_engine_open_with_config(path, config)` → HK_Engine*

**Current State** (to be removed):
- `cmd_team` subcommand `sync` — runs `git pull --no-rebase` (FR-044: remove)
- No sync state tracking in memory

**Storage**: Sync state stored in `.hakoagent/sync/sync.json` (config) — separate from hakodb `.db`

**Testing**: `test_hakoagent.py` — existing 75 tests + new sync tests (enable/disable/status/sync-now/backup, local-only, replication collections)

**Target Platform**: Linux (x86_64 glibc2.28-el8)

**Constraints**: No Git push/pull for sync; sync is optional and off by default; mesh default; no socket_sync; cloud sync optional with server+token

---

## Constitution Check

| Constitution Principle | Status | Notes |
|-------------------|--------|---------|
| Smart Memory | Met | Sync extends memory across agents |
| Anti-Lupa | Met | Synced context available across agents |
| Kronologi & Histori | Met | Events + revisions preserved during sync |
| Consistency | Met | Sync config consistent across agents |
| Cross-Model Consistency | Met | Same sync flow for all LLM models |
| Vigilance | Met | Sync status visible, conflicts detectable |
| Clear Target | Met | Sync commands have clear targets |
| Codebase Fluency | Met | Sync affects code_index/code_edges |
| Context Frugality | Met | Synced context reduces redundant LLM calls |
| Self Skill Improvement | Met | Synced skills available to all agents |
| Python Only | Met | ctypes to hakodb .so, no external deps |
| Real Hakodb FFI | Met | ctypes to libhakodb .so sync APIs |
| Code Quality | Met | Clean Python, no bare except |
| Testing | Met | Unit tests for sync functions |
| Maintainability | Met | Docs updated, no stale git references |

No violations. Constitution check PASSED.

---

## Project Structure

### Documentation (this feature)

```text
specs/009-hakodb-sync/
├── spec.md          # Feature specification
├── plan.md          # Implementation plan (this file)
├── research.md      # Phase 0 output (hakodb sync API analysis)
├── data-model.md    # Phase 1 output (SyncConfig, SyncPeer, SyncChange)
├── quickstart.md    # Phase 1 output (validation scenarios)
├── contracts/
│   └── hakodb-sync-interface.md  # Phase 1 output (CLI contracts)
└── tasks.md         # Phase 2 output (implementation tasks)
```

### Source Code Changes (repository root)

```text
hakoagent                      # Python CLI script — extended with sync commands
lib/
├── libhakodb-x86_64-unknown-linux-glibc2.28-el8.so   # Prebuilt hakodb (v0.20.0)
├── hakodb.h                                               # Hakodb C ABI header (v0.20.0)
└── SHA256SUMS.txt                                         # Release checksums
.hakoagent/
├── hakoagent.db                 # Hakodb database file (synced via hakodb net syncer)
├── sync/
│   └── sync.json                # Sync configuration (enabled, type, room_key, etc.)
├── memory/                      # JSON files per collection (fallback / dual-write)
├── skills/
├── sessions/
├── logs/
└── _indices/
specs/                         # Feature specs (001-009)
test_hakoagent.py              # Python stdlib unittest (75+ tests)
```

---

## Phase 0: Outline & Research

### Unknowns from Technical Context

| Unknown | Status | Resolution |
|---------|--------|----------|
| `hk_net_syncer_new` signature confirmed vs real .so | Open | Verify `hk_net_syncer_new`, `hk_net_syncer_set_discovery`, `hk_net_syncer_start`, `hk_net_syncer_status` exist in .so |
| `HK_CloudSync` cloud sync functions | Open | Check if cloud sync functions exist in .so (HK_CloudSync type in header) |
| `hk_engine_watch` callback signature in ctypes | Open | Verify callback type `HK_OnSnapshotCallback` works with ctypes |
| Room key format and validation | Open | Define room key format (string, min length) |
| Port selection for mesh sync | Open | Default port, user-overridable |
| Sync state persistence (sync.json) | Open | JSON file under `.hakoagent/sync/sync.json` |

### Research Findings

**Hakodb sync capabilities** (from `lib/hakodb.h` v0.20.0):

The header defines these sync-related types and functions:

- `HK_NetSyncer` — network syncer handle
- `HK_CloudSync` — cloud sync handle (type declared, functions may exist in .so)
- `HK_SocketSync` — socket sync handle (NOT to be used per requirements)
- `hk_net_syncer_new(engine, name, room_key)` — create syncer
- `hk_net_syncer_set_discovery(syncer, mode)` — 0=mDNS, 1=UDP broadcast, 2=both
- `hk_net_syncer_start(syncer, port)` — start listening
- `hk_net_syncer_status(syncer)` — get status JSON
- `hk_config_set_replication_collections(config, collections_json)` — opt-in collections
- `hk_config_set_sync_excluded(config, collections_json)` — excluded collections
- `hk_engine_set_collection_local(engine, collection, local)` — local-only toggle
- `hk_engine_replicate_collection(engine, collection)` — rejoin replication
- `hk_engine_get_versioned(engine, collection, doc_id, out_version)` — versioned read
- `hk_engine_watch(engine, collection, callback, user_data)` — change watcher
- `hk_engine_backup(engine, path)` — backup database

**Gap vs current hakoagent:**

| Capability | Current hakoagent | After US9-US11 |
|------------|------------------|----------------|
| Sync enable/disable | ❌ Not present | ✅ `hakoagent sync enable/disable` |
| Sync status | ❌ Not present | ✅ `hakoagent sync status` |
| Manual sync trigger | ❌ Not present | ✅ `hakoagent sync sync-now` |
| Mesh sync (mDNS/UDP) | ❌ Not present | ✅ Via `hk_net_syncer_*` |
| Cloud sync | ❌ Not present | ✅ Via `HK_CloudSync` + server+token |
| Local-only collections | ❌ Not present | ✅ Via `hk_engine_set_collection_local` |
| Versioned reads (conflict detection) | ❌ Not present | ✅ Via `hk_engine_get_versioned` |
| Change watcher | ❌ Not present | ✅ Via `hk_engine_watch` |
| Database backup | ❌ Not present | ✅ Via `hk_engine_backup` |
| Git team sync | ❌ Present (`team sync`) | ✅ Removed |

Output: `research.md` documenting hakodb sync API analysis and adaptation plan.

---

## Phase 1: Design & Contracts

### Data Model (`data-model.md`)

Entities:

| Entity | Key Attributes |
|--------|---------------|
| **SyncConfig** | `enabled` (bool), `type` (mesh|cloud), `room_key` (str), `port` (int), `server_url` (str|None), `api_token` (str|None), `replication_collections` (list), `local_only_collections` (list), `started_at` (ISO 8601), `actor` (str) |
| **SyncPeer** | `peer_id` (str), `address` (str), `mode` (mesh|cloud), `last_seen` (ISO 8601), `status` (connected|disconnected) |
| **SyncChange** | `change_id` (str), `collection` (str), `doc_id` (str), `operation` (insert|update|delete|soft_delete), `version` (int), `timestamp` (ISO 8601), `synced` (bool) |

Collections: No new hakodb collections needed. Sync config stored in `.hakoagent/sync/sync.json` (JSON file).

State transitions:
- SyncConfig: disabled → enabled (with type, room_key, etc.) → disabled

### Interface Contracts (`contracts/`)

**File**: `contracts/hakodb-sync-interface.md`

| Tool | Parameter | Return |
|------|-----------|--------|
| `hakoagent sync enable` | `--type`, `--room-key`, `--port`, `--server`, `--token`, `--collections`, `--local-only` | status, mode, peers, collections |
| `hakoagent sync disable` | — | status |
| `hakoagent sync status` | — | mode, peers, replicated_collections, local_only, pending_changes |
| `hakoagent sync sync-now` | — | changes_synced, peers_contacted |
| `hakoagent sync backup` | `<path>` | backup_path, status |

Return value always in JSON format for harness agent parsing.

### Quickstart Validation Guide (`quickstart.md`)

**Prerequisites**:
- Python 3 (stdlib only)
- Prebuilt hakodb library at `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so`

**Setup**:
```bash
# Initialize database
./hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

**Mesh sync (default)**:
```bash
# Agent A
./hakoagent sync enable --type mesh --room-key my-room-key --port 9876

# Agent B (same room key)
./hakoagent sync enable --type mesh --room-key my-room-key --port 9877
```

**Cloud sync (optional)**:
```bash
./hakoagent sync enable --type cloud --server https://sync.example.com --token <api-token> --room-key my-room-key
```

**Status**:
```bash
./hakoagent sync status
```

**Manual sync**:
```bash
./hakoagent sync sync-now
```

**Disable**:
```bash
./hakoagent sync disable
```

**Backup**:
```bash
./hakoagent sync backup ./backup.db
```

**Expected outcomes**:
- Sync starts/stops without Git
- Mesh agents with same room key discover each other
- Cloud agents connect to server with token
- Local-only collections excluded from replication
- All 75+ tests pass

### Re-evaluate Constitution Check (post-design)

| Constitution Principle | Status Post-Design | Notes |
|-------------------|-------------------|---------|
| Smart Memory | Met | Sync extends memory across agents |
| Anti-Lupa | Met | Synced context available across agents |
| Kronologi & Histori | Met | Events + revisions preserved |
| Consistency | Met | Sync config consistent |
| Cross-Model Consistency | Met | Same sync flow |
| Vigilance | Met | Sync status visible |
| Clear Target | Met | Clear sync commands |
| Codebase Fluency | Met | Sync affects all collections |
| Context Frugality | Met | Synced context reduces LLM calls |
| Self Skill Improvement | Met | Synced skills available to all agents |
| Python Only | Met | ctypes only, no external deps |
| Real Hakodb FFI | Met | ctypes to libhakodb .so sync APIs |
| Code Quality | Met | Clean Python |
| Testing | Met | Unit tests for sync |
| Maintainability | Met | Git sync removed, docs updated |

No violations. Constitution check PASSED post-design.

---

## Phase 2: Implementation Tasks (see `tasks.md`)

Plan workflow complete. Ready to proceed to `/speckit-implement`.
