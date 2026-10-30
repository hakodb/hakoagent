# Implementation Plan: Refactor HakoAgent to Constitution

**Branch**: `001-refactor-hakoagent` | **Date**: 2026-10-29 | **Spec**: `specs/001-refactor-hakoagent/spec.md`

**Input**: Feature specification from `/specs/001-refactor-hakoagent/spec.md`

## Summary

Refactor proyek hakoagent agar sesuai dengan konstitusi terbaru yang didasarkan pada HakoDB. Tujuan utama: membangun tool pendukung harness agent yang smart, tidak mudah lupa, konsisten lintas model LLM, cekatan, target jelas, mengerti codebase dengan cepat, dan irit context/endpoint request. Refactor mencakup 7 modul: HakoDB Binding Layer, Memory Service, Codebase Indexer, Context Retriever, Task Planner, Skill Engine, dan Vigilance Checker. Skill disimpan dalam format Markdown di `.hakoagent/skills/`, database HakoDB di `.hakoagent/hakoagent.db`, dan semua file terkait berada di lingkup hakoagent (tidak ada referensi ke hakoagent).

## Technical Context

**Language/Version**: Rust 1.75+ (core), Python 3.11+ (contoh integrasi harness)

**Primary Dependencies**: hakodb 0.19 (embedded core, `--no-default-features`), cbindgen (C ABI generation), serde (JSON), chrono (timestamp), uuid (ID generation), lazy_static (append-only guard)

**Storage**: HakoDB embedded document database (single file, `.hakoagent/hakoagent.db`), WAL durability, tiered-segment storage

**Testing**: `cargo test` (Rust core), integration tests untuk CLI commands, unit tests untuk setiap modul

**Target Platform**: Linux, macOS, Windows (shared library + CLI binary)

**Project Type**: CLI tool + library (Rust crate) + FFI bindings

**Performance Goals**: Siklus tugas lengkap < 30 detik; waktu ambil konteks < X detik; pengurangan panggilan endpoint LLM ≥ N%

**Constraints**: Irit context dan endpoint request; embedded (tanpa server/daemon); footprint ringan (`--no-default-features`); semua file di bawah `.hakoagent/` atau root proyek; skill dalam format Markdown; tidak ada referensi ke hakoagent

**Scale/Scope**: Single project per database; 9 koleksi HakoDB; 7 modul implementasi; 12 tool calling interface

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Prinsip Konstitusi | Status | Catatan |
|-------------------|--------|---------|
| Smart Memory | Terpenuhi | Koleksi `sessions`, `decisions`, `findings`, `skills` |
| Anti-Lupa | Terpenuhi | Query `findings` + `skills` sebelum tugas baru |
| Kronologi & Histori | Terpenuhi | Event log append-only di koleksi `events` |
| Consistency | Terpenuhi | Template output standar lintas model |
| Cross-Model Consistency | Terpenuhi | Flow tugas sama untuk semua LLM |
| Vigilance | Terpenuhi | Modul Vigilance Checker |
| Clear Target | Terpenuhi | Setiap task punya target + DoD |
| Codebase Fluency | Terpenuhi | Koleksi `code_index` + indexer |
| Context Frugality | Terpenuhi | HNSW + FTS + `context_cache` + rangkuman |
| Self Skill Improvement | Terpenuhi | Koleksi `skills` + `lessons_learned` + Markdown |

No violations. Constitution check PASSED.

## Project Structure

### Documentation (this feature)

```text
specs/001-refactor-hakoagent/
├── spec.md          # Spesifikasi fitur (/hakoagent.specify output)
├── plan.md          # Rencana teknis (ini, /hakoagent.plan output)
├── research.md      # Phase 0 output (/hakoagent.plan command)
├── data-model.md    # Phase 1 output (/hakoagent.plan command)
├── quickstart.md    # Phase 1 output (/hakoagent.plan command)
├── contracts/       # Phase 1 output (/hakoagent.plan command)
└── tasks.md         # Phase 2 output (/hakoagent.tasks command - NOT created by /hakoagent.plan)
```

### Source Code (repository root)

```text
.hakoagent/                      # Directory data HakoAgent (tidak di-track ke git)
├── hakoagent.db                 # Database HakoDB (single file)
├── skills/                      # Skill files dalam format Markdown
│   ├── skill_001.md
│   └── skill_002.md
├── sessions/                    # Export sesi (opsional)
└── logs/                        # Log operasi (opsional)

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
│   │   ├── summarizer.rs        # Rangkuman sebelum endpoint
│   │   └── cache.rs             # context_cache
│   ├── planner/                 # Task Planner
│   │   ├── mod.rs
│   │   ├── task.rs              # Target + DoD
│   │   └── flow.rs              # Konsisten lintas model (6-step flow)
│   ├── skill_engine/            # Skill Engine
│   │   ├── mod.rs
│   │   ├── reflector.rs         # Rifleksi pasca-tugas
│   │   ├── extractor.rs         # Ekstraksi skill
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
│   └── python/                  # Contoh integrasi bahasa non-Rust
└── cli/                         # CLI entry point (hakoagent command)
    ├── Cargo.toml
    └── src/
        └── main.rs
```

**Structure Decision**: Single project structure (DEFAULT) — Rust crate `hakoagent-core` sebagai inti, CLI sebagai crate terpisah, data di `.hakoagent/`. Ini memenuhi kebutuhan bahasa-agnostik via C ABI dan semua file tetap di lingkup hakoagent.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Tidak ada pelanggaran konstitusi. Kolom ini dikosongkan.

---

## Phase 0: Outline & Research

### Unknowns from Technical Context

Tidak ada NEEDS CLARIFICATION yang tersisa. Semua parameter teknis telah ditentukan melalui spec dan clarifikasi sebelumnya:

| Unknown | Status | Resolusi |
|---------|--------|----------|
| Mekanisme append-only | Resolved | Application-level guard (dokumentasi di spec FR-004 + Clarifications session) |
| Format skill | Resolved | Markdown (dokumentasi di spec FR-005 + constitution Section 4) |
| Lokasi database | Resolved | `.hakoagent/hakoagent.db` (constitution Section 3) |

### Research Findings (research.md)

Tidak ada research task yang diperlukan karena semua unknown telah diresolusi. `research.md` akan dicatat sebagai "no unresolved clarifications".

**Output**: `research.md` dengan catatan bahwa semua NEEDS CLARIFICATION telah diresolusi sebelumnya.

---

## Phase 1: Design & Contracts

### Data Model (`data-model.md`)

Entitas yang diekstrak dari feature spec:

| Entitas | Atribut Utama | Hubungan |
|---------|--------------|----------|
| Event | event_id, timestamp, session_id, actor, action, target, change_type, metadata | session_id → Session |
| Session | session_id, started_at, ended_at, ringkasan, status, model_used | 1:N dengan Event |
| Task | task_id, title, target, definition_of_done, prioritas, status, dod_verified, model_used | session_id → Session |
| Skill | skill_id, name, description, context_tags, success_count, failure_count, last_used, status | — |
| Finding | finding_id, content, finding_type, file, event_id | event_id → Event |
| Decision | decision_id, title, rationale, consequences, event_id | event_id → Event |
| CodeIndex | entry_id, file_path, symbol_name, symbol_type, dependensi, line_number | — |
| ContextCacheEntry | cache_key, query, summary, source_documents, created_at, ttl_seconds, hit_count | — |
| Lesson | lesson_id, title, description, failure_context, remediation, tags, status | — |

State transitions:
- Task: todo → in-progress → done (dod_verified=true) / blocked
- Skill: active → deprecated / archived
- Event: append-only (tidak ada transition, hanya create)

Validation rules:
- Event: event_id harus unik, tidak dapat di-overwrite (application-level guard)
- Task: target dan definition_of_done tidak boleh kosong
- Skill: skill_id harus unik, format file Markdown

### Interface Contracts (`contracts/`)

HakoAgent mengekspos tool calling interface untuk harness agent. Kontrak berikut didefinisikan:

**File**: `contracts/tool-calling-interface.md`

| Tool | Parameter | Return |
|------|-----------|--------|
| `hakoagent.init` | db_path, collections | status, collections_created |
| `hakoagent.index` | root_path | indexed_count |
| `hakoagent.recall` | query, limit | context_results |
| `hakoagent.skill_list` | — | skills_list |
| `hakoagent.skill_add` | name, content (Markdown) | skill_id, status |
| `hakoagent.skill_get` | skill_id atau name | skill_content (Markdown) |
| `hakoagent.task_list` | — | tasks_list |
| `hakoagent.task_create` | title, target, definition_of_done, priority | task_id, status |
| `hakoagent.task_complete` | task_id, dod_verified | status, completed_at |
| `hakoagent.events` | limit, session_id | events_list |
| `hakoagent.event_log` | action, target, actor, metadata | event_id, timestamp |
| `hakoagent.vigilance` | root_path | vigilance_report |
| `hakoagent.finding_save` | content, finding_type, file | finding_id |
| `hakoagent.decision_save` | title, rationale, consequences | decision_id |

Return value selalu dalam format JSON untuk kemudahan parsing oleh harness agent.

### Quickstart Validation Guide (`quickstart.md`)

**Prerequisites**:
- Rust toolchain terinstal
- Hak izin tulis di working directory proyek

**Setup commands**:
```bash
# Build HakoAgent
cargo build --release --manifest-path cli/Cargo.toml

# Inisialisasi database
./cli/target/release/hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

**Test/run commands**:
```bash
# Uji init
./cli/target/release/hakoagent init --db ./.hakoagent/hakoagent.db --collections all

# Uji recall
./cli/target/release/hakoagent recall "bagaimana implementasi error handling Rust?"

# Uji skill
./cli/target/release/hakoagent skill list

# Uji task
./cli/target/release/hakoagent task list

# Uji vigilance
./cli/target/release/hakoagent vigilance
```

**Expected outcomes**:
- `init`: 9 koleksi dibuat di `.hakoagent/hakoagent.db`
- `recall`: Mengembalikan konteks relevan dalam waktu target
- `skill list`: Menampilkan semua skill aktif
- `task list`: Menampilkan daftar tugas dengan status
- `vigilance`: Melaporkan file terlupakan, TODO, dan regresi konstitusi

### Re-evaluate Constitution Check (post-design)

| Prinsip Konstitusi | Status Post-Design | Catatan |
|-------------------|-------------------|---------|
| Smart Memory | Terpenuhi | 9 koleksi didefinisikan dalam data model |
| Anti-Lupa | Terpenuhi | Skill engine + recall via HNSW+FTS |
| Kronologi & Histori | Terpenuhi | Event append-only dengan application-level guard |
| Consistency | Terpenuhi | Tool calling interface standar |
| Cross-Model Consistency | Terpenuhi | Flow 6 langkah sama untuk semua LLM |
| Vigilance | Terpenuhi | Modul Vigilance Checker didefinisikan |
| Clear Target | Terpenuhi | Task dengan target + DoD |
| Codebase Fluency | Terpenuhi | Codebase Indexer + code_index koleksi |
| Context Frugality | Terpenuhi | Context Retriever + context_cache |
| Self Skill Improvement | Terpenuhi | Skill Engine + skill Markdown |

No violations. Constitution check PASSED post-design.

---

**Design artifacts siap: `research.md`, `data-model.md`, `contracts/tool-calling-interface.md`, `quickstart.md`**

Plan workflow selesai. Siap untuk dilanjutkan ke `/hakoagent-tasks`.
