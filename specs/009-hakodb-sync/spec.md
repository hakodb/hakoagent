# Feature Specification: Hakodb Sync (Optional, Mesh Default)

**Feature Branch**: `009-hakodb-sync`

**Created**: 2026-10-29

**Status**: Draft

**Input**: Requirement to add optional hakodb-based synchronization to hakoagent, replacing the existing git-based `team sync` push/pull logic. Sync is user-triggered, optional, mesh-type by default, with optional cloud_sync support.

**Reference**: `lib/hakodb.h` (v0.20.0) — contains `hk_net_syncer_*`, `hk_config_set_replication_collections`, `hk_config_set_sync_excluded`, `hk_engine_set_collection_local`, `hk_engine_replicate_collection`, `hk_engine_get_versioned`, `hk_engine_watch`, `hk_engine_backup`, etc.

---

## User Scenarios & Testing *(mandatory)*

### User Story 9 - Agent enables optional mesh sync to share context across machines (Priority: P1)

A harness agent running on Machine A wants to share its memory/context/history with Agent B on Machine B. Both agents use the same hakodb `.db` file conceptually (via sync), so changes made by Agent A appear on Agent B and vice versa.

Sync is **optional** and **off by default**. The agent enables it explicitly via CLI command. Default sync type is **mesh** (peer-to-peer via mDNS/UDP broadcast). Cloud sync is optional with server URL + API token.

**Independent Test**: Agent A enables mesh sync with a room key, makes a document change, Agent B runs sync status and sees the change replicated.

**Acceptance Scenarios**:

1. **Given** sync is off by default, **When** agent checks sync status, **Then** sync is reported as disabled/inactive
2. **Given** agent enables mesh sync with room key, **Then** net syncer starts and sync status shows active mesh mode
3. **Given** two agents share the same room key, **When** agent-A writes a document, **Then** agent-B can retrieve it after sync
4. **Given** agent enables cloud_sync with server URL + API token, **Then** sync uses cloud mode instead of mesh

---

### User Story 10 - Agent manages sync collections and local-only exclusions (Priority: P1)

A harness agent controls which collections participate in sync. Some collections (e.g., sensitive decisions) should be local-only and never replicate.

**Independent Test**: Agent marks `decisions` as local-only, writes a decision, verifies it does not replicate to peer.

**Acceptance Scenarios**:

1. **Given** agent marks collection as local-only, **When** sync runs, **Then** that collection's documents are not transmitted
2. **Given** agent rejoins a collection to replication, **When** sync runs, **Then** that collection's documents replicate again

---

### User Story 11 - Agent replaces git-based team sync with hakodb sync (Priority: P1)

The existing `hakoagent team sync` command uses `git pull --no-rebase` which is inappropriate for a binary `.db` file and doesn't push changes. This is replaced with hakodb-native sync commands.

**Independent Test**: Agent runs `hakoagent sync enable --type mesh --room-key <key>` instead of `git pull`-based sync.

**Acceptance Scenarios**:

1. **Given** agent runs `hakoagent team sync`, **Then** command is removed or deprecated with message to use `hakoagent sync` instead
2. **Given** agent enables sync, writes data, disables sync, **Then** sync stops and no new changes replicate

---

## Edge Cases

- **Same doc edited on two machines**: Versioned read (`hk_engine_get_versioned`) detects conflict; last-write-wins with version clock. No automatic merge.
- **Peer goes offline**: Sync queue holds changes; when peer returns, catch-up sync transmits pending changes.
- **Different room keys**: Agents with different room keys do not sync with each other.
- **Cloud vs mesh mismatch**: One agent on mesh, one on cloud — they do not sync (different sync planes).
- **Large binary .db file**: Git-based sync was inappropriate; hakodb sync handles binary database changes at record level.
- **Sync disabled but data exists locally**: Local data remains intact; sync just stops new changes from propagating.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-033**: System MUST provide `hakoagent sync enable --type <mesh|cloud> [--room-key <key>] [--port <port>] [--server <url>] [--token <token>] [--collections <list>] [--local-only <list>]` command
- **FR-034**: System MUST provide `hakoagent sync disable` command to stop sync
- **FR-035**: System MUST provide `hakoagent sync status` command to show sync mode, active peers, replicated collections, pending changes
- **FR-036**: System MUST provide `hakoagent sync sync-now` command to manually trigger catch-up sync
- **FR-037**: System MUST default sync to **off** (disabled) at startup
- **FR-038**: System MUST default sync type to **mesh** when enabled without `--type`
- **FR-039**: System MUST support mesh sync via mDNS/UDP broadcast discovery (hk_net_syncer_set_discovery)
- **FR-040**: System MUST support optional cloud sync with `--server` URL and `--token` API authentication (HK_CloudSync)
- **FR-041**: System MUST support `--room-key` for mesh sync peer grouping (agents with same room key sync together)
- **FR-042**: System MUST support `--collections` to specify which collections replicate (default: all)
- **FR-043**: System MUST support `--local-only` to exclude collections from sync (maps to hk_config_set_sync_excluded / hk_engine_set_collection_local)
- **FR-044**: System MUST remove `hakoagent team sync` git-based push/pull logic
- **FR-045**: System MUST use `hk_engine_get_versioned` for conflict detection on writes during sync
- **FR-046**: System MUST use `hk_engine_watch` to react to remote changes locally
- **FR-047**: System MUST provide `hakoagent sync backup <path>` to backup the synced database

### Key Entities

| Entity | Key Attributes | Relationships |
|--------|---------------|---------------|
| **SyncConfig** | `enabled`, `type` (mesh|cloud), `room_key`, `port`, `server_url`, `api_token`, `replication_collections[]`, `local_only_collections[]`, `started_at`, `actor` | — |
| **SyncPeer** | `peer_id`, `address`, `mode` (mesh|cloud), `last_seen`, `status` (connected|disconnected) | belongs to SyncConfig |
| **SyncChange** | `change_id`, `collection`, `doc_id`, `operation` (insert|update|delete|soft_delete), `version`, `timestamp`, `synced` (bool) | — |

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-025**: `hakoagent sync enable --type mesh --room-key <key>` starts sync successfully
- **SC-026**: `hakoagent sync status` shows sync mode, peers, and replicated collections
- **SC-027**: Document written on agent-A appears on agent-B after sync (same room key)
- **SC-028**: Local-only collection does not replicate to peers
- **SC-029**: Sync defaults to off at startup
- **SC-030**: `hakoagent team sync` is removed/deprecated
- **SC-031**: Cloud sync with `--server` and `--token` connects to cloud server
- **SC-032**: All existing 75 tests continue to pass
- **SC-033**: New tests for sync commands pass

---

## Assumptions

- Agents sharing context use the same `--room-key` (mesh) or same `--server` + `--token` (cloud)
- Each agent has its own local `.db` file; sync propagates record-level changes between them
- Sync is opt-in per agent process; not automatic
- Git-based `team sync` is removed entirely — no push/pull logic remains
- Cloud sync requires network access to the specified server URL
- Mesh sync uses local network discovery (mDNS/UDP broadcast), no central server needed

---
