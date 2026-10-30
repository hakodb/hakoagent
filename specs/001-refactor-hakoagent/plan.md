# Implementation Plan: Refactor HakoAgent to Constitution

**Branch**: `001-refactor-hakoagent` | **Date**: 2026-10-29 | **Spec**: `specs/001-refactor-hakoagent/spec.md`

**Input**: Feature specification from `/specs/001-refactor-hakoagent/spec.md`

## Summary

Refactor the hakoagent project to align with the latest constitution based on HakoDB. Main goals: build supporting tools for the harness agent that are smart, resistant to forgetting, consistent across LLM models, frugal, with clear targets, quick codebase comprehension, and economical with context/endpoint requests. The refactor covers 7 modules: HakoDB Binding Layer, Memory Service, Codebase Indexer, Context Retriever, Task Planner, Skill Engine, and Vigilance Checker. Skills are stored in Markdown format under `.hakoagent/skills/`, the HakoDB database lives at `.hakoagent/hakoagent.db`, and all related files stay within hakoagent scope (with no references to hakoagent).

## Technical Context

**Language/Version**: Rust 1.75+ (core), Python 3.11+ (harness integration example)

**Primary Dependencies**: hakodb 0.19 (embedded core, `--no-default-features`), cbindgen (C ABI generation), serde (JSON), chrono (timestamp), uuid (ID generation), lazy_static (append-only guard)

**Storage**: HakoDB embedded document database (single file, `.hakoagent/hakoagent.db`), WAL durability, tiered-segment storage

**Testing**: `cargo test` (Rust core), integration tests for CLI commands, unit tests for each module

**Target Platform**: Linux, macOS, Windows (shared library + CLI binary)

**Project Type**: CLI tool + library (Rust crate) + FFI bindings

**Performance Goals**: Full task cycle < 30 seconds; context retrieval time < X seconds; endpoint LLM call reduction ≥ N%

**Constraints**: Frugal with context and endpoint requests; embedded (no server/daemon); light footprint (`--no-default-features`); all files under `.hakoagent/` or the project root; skills in Markdown format; no references to hakoagent

**Scale/Scope**: Single project per database; 9 HakoDB collections; 7 implementation modules; 12 tool calling interfaces

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Status | Notes |
|-------------------|--------|---------|
| Smart Memory | Met | `sessions`, `decisions`, `findings`, `skills` collections |
| Anti-Lupa | Met | Query `findings` + `skills` before a new task |
| Kronologi & Histori | Met | Append-only event log in the `events` collection |
| Consistency | Met | Standard output template across models |
| Cross-Model Consistency | Met | Same task flow for all LLMs |
| Vigilance | Met | Vigilance Checker module |
| Clear Target | Met | Every task has a target + DoD |
| Codebase Fluency | Met | `code_index` collection + indexer |
| Context Frugality | Met | HNSW + FTS + `context_cache` + summaries |
| Self Skill Improvement | Met | `skills` + `lessons_learned` collections + Markdown |

No violations. Constitution check PASSED.

## Project Structure

### Documentation (this feature)

```text
specs/001-refactor-hakoagent/
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
.hakoagent/                      # HakoAgent data directory (not tracked by git)
├── hakoagent.db                 # HakoDB database (single file)
├── skills/                      # Skill files in Markdown format
│   ├── skill_001.md
│   └── skill_002.md
├── sessions/                    # Session exports (optional)
└── logs/                        # Operation logs (optional)

hakoagent-core/                    # Rust crate (HakoDB binding + core logic)
├── Cargo.toml
├── build.rs                     # cbindgen for hakodb.h generation
├── src/
│   ├── lib.rs                   # Crate entry point
│   ├── binding/                 # C ABI / FFI wrapper
│   │   ├── mod.rs
│   │   ├── engine.rs            # HK_Engine handle
│   │   ├── doc.rs               # HK_Doc handle
│   │   ├── query.rs             # HK_Query handle
│   │   ├── batch.rs             # HK_Batch handle
│   │   ├── transaction.rs       # HK_Transaction handle
│   │   ├── watch.rs             # HK_Watch handle
│   │   └── result_set.rs        # HK_ResultSet handle
│   ├── memory/                  # Memory Service
│   │   ├── mod.rs
│   │   ├── sessions.rs
│   │   ├── events.rs            # Append-only event log with application-level guard
│   │   ├── decisions.rs
│   │   ├── findings.rs
│   │   ├── code_index.rs
│   │   ├── tasks.rs             # Task with target + DoD
│   │   ├── context_cache.rs
│   │   ├── skills.rs            # Skill data model
│   │   └── lessons_learned.rs
│   ├── indexer/                 # Codebase Indexer
│   │   ├── mod.rs
│   │   ├── scanner.rs
│   │   └── watcher.rs           # watch_collection integration
│   ├── retriever/               # Context Retriever
│   │   ├── mod.rs
│   │   ├── hnsw.rs              # HNSW vector search
│   │   ├── fts.rs               # Full-text search
│   │   ├── summarizer.rs        # Summary before the endpoint
│   │   └── cache.rs             # context_cache
│   ├── planner/                 # Task Planner
│   │   ├── mod.rs
│   │   ├── task.rs              # Target + DoD
│   │   └── flow.rs              # Consistent across models (6-step flow)
│   ├── skill_engine/            # Skill Engine
│   │   ├── mod.rs
│   │   ├── reflector.rs         # Post-task reflection
│   │   ├── extractor.rs         # Skill extraction
│   │   └── registry.rs          # Skill registry
│   └── vigilance/               # Vigilance Checker
│       ├── mod.rs
│       ├── unused_file.rs
│       ├── todo_detector.rs
│       └── regression.rs
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
├── examples/
│   └── python/                  # Integration example for non-Rust languages
└── cli/                         # CLI entry point (hakoagent command)
    ├── Cargo.toml
    └── src/
        └── main.rs
```

**Structure Decision**: Single project structure (DEFAULT) — the `hakoagent-core` Rust crate as the core, the CLI as a separate crate, data in `.hakoagent/`. This meets the language-agnostic requirement via the C ABI and keeps all files within hakoagent scope.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations. This section is left empty.

---

## Phase 0: Outline & Research

### Unknowns from Technical Context

No NEEDS CLARIFICATION items remain. All technical parameters were determined through the spec and prior clarifications:

| Unknown | Status | Resolution |
|---------|--------|----------|
| Append-only mechanism | Resolved | Application-level guard (documented in spec FR-004 + Clarifications session) |
| Skill format | Resolved | Markdown (documented in spec FR-005 + constitution Section 4) |
| Database location | Resolved | `.hakoagent/hakoagent.db` (constitution Section 3) |

### Research Findings (research.md)

No research task is required because all unknowns have been resolved. `research.md` will be recorded as "no unresolved clarifications".

**Output**: `research.md` noting that all NEEDS CLARIFICATION items were resolved previously.

---

## Phase 1: Design & Contracts

### Data Model (`data-model.md`)

Entities extracted from the feature spec:

| Entity | Key Attributes | Relationships |
|---------|--------------|----------|
| Event | event_id, timestamp, session_id, actor, action, target, change_type, metadata | session_id → Session |
| Session | session_id, started_at, ended_at, summary, status, model_used | 1:N with Event |
| Task | task_id, title, target, definition_of_done, priority, status, dod_verified, model_used | session_id → Session |
| Skill | skill_id, name, description, context_tags, success_count, failure_count, last_used, status | — |
| Finding | finding_id, content, finding_type, file, event_id | event_id → Event |
| Decision | decision_id, title, rationale, consequences, event_id | event_id → Event |
| CodeIndex | entry_id, file_path, symbol_name, symbol_type, dependencies, line_number | — |
| ContextCacheEntry | cache_key, query, summary, source_documents, created_at, ttl_seconds, hit_count | — |
| Lesson | lesson_id, title, description, failure_context, remediation, tags, status | — |

State transitions:
- Task: todo → in-progress → done (dod_verified=true) / blocked
- Skill: active → deprecated / archived
- Event: append-only (no transitions, create only)

Validation rules:
- Event: event_id must be unique and cannot be overwritten (application-level guard)
- Task: target and definition_of_done must not be empty
- Skill: skill_id must be unique, file format is Markdown

### Interface Contracts (`contracts/`)

HakoAgent exposes a tool calling interface for the harness agent. The following contracts are defined:

**File**: `contracts/tool-calling-interface.md`

| Tool | Parameters | Return |
|------|-----------|--------|
| `hakoagent.init` | db_path, collections | status, collections_created |
| `hakoagent.index` | root_path | indexed_count |
| `hakoagent.recall` | query, limit | context_results |
| `hakoagent.skill_list` | — | skills_list |
| `hakoagent.skill_add` | name, content (Markdown) | skill_id, status |
| `hakoagent.skill_get` | skill_id or name | skill_content (Markdown) |
| `hakoagent.task_list` | — | tasks_list |
| `hakoagent.task_create` | title, target, definition_of_done, priority | task_id, status |
| `hakoagent.task_complete` | task_id, dod_verified | status, completed_at |
| `hakoagent.events` | limit, session_id | events_list |
| `hakoagent.event_log` | action, target, actor, metadata | event_id, timestamp |
| `hakoagent.vigilance` | root_path | vigilance_report |
| `hakoagent.finding_save` | content, finding_type, file | finding_id |
| `hakoagent.decision_save` | title, rationale, consequences | decision_id |

Return values are always in JSON format for easy parsing by the harness agent.

### Quickstart Validation Guide (`quickstart.md`)

**Prerequisites**:
- Rust toolchain installed
- Write permission in the project working directory

**Setup commands**:
```bash
# Build HakoAgent
cargo build --release --manifest-path cli/Cargo.toml

# Initialize the database
./cli/target/release/hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

**Test/run commands**:
```bash
# Test init
./cli/target/release/hakoagent init --db ./.hakoagent/hakoagent.db --collections all

# Test recall
./cli/target/release/hakoagent recall "bagaimana implementasi error handling Rust?"

# Test skill
./cli/target/release/hakoagent skill list

# Test task
./cli/target/release/hakoagent task list

# Test vigilance
./cli/target/release/hakoagent vigilance
```

**Expected outcomes**:
- `init`: 9 collections created at `.hakoagent/hakoagent.db`
- `recall`: Returns relevant context within the target time
- `skill list`: Lists all active skills
- `task list`: Lists tasks with their statuses
- `vigilance`: Reports overlooked files, TODOs, and constitution regressions

### Re-evaluate Constitution Check (post-design)

| Constitution Principle | Post-Design Status | Notes |
|-------------------|-------------------|---------|
| Smart Memory | Met | 9 collections defined in the data model |
| Anti-Lupa | Met | Skill engine + recall via HNSW+FTS |
| Kronologi & Histori | Met | Append-only events with application-level guard |
| Consistency | Met | Standard tool calling interface |
| Cross-Model Consistency | Met | Same 6-step flow for all LLMs |
| Vigilance | Met | Vigilance Checker module defined |
| Clear Target | Met | Tasks with target + DoD |
| Codebase Fluency | Met | Codebase Indexer + code_index collection |
| Context Frugality | Met | Context Retriever + context_cache |
| Self Skill Improvement | Met | Skill Engine + Markdown skills |

No violations. Constitution check PASSED post-design.

---

**Design artifacts ready: `research.md`, `data-model.md`, `contracts/tool-calling-interface.md`, `quickstart.md`**

Plan workflow complete. Ready to proceed to `/hakoagent-tasks`.
