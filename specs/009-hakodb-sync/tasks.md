# Tasks: Hakodb Sync (US9-US11)

**Input**: Design documents from `specs/009-hakodb-sync/` (spec.md, plan.md)

**Prerequisites**: spec.md (required), plan.md (required)

**Organization**: Tasks are grouped by phase corresponding to plan.md phases.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US9, US10, US11)
- Include exact file paths in descriptions

---

## Phase 0: Research (Shared Infrastructure)

- [ ] T001 [P] [US9-US11] Verify hakodb .so exports sync functions: `hk_net_syncer_new`, `hk_net_syncer_set_discovery`, `hk_net_syncer_start`, `hk_net_syncer_status`, `hk_config_set_replication_collections`, `hk_config_set_sync_excluded`, `hk_engine_set_collection_local`, `hk_engine_replicate_collection`, `hk_engine_get_versioned`, `hk_engine_watch`, `hk_engine_backup`
- [ ] T002 [P] [US9-US11] Verify if cloud sync functions (`HK_CloudSync` related) exist in .so
- [ ] T003 [P] [US9-US11] Verify ctypes callback type `HK_OnSnapshotCallback` compatibility with Python
- [ ] T004 [P] [US9-US11] Confirm `.hakoagent/sync/` directory structure for sync.json

---

## Phase 1: FFI Wrappers for Hakodb Sync APIs

- [ ] T005 [P] [US9] Implement `hk_net_syncer_new` FFI wrapper → returns `c_void_p`
- [ ] T006 [P] [US9] Implement `hk_net_syncer_set_discovery` FFI wrapper → `c_int` argtypes `[c_void_p, c_int]`
- [ ] T007 [P] [US9] Implement `hk_net_syncer_start` FFI wrapper → `c_int` argtypes `[c_void_p, c_ushort]`
- [ ] T008 [P] [US9] Implement `hk_net_syncer_status` FFI wrapper → `c_void_p` restype + `string_at()` + `hk_string_free`
- [ ] T009 [P] [US10] Implement `hk_config_set_replication_collections` FFI wrapper
- [ ] T010 [P] [US10] Implement `hk_config_set_sync_excluded` FFI wrapper
- [ ] T011 [P] [US10] Implement `hk_engine_set_collection_local` FFI wrapper → `c_int` argtypes `[c_void_p, c_char_p, c_int]`
- [ ] T012 [P] [US10] Implement `hk_engine_replicate_collection` FFI wrapper
- [ ] T013 [P] [US9] Implement `hk_engine_get_versioned` FFI wrapper → `c_void_p` restype + version output
- [ ] T014 [P] [US9] Implement `hk_engine_watch` FFI wrapper → `c_void_p` restype + callback
- [ ] T015 [P] [US11] Implement `hk_engine_backup` FFI wrapper → `c_int` argtypes `[c_void_p, c_char_p]`
- [ ] T016 [P] [US9] Implement `hk_config_new` / `hk_config_free` FFI wrappers
- [ ] T017 [P] [US9] Implement `hk_engine_open_with_config` FFI wrapper

---

## Phase 2: Sync Config Management (JSON file)

- [ ] T018 [P] [US9] Implement `_sync_config_path()` → `.hakoagent/sync/sync.json`
- [ ] T019 [P] [US9] Implement `_load_sync_config()` → read sync.json or return defaults (enabled=False, type=mesh)
- [ ] T020 [P] [US9] Implement `_save_sync_config(config)` → write sync.json
- [ ] T021 [P] [US9] Implement `_is_sync_enabled()` → check config.enabled
- [ ] T022 [P] [US9] Implement `_get_net_syncer()` → lazy-load and cache `HK_NetSyncer*`
- [ ] T023 [P] [US9] Implement `_free_net_syncer()` → free syncer handle

---

## Phase 3: US9 - Sync Enable/Disable/Status

- [ ] T024 [US9] Implement `_cmd_sync_enable(args)` — parse args, create config, start net syncer, save config
- [ ] T025 [US9] Implement `_cmd_sync_disable(args)` — stop syncer, update config, free handle
- [ ] T026 [US9] Implement `_cmd_sync_status(args)` — read config + syncer status, return peer info
- [ ] T027 [US9] Implement `cmd_sync(args)` dispatcher for enable/disable/status/sync-now/backup
- [ ] T028 [US9] Add `sync` to main command dispatch dictionary
- [ ] T029 [US9] Update module docstring with sync commands
- [ ] T030 [US9] Add test: sync defaults to off at startup
- [ ] T031 [US9] Add test: sync enable mesh with room key succeeds
- [ ] T032 [US9] Add test: sync enable cloud with server+token succeeds
- [ ] T033 [US9] Add test: sync status returns config and peer info
- [ ] T034 [US9] Add test: sync disable stops sync
- [ ] T035 [US9] Add test: invalid type (not mesh/cloud) rejected

---

## Phase 4: US10 - Sync Collections & Local-Only

- [ ] T036 [US10] Implement `_sync_set_replication_collections(collections)` — call `hk_config_set_replication_collections`
- [ ] T037 [US10] Implement `_sync_set_local_only(collections)` — call `hk_engine_set_collection_local` for each
- [ ] T038 [US10] Implement `_sync_rejoin_collection(collection)` — call `hk_engine_replicate_collection`
- [ ] T039 [US10] Add `--collections` and `--local-only` parsing to `sync enable`
- [ ] T040 [US10] Add test: local-only collection does not replicate
- [ ] T041 [US10] Add test: replication collections filter works
- [ ] T042 [US10] Add test: rejoin collection restores replication

---

## Phase 5: US11 - Sync-Now, Backup, Watch, Versioned Reads

- [ ] T043 [US11] Implement `_cmd_sync_sync_now(args)` — trigger catch-up sync, return changes synced count
- [ ] T044 [US11] Implement `_cmd_sync_backup(args)` — call `hk_engine_backup`, return backup path
- [ ] T045 [US11] Implement `_watch_collection(collection, callback)` — register `hk_engine_watch` callback
- [ ] T046 [US11] Implement `_get_versioned_doc(collection, doc_id)` — call `hk_engine_get_versioned`, return doc + version
- [ ] T047 [US11] Add test: sync-now returns changes synced count
- [ ] T048 [US11] Add test: backup creates file at specified path
- [ ] T049 [US11] Add test: versioned read returns doc and version
- [ ] T050 [US11] Add test: watch callback fires on document change

---

## Phase 6: Remove Git-Based Team Sync

- [ ] T051 [US11] Remove `sync` subcommand from `cmd_team`
- [ ] T052 [US11] Remove `git pull --no-rebase` logic from team sync
- [ ] T053 [US11] Update `cmd_team` usage message (remove sync from list)
- [ ] T054 [US11] Update `team status` to not reference sync remote
- [ ] T055 [US11] Update AGENTS.md — remove git sync references, add sync commands
- [ ] T056 [US11] Update module docstring — remove `team sync`, add `sync` commands
- [ ] T057 [US11] Add test: `hakoagent team sync` returns deprecation/error message

---

## Phase 7: Polish

- [ ] T058 [US9-US11] Run full test suite: 75+ tests passing
- [ ] T059 [US9-US11] Run `hakoagent bug_scan` on new sync code
- [ ] T060 [US9-US11] Run `hakoagent vigilance` — constitution check pass
- [ ] T061 [US9-US11] Verify no Git push/pull logic remains in sync path
- [ ] T062 [US9-US11] Reinstall globally via `./install.sh --global`
- [ ] T063 [US9-US11] End-to-end validation: enable mesh sync on two processes, write data on one, read on other

---

**Design artifacts ready**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/hakodb-sync-interface.md`, `quickstart.md`

Plan workflow complete. Ready to proceed to `/speckit-implement`.
