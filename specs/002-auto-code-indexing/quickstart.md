# Quickstart Validation Guide — Auto Codebase Indexing

**Feature**: 002-auto-code-indexing  
**Date**: 2026-10-29  
**Status**: Draft

## Purpose

End-to-end validation documentation proving the auto codebase indexing feature works according to the specification and the HakoAgent constitution. This guide contains runnable scenarios, not full implementation code.

## Prerequisites

- Rust toolchain installed (cargo, rustc)
- Write permission in the project working directory
- HakoDB 0.19 available as a dependency
- HakoAgent already built

## Setup Commands

```bash
# 1. Build HakoAgent core and CLI
cargo build --release --manifest-path cli/Cargo.toml

# 2. Initialize the HakoDB database and all collections
./cli/target/release/hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

Expected output:
```
HakoAgent database initialized at: ./.hakoagent/hakoagent.db
Collections: ["sessions", "events", "decisions", "findings", "code_index", "tasks", "context_cache", "skills", "lessons_learned"]
```

The background thread auto indexing will automatically scan the codebase after initialization.

## Test/Run Commands

### Test 1: Startup auto indexing (FR-001)

```bash
# Ensure the database is initialized
./cli/target/release/hakoagent init --db ./.hakoagent/hakoagent.db --collections all

# Create a new source code file
echo "fn hello() { println!(\"hello\"); }" > src/hello.rs

# Wait for the background thread to detect and index
# Verify with recall
./cli/target/release/hakoagent recall "hello"
```

**Expected**: The file `hello.rs` is automatically indexed into code_index without the agent calling `hakoagent index`. The recall results show symbols from that file.

### Test 2: Incremental indexing (FR-002, SC-002)

```bash
# Change an already-indexed file
echo "fn hello() { println!(\"hello world\"); }" > src/hello.rs

# Wait for the background thread to detect the change
# Verify code_index is updated
./cli/target/release/hakoagent recall "hello world"
```

**Expected**: The recall results show the updated content. Indexing one file takes < 5 seconds.

### Test 3: File deleted (FR-006, SC-004)

```bash
# Delete the file
rm src/hello.rs

# Wait for the background thread to detect the deletion
# Verify the code_index entry is removed
./cli/target/release/hakoagent recall "hello"
```

**Expected**: The recall results no longer show symbols from `hello.rs` because the file was deleted.

### Test 4: Indexing notification (FR-005, SC-005)

```bash
# Create several new files
echo "fn foo() {}" > src/foo.rs
echo "fn bar() {}" > src/bar.rs

# Wait for the background thread to finish indexing
# Check notifications/events
./cli/target/release/hakoagent events
```

**Expected**: The agent receives a concise notification about the number of files indexed and the success/error status.

### Test 5: Directory ignored (FR-004)

```bash
# Create a directory that must be ignored
mkdir -p target/debug
echo "fn ignored() {}" > target/debug/ignored.rs

# Verify files under target/ are not indexed
./cli/target/release/hakoagent recall "ignored"
```

**Expected**: Files under `target/` do not appear in the recall results.

## Expected Outcomes (Success Criteria)

| SC | Target | Expected Result |
|----|--------|----------------------|
| SC-001 | No manual `hakoagent index` needed | Background thread indexes automatically at startup and on changes |
| SC-002 | Incremental indexing < 5 seconds/file | A single changed file is indexed in < 5 seconds |
| SC-003 | 100% of source files indexed | All .rs, .py, .js, .ts, .go files are in code_index |
| SC-004 | 0 entries for deleted files | Deleted files no longer appear in code_index |
| SC-005 | Notification after indexing | Events show the completed indexing status |
| SC-006 | 0 hakoagent references | No occurrence of "hakoagent" in source/documentation |

## Validation Steps

1. Run all the Setup commands above
2. Run Test 1 through Test 5 in order
3. Verify the Expected Outcomes against the table above
4. If everything passes, the auto codebase indexing feature is considered ready

## References

- Feature specification: `spec.md`
- Data model: `data-model.md`
- Interface contract: `contracts/auto-indexing-interface.md`
- Constitution: `.specify/memory/constitution.md`
