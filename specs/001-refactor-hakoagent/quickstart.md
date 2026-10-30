# Quickstart Validation Guide — HakoAgent

**Feature**: 001-refactor-hakoagent  
**Date**: 2026-10-29  
**Status**: Draft

## Purpose

End-to-end validation documentation proving the HakoAgent feature works according to the specification and the constitution. This guide contains runnable scenarios, not full implementation code.

## Prerequisites

- Rust toolchain installed (cargo, rustc)
- Write permission in the project working directory
- HakoDB 0.19 available as a dependency

## Setup Commands

```bash
# 1. Build HakoAgent core and CLI
cargo build --release --manifest-path cli/Cargo.toml

# 2. Initialize the HakoDB database and all collections
./cli/target/release/hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

Expected output:
```
Speckit database initialized at: ./.hakoagent/hakoagent.db
Collections: ["sessions", "events", "decisions", "findings", "code_index", "tasks", "context_cache", "skills", "lessons_learned"]
```

## Test/Run Commands

### Test 1: Initialize the database (FR-002, FR-003)

```bash
./cli/target/release/hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

**Expected**: All 9 collections are created at `.hakoagent/hakoagent.db`:
- sessions, events, decisions, findings, code_index, tasks, context_cache, skills, lessons_learned

### Test 2: Record an append-only event (FR-004)

```bash
./cli/target/release/hakoagent events
```

**Expected**: Display the event history (empty on first initialization). Each new event is appended with a timestamp and cannot be overwritten.

### Test 3: Retrieve context from memory (FR-007)

```bash
./cli/target/release/hakoagent recall "bagaimana implementasi error handling Rust?"
```

**Expected**: Returns relevant context from `code_index` via HNSW + FTS within the target time (< X seconds).

### Test 4: Manage skills in Markdown format (FR-005)

```bash
./cli/target/release/hakoagent skill list
./cli/target/release/hakoagent skill add "rust_error_handling"
```

**Expected**: A new skill is created as a Markdown file under `.hakoagent/skills/`, not YAML or JSON.

### Test 5: Create and complete a task with DoD (FR-006)

```bash
./cli/target/release/hakoagent task list
./cli/target/release/hakoagent task create "Implement error handling"
./cli/target/release/hakoagent task complete <task_id>
```

**Expected**: The task is created with a target and definition_of_done. After completion, the status changes to "done" and `dod_verified` = true.

### Test 6: Detect regressions and overlooked files (FR-008)

```bash
./cli/target/release/hakoagent vigilance
```

**Expected**: The report contains files changed but not tested, untouched TODOs, and regression checks against constitution principles.

## Expected Outcomes (Success Criteria)

| SC | Target | Expected Result |
|----|--------|----------------------|
| SC-001 | Full task cycle < 30 seconds | `init → recall → event_log → task_create → skill_add → task_complete` finishes within the target time |
| SC-002 | 100% of completed tasks have a DoD | Every task marked "done" has `dod_verified` = true |
| SC-003 | 0 references to "hakoagent" | No occurrence of "hakoagent" in any source file, documentation, or configuration |
| SC-004 | 100% of skills as Markdown | All files under `.hakoagent/skills/` have the `.md` extension |
| SC-005 | Events cannot be overwritten | Every event has an ISO 8601 timestamp and cannot be overwritten |
| SC-006 | Tool calling easy to discover | All `hakoagent.<command>` tools can be invoked without complex configuration |

## Validation Steps

1. Run all the Setup commands above
2. Run Test 1 through Test 6 in order
3. Verify the Expected Outcomes against the table above
4. If everything passes, the feature is considered ready for the next implementation phase

## References

- Feature specification: `spec.md`
- Data model: `data-model.md`
- Interface contract: `contracts/tool-calling-interface.md`
- Constitution: `.specify/memory/constitution.md`
