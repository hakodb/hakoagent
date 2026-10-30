# Quickstart Validation Guide — HakoAgent Memory, Context & History System (Non-MCP, Embedded Hakodb)

**Feature**: 007-hakodb-memory-context-history  
**Date**: 2026-10-29  
**Status**: Draft

## Purpose

End-to-end validation that HakoAgent memory, context, and history system works with the embedded hakodb shared library via Python ctypes FFI, without MCP, and that context efficiency reduces LLM endpoint calls to save LLM model costs while boosting agent effectiveness.

Patterns validated: graph trace (inbound/outbound/both), shortest-path, impact analysis, index coverage, immutable revisions, context cache efficiency, multi-agent sync via shared filesystem.

## Prerequisites

- Python 3 (stdlib only, no external dependencies)
- Write permission in working directory
- Prebuilt hakodb library at `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` + header `lib/hakodb.h`

## Setup Commands

```bash
# 1. Initialize database hakodb and all collections
./hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

Expected output:
```
HakoAgent database initialized at: ./.hakoagent/hakoagent.db
Collections: ["sessions", "events", "decisions", "findings", "code_index", "tasks", "context_cache", "skills", "lessons_learned", "revisions", "softdel"]
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

## Test 3: Context efficiency — reduce LLM endpoint calls (FR-005, FR-006, FR-012)

```bash
# Write a skill document
./hakoagent skill add "python-error-handling"

# First recall — cache miss, performs vector search (LLM call would be made)
./hakoagent recall "python error handling" --limit 5

# Second identical query within TTL — cache hit (NO LLM call, cost saved)
./hakoagent recall "python error handling" --limit 5

# Cache statistics — should show hits >= 1, llm_calls_saved >= 1
./hakoagent cache stats
```

**Expected**:
- First query returns relevant context (cache miss)
- Second query returns cache hit (no re-search, no LLM call)
- `cache stats` shows hits ≥ 1, misses ≥ 1, llm_calls_saved ≥ 1

## Test 4: Multi-agent context sync (non-MCP) (FR-007, FR-008)

```bash
# Agent-A writes a finding
./hakoagent event_log "finding" "buffer overflow in parser" "agent-a" "error" '{"severity": "high"}'

# Agent-B recalls — should see Agent-A's finding
./hakoagent recall "buffer overflow" --limit 5
```

**Expected**: Agent-B's recall returns Agent-A's finding with `actor: "agent-a"` attribution

## Test 5: Graph trace (adapted from MCP trace_path) (FR-015)

```bash
# Index codebase first
./hakoagent index

# Trace outbound (what does func_a depend on?)
./hakoagent graph trace func_a out 3

# Trace inbound (who depends on func_a?)
./hakoagent graph trace func_a in 2

# Trace both directions
./hakoagent graph trace func_a both 3
```

**Expected**:
- Outbound: all nodes reachable via outgoing dependency edges
- Inbound: all nodes that depend on func_a
- Both: combined neighborhood

## Test 6: Shortest path (adapted from MCP query_graph) (FR-016)

```bash
# Find shortest dependency chain between two symbols
./hakoagent graph shortest-path func_a func_c
```

**Expected**: Shortest dependency chain from func_a to func_c

## Test 7: Impact analysis (blast radius) (FR-017)

```bash
# What breaks if src/main.py changes?
./hakoagent impact src/main.py
```

**Expected**: All transitive dependents (blast radius) of src/main.py

## Test 8: Index coverage (adapted from MCP check_index_coverage) (FR-018)

```bash
# Check coverage of specific files
./hakoagent graph coverage src/main.py src/utils.py src/legacy.py
```

**Expected**: Per-file coverage status; files with gaps indicate source_fallback needed

## Test 9: Task management with DoD (FR-007)

```bash
# Create task
./hakoagent task create "Implement memory system" "Embedded hakodb memory works" "All tests pass" P1 "agent-a"

# List tasks
./hakoagent task list

# Complete task
./hakoagent task complete <task_id> true "agent-a"
```

**Expected**: Task created with target + DoD; completion sets `dod_verified=true` and `completed_at`

## Test 10: Immutable revisions (history) (FR-014)

```bash
# Create a document
./hakoagent event_log "finding" "initial finding" "agent-a" "info" '{"id": "f1"}'

# Update — previous version preserved as revision
./hakoagent event_log "finding" "updated finding" "agent-a" "info" '{"id": "f1", "rev": 2}'

# List revisions — both versions preserved immutably
./hakoagent revision.list f1 findings
```

**Expected**: Both revisions listed chronologically; neither can be overwritten

## Test 12: Bug fixing loop — finding → task → fix → skill (FR-007, US7)

```bash
# Agent logs a bug finding
./hakoagent event_log "finding" "null pointer in parser" "agent-a" "error" '{"finding_type": "bug", "severity": "high", "file": "src/parser.py"}'

# Create fix task with target + DoD
./hakoagent task create "Fix null pointer in parser" "Add null check before accessing parser result" "Unit test covers null case, revision saved" P1 "agent-a"

# Complete the fix task
./hakoagent task complete <task_id> true "agent-a"

# Verify immutable revision of the fixed document
./hakoagent revision.list src/parser.py findings

# Extract bug-fix skill
./hakoagent skill add "null-check-before-parser-access"
```

**Expected**:
- Finding logged with type: bug
- Task created with target + DoD
- Task completed with dod_verified=true
- Revision saved immutably
- New skill created (extracted bug pattern)

## Test 13: Full test suite

```bash
python3 test_hakoagent.py
```

**Expected**: 31+ tests passing

## Expected Outcomes (Success Criteria)

| SC | Target | Expected Result |
|----|--------|-----------------|
| SC-001 | Single-agent write/read < 1s | `event_log` + `recall` completes in < 1 second |
| SC-002 | Multi-agent document sharing | Agent-A writes, Agent-B reads same doc |
| SC-003 | Append-only guard | 0 events overwritten on duplicate `event_id` |
| SC-004 | Cache hit ratio ≥ 50% | Repeated queries served from cache |
| SC-005 | LLM calls reduced by ≥ N% | `cache stats` shows llm_calls_saved > 0 |
| SC-006 | Tests passing | 31+ tests in `test_hakoagent.py` pass |
| SC-007 | No MCP/Rust references | 0 references to MCP/Rust/Cargo/build in code/docs |
| SC-008 | File location | All files under `.hakoagent/` or project root |
| SC-009 | Immutable revisions | 0 revisions overwritten or deleted |
| SC-010 | Graph trace | Correct nodes for inbound/outbound/both |
| SC-011 | Shortest path | Correct dependency chain |
| SC-012 | Index coverage | Coverage gaps reported with source fallback |
| SC-013 | Bug fixing loop | Finding → task → fix → revision → skill → lessons_learned works end-to-end |

## References

- Spesifikasi fitur: `spec.md`
- Rencana implementasi: `plan.md`
- Kontrak antarmuka: `contracts/hakodb-memory-context-interface.md`
- Konstitusi: `.specify/memory/constitution.md`
- Referensi pola MCP: `/home/web/.claude/skills/codebase-memory/SKILL.md` (codebase-memory knowledge graph MCP, adapted to non-MCP embedded hakodb)
