# Implementation Plan: Auto Codebase Indexing

**Branch**: `002-auto-code-indexing` | **Date**: 2026-10-29 | **Spec**: `specs/002-auto-code-indexing/spec.md`

**Input**: Feature specification from `/specs/002-auto-code-indexing/spec.md`

## Summary

Auto Codebase Indexing is a feature that lets HakoAgent automatically scan and index the codebase without the agent calling `hakoagent index` manually. At session startup, codebase scanning runs as a background thread within the same agent process. If the database does not exist yet, a full scan is performed; if it does exist, it is verified and only changed files are updated. Indexing results are stored in the `code_index` collection in HakoDB. The feature supports incremental indexing, detection of new/deleted/changed files, and completion notification to the agent.

## Technical Context

**Language/Version**: Rust 1.75+ (core), Python 3.11+ (integration example)

**Primary Dependencies**: hakodb 0.19 (embedded core, `--no-default-features`), notify (file system watcher), walkdir (directory traversal), serde (JSON), chrono (timestamp), uuid (ID generation)

**Storage**: HakoDB embedded document database (`.hakoagent/hakoagent.db`), `code_index` collection for storing indexing results

**Testing**: `cargo test` (Rust core), integration tests for the indexing flow

**Target Platform**: Linux, macOS, Windows (cross-platform file system watcher)

**Project Type**: CLI tool + library (Rust crate) + FFI bindings

**Performance Goals**: Incremental indexing time for one file < 5 seconds (SC-002); startup scan finishes in reasonable time for small-to-medium codebases

**Constraints**: Background thread within the agent process (no separate process); embedded database (no server); frugal with context and endpoint requests; all files under `.hakoagent/` or the project root; no references to hakoagent

**Scale/Scope**: Single project per database; 9 HakoDB collections including `code_index`; source code files (.rs, .py, .js, .ts, .go, etc.)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Status | Notes |
|-------------------|--------|---------|
| Smart Memory | Met | Indexing results stored in `code_index` in HakoDB |
| Anti-Lupa | Met | code_index stays up-to-date automatically |
| Kronologi & Histori | Met | IndexingRun recorded as an append-only event |
| Consistency | Met | Standard output template for indexing notifications |
| Cross-Model Consistency | Met | Same indexing flow for all LLM models |
| Vigilance | Met | Detects files that changed, were deleted, or are new |
| Clear Target | Met | Every indexing task has a target and DoD |
| Codebase Fluency | Met | code_index stores symbols, files, dependencies |
| Context Frugality | Met | Incremental indexing reduces LLM endpoint load |
| Self Skill Improvement | Met | Successful indexing patterns can be extracted as skills |

No violations. Constitution check PASSED.

## Project Structure

### Documentation (this feature)

```text
specs/002-auto-code-indexing/
├── spec.md          # Feature specification (/hakoagent.specify output)
├── plan.md          # Technical plan (this file, /hakoagent.plan output)
├── research.md      # Phase 0 output (/hakoagent.plan command)
├── data-model.md    # Phase 1 output (/hakoagent.plan command)
├── quickstart.md    # Phase 1 output (/hakoagent.plan command)
├── contracts/       # Phase 1 output (/hakoagent.plan command)
└── tasks.md         # Phase 2 output (/hakoagent.tasks command - NOT created by /hakoagent.plan)
```

### Source Code (repository root)

```text
.hakoagent/                      # HakoAgent data directory
├── hakoagent.db                 # HakoDB database (single file)
├── skills/                      # Skill files in Markdown format
├── sessions/                    # Session exports (optional)
└── logs/                        # Operation logs (optional)

hakoagent-core/                    # Rust crate (HakoDB binding + core logic)
├── Cargo.toml
├── build.rs                     # cbindgen for hakodb.h generation
├── src/
│   ├── lib.rs                   # Crate entry point
│   ├── binding/                 # C ABI / FFI wrapper
│   ├── memory/                  # Memory Service (9 collections including code_index)
│   ├── indexer/                 # Codebase Indexer (EXISTING - extended for auto indexing)
│   │   ├── mod.rs
│   │   ├── scanner.rs           # Directory traversal
│   │   ├── watcher.rs           # watch_collection integration
│   │   └── auto_indexer.rs      # NEW: Background thread startup scanning + incremental
│   ├── retriever/               # Context Retriever (HNSW + FTS + summarizer + cache)
│   ├── planner/                 # Task Planner (target + DoD)
│   ├── skill_engine/            # Skill Engine (self-improvement)
│   └── vigilance/               # Vigilance Checker
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
├── examples/
│   └── python/
└── cli/                         # CLI entry point (hakoagent command)
    ├── Cargo.toml
    └── src/
        └── main.rs
            └── commands/
                ├── init.rs
                ├── index.rs     # EXISTING - extended for auto indexing trigger
                ├── recall.rs
                ├── skill.rs
                ├── task.rs
                ├── events.rs
                └── vigilance.rs
```

**Structure Decision**: Single project structure (DEFAULT) — the `hakoagent-core` Rust crate as the core, the CLI as a separate crate. The auto indexer is added as a new module at `indexer/auto_indexer.rs` that uses a background thread for startup scanning and incremental updates.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations. This section is left empty.

---

## Phase 0: Outline & Research

### Unknowns from Technical Context

No NEEDS CLARIFICATION items remain. All parameters were determined through the spec and prior clarifications:

| Unknown | Status | Resolution |
|---------|--------|----------|
| Startup scanning mechanism | Resolved | Background thread within the agent process (Clarification Session 2026-10-29) |
| Database not present vs. present | Resolved | Full scan if absent, verify + update if present (FR-001) |

### Research Findings (research.md)

No research task is required because all unknowns have been resolved. `research.md` is recorded as "no unresolved clarifications".

**Output**: `research.md` noting that all NEEDS CLARIFICATION items were resolved previously.

---

## Phase 1: Design & Contracts

### Data Model (`data-model.md`)

Entities extracted from the feature spec:

| Entity | Key Attributes | Relationships |
|---------|--------------|----------|
| CodeIndexEntry | entry_id, file_path, symbol_name, symbol_type, dependencies, line_number, last_indexed_at, file_hash | — |
| FileChange | change_id, file_path, change_type (created/modified/deleted), timestamp, indexed_status | — |
| IndexingRun | run_id, started_at, ended_at, files_processed, files_indexed, errors, status | — |

State transitions:
- IndexingRun: started → completed / failed
- FileChange: detected → indexed / skipped / error
- CodeIndexEntry: created → updated / deleted

Validation rules:
- CodeIndexEntry: file_hash must be unique per file_path, last_indexed_at must be updated on change
- FileChange: change_type must be one of created/modified/deleted
- IndexingRun: files_processed must be >= files_indexed

### Interface Contracts (`contracts/`)

HakoAgent exposes a tool calling interface for auto indexing. The following contracts are defined:

**File**: `contracts/auto-indexing-interface.md`

| Tool | Parameters | Return |
|------|-----------|--------|
| `hakoagent.index` | — | indexing_run_id, status |
| `hakoagent.recall` | query, limit | context_results |
| `hakoagent.events` | limit, session_id | events_list (including indexing events) |

Auto indexing runs as a background thread and requires no additional CLI command. The `hakoagent index` CLI can be invoked manually to force a re-index.

Return values are always in JSON format for easy parsing by the harness agent.

### Quickstart Validation Guide (`quickstart.md`)

**Prerequisites**:
- Rust toolchain installed
- Write permission in the project working directory
- HakoDB database initialized (`hakoagent init`)

**Setup commands**:
```bash
# Build HakoAgent
cargo build --release --manifest-path cli/Cargo.toml

# Initialize the database
./cli/target/release/hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

**Test/run commands**:
```bash
# Test auto indexing at startup
./cli/target/release/hakoagent init --db ./.hakoagent/hakoagent.db --collections all
# The background thread will automatically scan the codebase

# Test incremental indexing
# Change one source code file, then wait for the indexing notification

# Test recall
./cli/target/release/hakoagent recall "fungsi error handling"
```

**Expected outcomes**:
- `init`: Background thread starts codebase scanning automatically
- New file: Automatically added to `code_index`
- File changed: `code_index` entry updated
- File deleted: `code_index` entry removed
- Notification: Agent receives an indexing summary after completion

### Re-evaluate Constitution Check (post-design)

| Constitution Principle | Post-Design Status | Notes |
|-------------------|-------------------|---------|
| Smart Memory | Met | Indexing results stored in `code_index` |
| Anti-Lupa | Met | code_index always up-to-date automatically |
| Kronologi & Histori | Met | IndexingRun as an append-only event |
| Consistency | Met | Standard indexing notification |
| Cross-Model Consistency | Met | Same indexing flow for all LLMs |
| Vigilance | Met | Automatic file change detection |
| Clear Target | Met | Every indexing run has a target and DoD |
| Codebase Fluency | Met | code_index stores code structure |
| Context Frugality | Met | Incremental indexing reduces endpoint load |
| Self Skill Improvement | Met | Indexing patterns can be extracted as skills |

No violations. Constitution check PASSED post-design.

---

**Design artifacts ready: `research.md`, `data-model.md`, `contracts/auto-indexing-interface.md`, `quickstart.md`**

Plan workflow complete. Ready to proceed to `/hakoagent-tasks`.
