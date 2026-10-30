# Quickstart — Hakodb Sync (US9-US11)

**Feature**: 009-hakodb-sync  
**Date**: 2026-10-29  
**Status**: Draft

## Prerequisites

- Python 3 (stdlib only, no external dependencies)
- Prebuilt hakodb library at `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so`
- Write permission in working directory
- Two or more machines/processes for multi-agent sync testing

## Setup

```bash
# Initialize database with all collections
./hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

## Validation Scenarios

### 1. Verify sync is off by default

```bash
./hakoagent sync status
```

**Expected**: `enabled: false`, no peers, sync type null

### 2. Enable mesh sync (Agent A)

```bash
./hakoagent sync enable --type mesh --room-key my-room-key --port 9876
```

**Expected**: Sync enabled, type=mesh, room_key=my-room-key, port=9876, syncer started

### 3. Enable mesh sync (Agent B — same room key)

```bash
./hakoagent sync enable --type mesh --room-key my-room-key --port 9877
```

**Expected**: Sync enabled, peers discovered via mDNS/UDP

### 4. Write data on Agent A, verify on Agent B

```bash
# Agent A writes a document
./hakoagent save_doc findings finding_1 '{"content": "shared finding", "actor": "agent-a", "finding_type": "bug"}'

# Agent B checks sync status
./hakoagent sync status

# Expected: peers connected, pending_changes may show pending replication

# Agent B triggers manual sync
./hakoagent sync sync-now

# Agent B reads the document
./hakoagent load_doc findings finding_1
```

**Expected**: Agent B can read the document written by Agent A

### 5. Enable cloud sync (optional)

```bash
./hakoagent sync enable --type cloud --server https://sync.example.com --token <api-token> --room-key my-room-key
```

**Expected**: Sync enabled, type=cloud, server_url and api_token set

### 6. Mark collection as local-only

```bash
./hakoagent sync enable --type mesh --room-key my-room-key --local-only decisions

# Write to decisions — should NOT replicate
./hakoagent save_doc decisions decision_1 '{"title": "local decision", "actor": "agent-a"}'

# On peer, decision_1 should NOT appear
```

**Expected**: Local-only collection documents do not replicate

### 7. Check sync status

```bash
./hakoagent sync status --tier auditor
```

**Expected**: Detailed peer list, pending changes, per-collection sync status

### 8. Manual sync trigger

```bash
./hakoagent sync sync-now
```

**Expected**: Changes synced count, peers contacted

### 9. Backup database

```bash
./hakoagent sync backup ./backup.db
```

**Expected**: Backup file created, status success

### 10. Disable sync

```bash
./hakoagent sync disable
```

**Expected**: Sync disabled, no new changes replicate

### 11. Verify `team sync` is removed

```bash
./hakoagent team sync
```

**Expected**: Command not found or deprecated message pointing to `hakoagent sync`

### 12. Full test suite

```bash
python3 test_hakoagent.py
```

**Expected**: 75+ tests passing (including new sync tests)

---
