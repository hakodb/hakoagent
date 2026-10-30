# Quickstart Validation Guide — HakoAgent Multi-Agent Context Sync

**Feature**: 006-multi-agent-context-sync  
**Date**: 2026-10-29  
**Status**: Draft

## Purpose

End-to-end validation that HakoAgent memory, context, and history system works with the real HakoDB shared library via Python ctypes FFI, and that multiple agents can share context through a common HakoDB instance.

## Prerequisites

- Python 3 (stdlib only, no external dependencies)
- Write permission in working directory
- Prebuilt HakoDB library at `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` + header `lib/hakodb.h`

## Setup Commands

```bash
# 1. Initialize database HakoDB and all collections
./hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

Expected output:
```
HakoAgent database initialized at: ./.hakoagent/hakoagent.db
Collections: ["sessions", "events", "decisions", "findings", "code_index", "tasks", "context_cache", "skills", "lessons_learned"]
```

## Test 1: Single-agent memory write + read via FFI (FR-001, FR-003, FR-004)

```bash
# Agent A writes an event
./hakoagent event_log "code_read" "src/main.py" "agent-a" "info" '{"file": "src/main.py"}'

# Verify event appears in events collection
./hakoagent events
```

**Expected**:
- Event created with unique `event_id` and ISO 8601 `timestamp`
- Event appears in `./hakoagent events` output
- `actor` field set to `agent-a`

## Test 2: Append-only guard (FR-003)

```bash
# Attempt to write same event_id twice — second write should be rejected
```

**Expected**: Second write with duplicate `event_id` is rejected (no overwrite)

## Test 3: Context retrieval via recall (FR-005, FR-006)

```bash
# Write a skill document
./hakoagent skill add "python-error-handling"

# First recall — cache miss, performs vector search
./hakoagent recall "python error handling" --limit 5

# Second identical query within TTL — cache hit
./hakoagent recall "python error handling" --limit 5

# Cache statistics
./hakoagent cache stats
```

**Expected**:
- First query returns relevant context (cache miss)
- Second query returns cache hit (no re-search)
- `cache stats` shows hits ≥ 1, misses ≥ 1

## Test 4: Multi-agent context sync (FR-007, FR-008)

```bash
# Agent-A writes a finding
./hakoagent event_log "finding" "buffer overflow in parser" "agent-a" "error" '{"severity": "high"}'

# Agent-B recalls — should see Agent-A's finding
./hakoagent recall "buffer overflow" --limit 5
```

**Expected**: Agent-B's recall returns Agent-A's finding with `actor: "agent-a"` attribution

## Test 5: Task management with DoD (FR-007)

```bash
# Create task
./hakoagent task create "Implement multi-agent sync" "Two agents can read same document" "Verify via recall from separate sessions" P1 "agent-a"

# List tasks
./hakoagent task list

# Complete task
./hakoagent task complete <task_id> true "agent-a"
```

**Expected**: Task created with target + DoD; completion sets `dod_verified=true` and `completed_at`

## Test 6: Full test suite

```bash
python3 test_hakoagent.py
```

**Expected**: 31+ tests passing

## Expected Outcomes (Success Criteria)

| SC | Target | Hasil yang Diharapkan |
|----|--------|----------------------|
| SC-001 | Single-agent write/read < 1s | `event_log` + `recall` completes in < 1 second |
| SC-002 | Multi-agent document sharing | Agent-A writes, Agent-B reads same doc |
| SC-003 | Append-only guard | 0 events overwritten on duplicate `event_id` |
| SC-004 | Cache hit ratio ≥ 50% | Repeated queries served from cache |
| SC-005 | Tests passing | 31+ tests in `test_hakoagent.py` pass |
| SC-006 | No Rust references | 0 references to Rust/Cargo/build in code/docs |
| SC-007 | File location | All files under `.hakoagent/` or project root |

## References

- Spesifikasi fitur: `spec.md`
- Rencana implementasi: `plan.md`
- Kontrak antarmuka: `contracts/multi-agent-context-interface.md`
- Konstitusi: `.specify/memory/constitution.md`
