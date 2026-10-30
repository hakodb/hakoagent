# Interface Contract — Hakodb Sync (US9-US11)

**Feature**: 009-hakodb-sync  
**Date**: 2026-10-29  
**Status**: Draft

All tool returns are in JSON format for harness agent parsing.

---

## 1. `hakoagent sync enable`

Enable hakodb synchronization (mesh or cloud).

**Usage**: `hakoagent sync enable --type <mesh|cloud> [--room-key <key>] [--port <port>] [--server <url>] [--token <token>] [--collections <c1,c2,...>] [--local-only <c1,c2,...>]`

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `--type` | string | Yes | — | `mesh` or `cloud` |
| `--room-key` | string | No (mesh: required) | — | Peer grouping key for mesh sync |
| `--port` | int | No | 9876 | Port for net syncer |
| `--server` | string | No (cloud: required) | — | Cloud sync server URL |
| `--token` | string | No (cloud: required) | — | Cloud API authentication token |
| `--collections` | string | No | all | Comma-separated collection names to replicate |
| `--local-only` | string | No | — | Comma-separated collection names to exclude from sync |

**Returns**:
```json
{
  "enabled": true,
  "type": "mesh",
  "room_key": "my-room-key",
  "port": 9876,
  "server_url": null,
  "api_token": null,
  "replication_collections": ["all"],
  "local_only_collections": [],
  "started_at": "2026-10-29T12:00:00Z",
  "actor": "agent-a",
  "syncer_status": "started",
  "message": "Sync enabled in mesh mode with room key 'my-room-key'"
}
```

---

## 2. `hakoagent sync disable`

Disable synchronization and stop the net syncer.

**Usage**: `hakoagent sync disable`

**Returns**:
```json
{
  "enabled": false,
  "type": null,
  "disabled_at": "2026-10-29T12:05:00Z",
  "message": "Sync disabled"
}
```

---

## 3. `hakoagent sync status`

Show current sync configuration and peer status.

**Usage**: `hakoagent sync status [--tier scout|verify|auditor]`

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `--tier` | string | No | verify | Evidence tier depth |

**Returns**:
```json
{
  "enabled": true,
  "type": "mesh",
  "room_key": "my-room-key",
  "port": 9876,
  "replication_collections": ["sessions", "events", "decisions", "findings", "code_index", "code_edges", "tasks", "context_cache", "skills", "lessons_learned", "revisions"],
  "local_only_collections": [],
  "peers": [
    {
      "peer_id": "peer-abc123",
      "address": "192.168.1.50:9876",
      "mode": "mesh",
      "last_seen": "2026-10-29T12:03:00Z",
      "status": "connected"
    }
  ],
  "pending_changes": 0,
  "tier": "verify"
}
```

---

## 4. `hakoagent sync sync-now`

Manually trigger catch-up sync with peers.

**Usage**: `hakoagent sync sync-now`

**Returns**:
```json
{
  "changes_synced": 5,
  "peers_contacted": 1,
  "sync_duration_ms": 230,
  "errors": []
}
```

---

## 5. `hakoagent sync backup`

Backup the synced database to a file.

**Usage**: `hakoagent sync backup <path>`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| path | string | Yes | Backup file path |

**Returns**:
```json
{
  "backup_path": "./backup.db",
  "status": "success",
  "backup_size_bytes": 1048576,
  "collections_backed_up": 11
}
```

---

## 6. Removed Command

**`hakoagent team sync`** — The git-based `git pull --no-rebase` sync is removed. Use `hakoagent sync enable/disable/status/sync-now` instead.

---

## 7. Hakodb FFI Functions Used

| Function | Purpose |
|----------|---------|
| `hk_net_syncer_new(engine, name, room_key)` | Create net syncer |
| `hk_net_syncer_set_discovery(syncer, mode)` | Set discovery mode (0=mDNS, 1=UDP, 2=both) |
| `hk_net_syncer_start(syncer, port)` | Start syncer listening |
| `hk_net_syncer_status(syncer)` | Get syncer status JSON |
| `hk_config_set_replication_collections(config, collections_json)` | Configure replication opt-in |
| `hk_config_set_sync_excluded(config, collections_json)` | Configure excluded collections |
| `hk_engine_set_collection_local(engine, collection, local)` | Mark collection local-only |
| `hk_engine_replicate_collection(engine, collection)` | Rejoin collection to replication |
| `hk_engine_get_versioned(engine, collection, doc_id, out_version)` | Versioned read for conflict detection |
| `hk_engine_watch(engine, collection, callback, user_data)` | Watch for remote changes |
| `hk_engine_backup(engine, path)` | Backup database |
| `hk_config_new()` / `hk_config_free(config)` | Config lifecycle |

**NOT used**: `hk_net_syncer_*` socket_sync, `HK_CloudSync` (cloud functions not yet verified in .so — will be added if available), `hk_engine_delete_local` (covered by `hk_engine_set_collection_local`).

---
