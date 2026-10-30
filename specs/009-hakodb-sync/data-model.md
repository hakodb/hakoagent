# Data Model — Hakodb Sync (US9-US11)

**Feature**: 009-hakodb-sync  
**Date**: 2026-10-29  
**Status**: Draft

## Entities

### SyncConfig

| Attribute | Type | Description |
|-----------|------|-------------|
| `enabled` | bool | Sync is active or not (default: false) |
| `type` | string | `mesh` (default) or `cloud` |
| `room_key` | string | Peer grouping key for mesh sync |
| `port` | int | Port for net syncer to listen on |
| `server_url` | string\|null | Cloud sync server URL (cloud type only) |
| `api_token` | string\|null | Cloud API authentication token (cloud type only) |
| `replication_collections` | list[str] | Collections to replicate (default: all) |
| `local_only_collections` | list[str] | Collections excluded from sync |
| `started_at` | string | ISO 8601 timestamp when sync was enabled |
| `actor` | string | Agent that enabled sync |

### SyncPeer

| Attribute | Type | Description |
|-----------|------|-------------|
| `peer_id` | string | Unique peer identifier |
| `address` | string | Network address (host:port or cloud URL) |
| `mode` | string | `mesh` or `cloud` |
| `last_seen` | string | ISO 8601 timestamp |
| `status` | string | `connected` or `disconnected` |

### SyncChange

| Attribute | Type | Description |
|-----------|------|-------------|
| `change_id` | string | Unique change identifier |
| `collection` | string | Collection name |
| `doc_id` | string | Document ID |
| `operation` | string | `insert`, `update`, `delete`, `soft_delete` |
| `version` | int | Document version at time of change |
| `timestamp` | string | ISO 8601 timestamp |
| `synced` | bool | Whether change has been synced to peers |

## Collections

No new hakodb collections are created. Sync configuration is stored as a JSON file:

```
.hakoagent/sync/sync.json
```

This file contains the `SyncConfig` serialized as JSON. It is read at startup and written when sync is enabled/disabled/configured.

## State Transitions

| Entity | Transitions |
|--------|-------------|
| SyncConfig | `disabled` → `enabled` (via `hakoagent sync enable`) → `disabled` (via `hakoagent sync disable`) |
| SyncPeer | `disconnected` → `connected` (peer discovered) → `disconnected` (peer lost) |

## Validation Rules

- **SyncConfig**: `room_key` is required for mesh type; `server_url` and `api_token` are required for cloud type
- **SyncConfig**: `type` must be `mesh` or `cloud`
- **SyncConfig**: `port` must be a valid TCP port (1-65535)
- **Collections**: `local_only_collections` and `replication_collections` should not overlap
- **Versioned read**: `hk_engine_get_versioned` used to detect conflicts when same doc edited on multiple peers

## Evidence Tiers for Sync

| Tier | Behavior |
|------|----------|
| Scout | Fast status check, provisional peer list |
| Verify | Full peer enumeration, pending change count |
| Auditor | Complete change listing, per-collection sync status, conflict details |
