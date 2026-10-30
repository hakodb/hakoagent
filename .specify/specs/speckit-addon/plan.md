# Implementation Plan: Speckit Addon (HakoDB Agent Memory & Skill Engine)

**Branch**: `001-hakoagent-addon` | **Date**: 2026-10-28 | **Spec**: `.specify/specs/hakoagent-addon/spec.md`

**Input**: Feature specification from `/specs/hakoagent-addon/spec.md`

## Summary

Speckit Addon adalah skill/addon plug-and-play untuk harness agent yang didukung oleh HakoDB sebagai memori jangka panjang. Tujuan utamanya menjadikan agent AI lebih smart, tidak mudah lupa, konsisten lintas model LLM, cekatan, target jelas, mengerti codebase dengan cepat, dan irit context/endpoint request. Plan mencakup 7 modul: Hakodb Binding Layer, Memory Service, Codebase Indexer, Context Retriever, Task Planner, Skill Engine, dan Vigilance Checker.

## Technical Context

**Language/Version**: Rust 1.75+ (core), Python 3.11+ (contoh integrasi), Go/JS/TS (binding opsi)

**Primary Dependencies**: hakodb 0.19 (embedded core, `--no-default-features`), cbindgen (C ABI generation), serde (JSON), anyhow (error handling)

**Storage**: HakoDB embedded document database (single file, `./hakoagent.db`), WAL durability, tiered-segment storage

**Testing**: `cargo test` (Rust core), `pytest` (Python contoh), integration tests untuk CLI commands

**Target Platform**: Linux, macOS, Windows (shared library + CLI binary)

**Project Type**: CLI tool + library (Rust crate) + FFI bindings

**Performance Goals**: Waktu ambil konteks terkait tugas < X detik; pengurangan panggilan endpoint LLM per task ≥ N%

**Constraints**: Irit context dan endpoint request; embedded (tanpa server/daemon); footprint ringan (`--no-default-features`)

**Scale/Scope**: Single project per database; 9 koleksi HakoDB; 7 modul implementasi

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
| Self Skill Improvement | Terpenuhi | Koleksi `skills` + `lessons_learned` |

No violations. Constitution check PASSED.

## Project Structure

### Documentation (this feature)

```text
specs/hakoagent-addon/
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
hakoagent-core/              # Rust crate (HakoDB binding + core logic)
├── Cargo.toml
├── build.rs               # cbindgen for hakodb.h generation
├── src/
│   ├── lib.rs             # Crate entry point
│   ├── binding/           # C ABI / FFI wrapper
│   │   ├── mod.rs
│   │   ├── engine.rs      # HK_Engine handle
│   │   ├── doc.rs         # HK_Doc handle
│   │   ├── query.rs       # HK_Query handle
│   │   ├── batch.rs       # HK_Batch handle
│   │   ├── transaction.rs # HK_Transaction handle
│   │   ├── watch.rs       # HK_Watch handle
│   │   └── result_set.rs  # HK_ResultSet handle
│   ├── memory/            # Memory Service
│   │   ├── mod.rs
│   │   ├── sessions.rs
│   │   ├── events.rs      # Append-only event log
│   │   ├── decisions.rs
│   │   ├── findings.rs
│   │   ├── code_index.rs
│   │   ├── tasks.rs
│   │   ├── context_cache.rs
│   │   ├── skills.rs      # Self-improvement skill store
│   │   └── lessons_learned.rs
│   ├── indexer/           # Codebase Indexer
│   │   ├── mod.rs
│   │   ├── scanner.rs
│   │   └── watcher.rs     # watch_collection integration
│   ├── retriever/         # Context Retriever
│   │   ├── mod.rs
│   │   ├── hnsw.rs        # HNSW vector search
│   │   ├── fts.rs         # Full-text search
│   │   ├── summarizer.rs  # Rangkuman sebelum endpoint
│   │   └── cache.rs       # context_cache
│   ├── planner/           # Task Planner
│   │   ├── mod.rs
│   │   ├── task.rs        # Target + DoD
│   │   └── flow.rs        # Konsisten lintas model
│   ├── skill_engine/      # Skill Engine
│   │   ├── mod.rs
│   │   ├── reflector.rs   # Rifleksi pasca-tugas
│   │   ├── extractor.rs   # Ekstraksi skill
│   │   └── registry.rs    # Skill registry
│   └── vigilance/         # Vigilance Checker
│       ├── mod.rs
│       ├── unused_file.rs
│       ├── todo_detector.rs
│       └── regression.rs
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
├── examples/
│   └── python/            # Contoh integrasi bahasa non-Rust
└── cli/                   # CLI entry point (hakoagent command)
    ├── Cargo.toml
    └── src/
        └── main.rs

bindings/
├── python/                # Python FFI binding (ctypes/cffi)
├── go/                    # Go FFI binding (cgo)
├── js/                    # JS/TS FFI binding (node-ffi-napi)
└── cargo/                 # Rust-native binding (no FFI needed)

```

**Structure Decision**: Single project structure (DEFAULT) — Rust crate `hakoagent-core` sebagai inti, CLI sebagai crate terpisah, bindings per bahasa di `bindings/`. Ini memenuhi kebutuhan bahasa-agnostik via C ABI tanpa kompleksitas multi-project.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Tidak ada pelanggaran konstitusi. Kolom ini dikosongkan.

---

## Fase Implementasi (7 Fase)

| Fase | Modul | Deliverable Utama |
|------|-------|-------------------|
| Fase 1 | Hakodb Binding Layer | `build.rs` + cbindgen, shared library, `hakodb.h` per target |
| Fase 2 | Memory Service | CRUD semua 9 koleksi, event append-only, session boundary |
| Fase 3 | Codebase Indexer | `hakoagent index`, scanner, `watch_collection` inkremental |
| Fase 4 | Context Retriever | `hakoagent recall`, HNSW + FTS, summarizer, `context_cache` |
| Fase 5 | Task Planner | Target + DoD, flow konsisten lintas model, template standar |
| Fase 6 | Skill Engine | Rifleksi otomatis, ekstraksi skill, `lessons_learned`, reuse |
| Fase 7 | Vigilance Checker + CLI | Deteksi regresi, TODO, file terlupakan; integrasi CLI penuh |

---

## Rencana Pengujian

1. **Unit tests**: Setiap modul Rust memiliki unit test cakupan ≥ 80%.
2. **Integration tests**: Uji alur lengkap `init → index → recall → task → skill` dengan database HakoDB temporary.
3. **Contract tests**: Uji C ABI binding terhadap `hakodb.h` generated.
4. **Constitution compliance**: Uji bahwa setiap task memiliki DoD dan setiap tindakan dicatat ke `events`.
5. **Cross-model consistency**: Uji flow tugas dengan minimal 2 model LLM berbeda, verifikasi output struktural identik.

---

## Kriteria Penerimaan (dari spec)

- [ ] HakoDB shared library dapat dibangun untuk Linux/macOS/Windows.
- [ ] Semua 9 koleksi HakoDB dapat diakses melalui Memory Service.
- [ ] Event log append-only terverifikasi (tidak ada data yang ter-overwrite).
- [ ] `hakoagent init` membuat database dan koleksi dengan benar.
- [ ] `hakoagent recall` mengembalikan konteks relevan dalam waktu target.
- [ ] Flow tugas konsisten untuk minimal 2 model LLM berbeda.
- [ ] Skill engine dapat mengekstrak dan menyimpan minimal 1 skill dari satu tugas uji coba.
- [ ] Vigilance checker mendeteksi minimal 1 kasus file yang diubah tapi tidak diuji.
- [ ] Dokumentasi instalasi (Cargo, standalone binary, skill.yaml) lengkap dan diuji.

---

**Rencana siap untuk dilanjutkan ke `/hakoagent-tasks`.**
