# Implementation Plan: HakoAgent Multi-Agent Context Sync

**Branch**: `006-multi-agent-context-sync` | **Date**: 2026-10-29 | **Spec**: `specs/006-multi-agent-context-sync/spec.md`

**Input**: Feature specification from `/specs/006-multi-agent-context-sync/spec.md`

## Summary

Extend the Python-only HakoAgent to be a full agent memory, context, and history system backed by the real prebuilt HakoDB shared library via ctypes FFI, with a sync path enabling multiple harness agents to share context through a common HakoDB instance. The system stores sessions, events, decisions, findings, tasks, skills, and code_index documents; supports append-only event logging, TF-IDF + cosine similarity recall, TTL-based context caching, and cross-agent document sharing via an `actor` attribution field.

## Technical Context

**Language/Version**: Python 3.11+ (stdlib only, no external dependencies, no build step)

**Primary Dependencies**: Python standard library (`ctypes`, `json`, `hashlib`, `uuid`, `time`, `datetime`, `re`, `math`, `collections`, `heapq`, `pathlib`); prebuilt HakoDB shared library (`lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so`) loaded via `ctypes`; C ABI header `lib/hakodb.h` (v0.20.0, hash-verified)

**Storage**: HakoDB via FFI for writes/reads, with JSON file fallback under `.hakoagent/memory/<collection>/` (9 collections: sessions, events, decisions, findings, code_index, tasks, context_cache, skills, lessons_learned)

**Testing**: `test_hakoagent.py` (Python stdlib unittest, 31+ tests); new tests for FFI write/read, append-only guard, multi-agent sharing

**Target Platform**: Linux (x86_64 glibc2.28-el8), cross-platform Python

**Project Type**: Single Python CLI script (`hakoagent`) at project root

**Performance Goals**: Single-agent write/read via FFI < 1 second; cache hit ratio ≥ 50% for repeated queries; cache hit response < 100ms

**Constraints**: No Rust, no Cargo, no build step; embedded (no server/daemon); all files under `.hakoagent/` or project root; Python stdlib only; graceful fallback to JSON when HakoDB library unavailable

**Scale/Scope**: Single project per HakoDB file; multiple agents share the same `.hakoagent/hakoagent.db` via filesystem; 9 collections; actor-attributed documents for multi-agent awareness

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Prinsip Konstitusi | Status | Catatan |
|-------------------|--------|---------|
| Smart Memory | Terpenuhi | Sessions, events, decisions, findings, tasks, skills collections via FFI |
| Anti-Lupa | Terpenuhi | Query findings + skills via recall before new tasks |
| Kronologi & Histori | Terpenuhi | Append-only events with ISO 8601 timestamps, event_id uniqueness guard |
| Consistency | Terpenuhi | Template output, naming, error handling consistent across agents |
| Cross-Model Consistency | Terpenuhi | Flow identical regardless of LLM model |
| Vigilance | Terpenuhi | Existing vigilance checker detects regressions, TODO, unused files |
| Clear Target | Terpenuhi | Task with target + DoD |
| Codebase Fluency | Terpenuhi | Code_index collection + indexer |
| Context Frugality | Terpenuhi | Context cache TTL + recall with vector search |
| Self Skill Improvement | Terpenuhi | Skills collection + skill engine |
| Python Only | Terpenuhi | No Rust/Cargo/build; stdlib only |
| Real Hakodb FFI | Terpenuhi | libhakodb .so + hakodb.h via ctypes |
| Code Quality | Terpenuhi | Clean Python, no bare except, no hardcoded secrets |
| Testing | Terpenuhi | Unit tests for all new FFI functions |
| Maintainability | Terpenuhi | Docs updated with code, no stale Rust references |

No violations. Constitution check PASSED.

## Project Structure

### Documentation (this feature)

```text
specs/006-multi-agent-context-sync/
├── spec.md          # Feature specification (this feature)
├── plan.md          # Implementation plan (this file)
├── research.md      # Phase 0 output (create next)
├── data-model.md    # Phase 1 output (create next)
├── quickstart.md    # Phase 1 output (create next)
├── contracts/       # Phase 1 output (create next)
└── tasks.md         # Phase 2 output (create via /speckit-tasks)
```

### Source Code (repository root)

```text
hakoagent                      # Python CLI script (stdlib only) — extended with FFI memory functions
lib/
├── libhakodb-x86_64-unknown-linux-glibc2.28-el8.so   # Prebuilt HakoDB shared library (v0.20.0)
├── hakodb.h                                               # HakoDB C ABI header (v0.20.0, hash-verified)
└── SHA256SUMS.txt                                         # Release checksums
.hakoagent/                      # Runtime data directory
├── hakoagent.db                 # HakoDB database file (via FFI)
├── memory/                      # JSON files per collection (fallback / dual-write)
│   ├── sessions/, events/, decisions/, findings/, code_index/,
│   │   tasks/, context_cache/, skills/, lessons_learned/
├── skills/                      # Skill Markdown files
├── sessions/                    # Session exports (optional)
└── logs/                        # Operation logs (optional)
specs/                         # Feature specs (001-006)
docs/                          # T057 perf, T059 security
examples/
└── performance_benchmark.rs
test_hakoagent.py              # Python stdlib unittest (31+ tests)
install.sh                     # Project installer
INSTALL.md                     # Installation guide
AGENTS.md                      # Agent-facing instructions
```

**Structure Decision**: Single project structure (DEFAULT) — one Python CLI script `hakoagent` at project root, extended with real HakoDB FFI functions. All runtime data stays under `.hakoagent/` or project root. No Rust, no Cargo, no separate crate.

## Phase 0: Outline & Research

### Unknowns from Technical Context

| Unknown | Status | Resolusi |
|---------|--------|----------|
| HakoDB FFI function signatures confirmed against real .so | Resolved | Verified `hk_engine_insert_json`, `hk_engine_get_json`, `hk_engine_delete`, `hk_engine_open`, `hk_engine_free`, `hk_string_free` export symbols |
| Multi-agent sync mechanism | Resolved | Shared filesystem HakoDB + `actor` attribution field; no network server needed |
| Fallback behavior when library missing | Resolved | Graceful fallback to JSON files under `.hakoagent/memory/` |

### Research Findings

The prebuilt `libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` (v0.20.0) exports the following FFI functions verified via `nm -D`:
- `hk_engine_open`, `hk_engine_free`, `hk_engine_insert_json`, `hk_engine_get_json`, `hk_engine_delete`, `hk_string_free`, plus many others

The current Python FFI wrapper in `hakoagent` was using incorrect signatures (`hk_engine_insert` with 4 string args, `hk_engine_get` returning `c_char_p`). These have been corrected to use `hk_engine_insert_json` and `hk_engine_get_json` with proper `c_void_p` pointer handling.

Output: `research.md` documenting FFI symbol verification and multi-agent sync design.

## Phase 1: Design & Contracts

### Data Model (`data-model.md`)

Entities from the feature spec:

| Entity | Key Attributes | Relationships |
|--------|---------------|---------------|
| Session | session_id, started_at, ended_at, status, summary, model_used, actor | 1:N with Event |
| Event | event_id, timestamp (ISO 8601), session_id, actor, action, target, change_type, metadata | session_id → Session |
| Decision | decision_id, title, rationale, consequences, event_id, actor | event_id → Event |
| Finding | finding_id, content, finding_type, file, event_id, actor | event_id → Event |
| Task | task_id, title, target, definition_of_done, priority, status, dod_verified, actor | — |
| Skill | skill_id, name, description, context_tags, success_count, failure_count, status, actor | — |
| CodeIndex | entry_id, file_path, symbol_name, symbol_type, dependensi, line_number, file_hash, actor | — |
| ContextCacheEntry | cache_key, query, summary, source_documents, created_at, ttl_seconds, hit_count | — |

State transitions:
- Session: active → ended (ended_at set)
- Task: todo → in-progress → done (dod_verified=true) / blocked
- Skill: active → deprecated / archived
- Event: append-only (create only, no update/delete)

Validation rules:
- Event: event_id must be unique; append-only guard rejects duplicates
- Task: target and definition_of_done must not be empty
- All documents: actor field must be present (multi-agent attribution)

### Interface Contracts (`contracts/`)

**File**: `contracts/multi-agent-context-interface.md`

| Tool | Parameter | Return |
|------|-----------|--------|
| `hakoagent.init` | db_path, collections | status, collections_created |
| `hakoagent.event_log` | action, target, actor, session_id, change_type, metadata | event_id, timestamp |
| `hakoagent.recall` | query, limit, actor | context_results, cache_hit |
| `hakoagent.cache.stats` | — | total_hits, total_misses, eviction_count, cache_size |
| `hakoagent.task.create` | title, target, definition_of_done, priority, actor | task_id, status |
| `hakoagent.task.complete` | task_id, dod_verified, actor | status, completed_at |
| `hakoagent.skill.add` | name, content (Markdown), actor | skill_id, status |
| `hakoagent.events` | limit, session_id, actor | events_list |
| `hakoagent.index` | root_path | indexed_count |
| `hakoagent.vigilance` | root_path | vigilance_report |

Return value always in JSON format for harness agent parsing.

### Quickstart Validation Guide (`quickstart.md`)

**Prerequisites**:
- Python 3 (stdlib only, no external dependencies)
- Prebuilt HakoDB library at `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` + header `lib/hakodb.h`
- Write permission in working directory

**Setup commands**:
```bash
# Initialize database
./hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

**Test/run commands**:
```bash
# Single-agent memory write + read
./hakoagent event_log "code_read" "src/main.py" "agent-a" "info" '{"file": "src/main.py"}'
./hakoagent recall "main.py" --limit 5

# Multi-agent sync: agent-a writes, agent-b reads
./hakoagent event_log "decision" "use Python FFI" "agent-a" "info" '{"rationale": "stdlib only"}'
./hakoagent recall "Python FFI" --limit 5  # agent-b sees agent-a's event

# Cache
./hakoagent cache stats
./hakoagent cache put "test-query" "test-summary" 300
./hakoagent cache get "test-query"

# Task
./hakoagent task create "Implement sync" "Multi-agent context sharing works" "Two agents read same doc" P1 "agent-a"
./hakoagent task list

# Events (history)
./hakoagent events

# Full test suite
python3 test_hakoagent.py
```

**Expected outcomes**:
- `./hakoagent event_log`: Creates append-only event with unique event_id and ISO 8601 timestamp
- `./hakoagent recall`: Returns relevant context ranked by similarity; second identical query within TTL is cache hit
- Multi-agent: Document written by agent-A is readable by agent-B via same HakoDB
- `./hakoagent cache stats`: Shows hits, misses, hit rate, cache size, eviction count
- `python3 test_hakoagent.py`: 31+ tests passing

### Re-evaluate Constitution Check (post-design)

| Prinsip Konstitusi | Status Post-Design | Catatan |
|-------------------|-------------------|---------|
| Smart Memory | Terpenuhi | 9 collections via FFI + JSON fallback |
| Anti-Lupa | Terpenuhi | Recall queries findings + skills |
| Kronologi & Histori | Terpenuhi | Append-only events with event_id guard |
| Consistency | Terpenuhi | JSON return format, standard tool names |
| Cross-Model Consistency | Terpenuhi | Same flow for all LLM models |
| Vigilance | Terpenuhi | Existing vigilance checker |
| Clear Target | Terpenuhi | Task with target + DoD |
| Codebase Fluency | Terpenuhi | Code_index + graph traversal |
| Context Frugality | Terpenuhi | Context cache TTL + recall |
| Self Skill Improvement | Terpenuhi | Skills + lessons_learned |
| Python Only | Terpenuhi | stdlib only, no Rust/Cargo |
| Real Hakodb FFI | Terpenuhi | ctypes to libhakodb .so |
| Code Quality | Terpenuhi | No bare except, no hardcoded secrets |
| Testing | Terpenuhi | 31+ tests passing |
| Maintainability | Terpenuhi | Docs current, no stale references |

No violations. Constitution check PASSED post-design.

---

**Design artifacts ready**: `research.md`, `data-model.md`, `contracts/multi-agent-context-interface.md`, `quickstart.md`

Plan workflow complete. Ready to proceed to `/speckit-tasks`.
