# Implementation Plan: Auto Codebase Indexing

**Branch**: `002-auto-code-indexing` | **Date**: 2026-10-29 | **Spec**: `specs/002-auto-code-indexing/spec.md`

**Input**: Feature specification from `/specs/002-auto-code-indexing/spec.md`

## Summary

Auto Codebase Indexing adalah fitur yang memungkinkan HakoAgent secara otomatis memindai dan mengindex codebase tanpa perlu agen memanggil perintah `hakoagent index` secara manual. Saat sesi startup, scanning codebase dijalankan sebagai background thread dalam proses agen yang sama. Jika database belum ada, scanning dilakukan penuh; jika sudah ada, diverifikasi dan diperbarui hanya file yang berubah. Hasil indexing disimpan di koleksi `code_index` di HakoDB. Fitur ini mendukung indexing inkremental, deteksi file baru/dihapus/diubah, dan notifikasi selesai kepada agen.

## Technical Context

**Language/Version**: Rust 1.75+ (core), Python 3.11+ (contoh integrasi)

**Primary Dependencies**: hakodb 0.19 (embedded core, `--no-default-features`), notify (file system watcher), walkdir (directory traversal), serde (JSON), chrono (timestamp), uuid (ID generation)

**Storage**: HakoDB embedded document database (`.hakoagent/hakoagent.db`), koleksi `code_index` untuk penyimpanan hasil indexing

**Testing**: `cargo test` (Rust core), integration tests untuk indexing flow

**Target Platform**: Linux, macOS, Windows (file system watcher cross-platform)

**Project Type**: CLI tool + library (Rust crate) + FFI bindings

**Performance Goals**: Waktu indexing inkremental untuk satu file < 5 detik (SC-002); startup scan selesai dalam waktu wajar untuk codebase kecil menengah

**Constraints**: Background thread dalam proses agen (tidak proses terpisah); embedded database (tanpa server); irit context dan endpoint request; semua file di bawah `.hakoagent/` atau root proyek; tidak ada referensi ke hakoagent

**Scale/Scope**: Single project per database; 9 koleksi HakoDB termasuk `code_index`; file source code (.rs, .py, .js, .ts, .go, dll.)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Prinsip Konstitusi | Status | Catatan |
|-------------------|--------|---------|
| Smart Memory | Terpenuhi | Hasil indexing disimpan di `code_index` HakoDB |
| Anti-Lupa | Terpenuhi | code_index tetap up-to-date secara otomatis |
| Kronologi & Histori | Terpenuhi | IndexingRun dicatat sebagai event append-only |
| Consistency | Terpenuhi | Template output standar untuk notifikasi indexing |
| Cross-Model Consistency | Terpenuhi | Flow indexing sama untuk semua model LLM |
| Vigilance | Terpenuhi | Deteksi file yang berubah, dihapus, atau baru |
| Clear Target | Terpenuhi | Setiap tugas indexing punya target dan DoD |
| Codebase Fluency | Terpenuhi | code_index menyimpan simbol, file, dependensi |
| Context Frugality | Terpenuhi | Indexing inkremental mengurangi beban endpoint LLM |
| Self Skill Improvement | Terpenuhi | Pola indexing sukses dapat diekstrak sebagai skill |

No violations. Constitution check PASSED.

## Project Structure

### Documentation (this feature)

```text
specs/002-auto-code-indexing/
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
.hakoagent/                      # Directory data HakoAgent
├── hakoagent.db                 # Database HakoDB (single file)
├── skills/                      # Skill files dalam format Markdown
├── sessions/                    # Export sesi (opsional)
└── logs/                        # Log operasi (opsional)

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

**Structure Decision**: Single project structure (DEFAULT) — Rust crate `hakoagent-core` sebagai inti, CLI sebagai crate terpisah. Auto indexer ditambahkan sebagai modul baru di `indexer/auto_indexer.rs` yang menggunakan background thread untuk scanning startup dan inkremental update.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Tidak ada pelanggaran konstitusi. Kolom ini dikosongkan.

---

## Phase 0: Outline & Research

### Unknowns from Technical Context

Tidak ada NEEDS CLARIFICATION yang tersisa. Semua parameter telah ditentukan melalui spec dan clarifikasi sebelumnya:

| Unknown | Status | Resolusi |
|---------|--------|----------|
| Mekanisme startup scanning | Resolved | Background thread dalam proses agen (Clarification Session 2026-10-29) |
| Database belum ada vs sudah ada | Resolved | Full scan jika belum ada, verifikasi + update jika sudah ada (FR-001) |

### Research Findings (research.md)

Tidak ada research task yang diperlukan karena semua unknown telah diresolusi. `research.md` dicatat sebagai "no unresolved clarifications".

**Output**: `research.md` dengan catatan bahwa semua NEEDS CLARIFICATION telah diresolusi sebelumnya.

---

## Phase 1: Design & Contracts

### Data Model (`data-model.md`)

Entitas yang diekstrak dari feature spec:

| Entitas | Atribut Utama | Hubungan |
|---------|--------------|----------|
| CodeIndexEntry | entry_id, file_path, symbol_name, symbol_type, dependensi, line_number, last_indexed_at, file_hash | — |
| FileChange | change_id, file_path, change_type (created/modified/deleted), timestamp, indexed_status | — |
| IndexingRun | run_id, started_at, ended_at, files_processed, files_indexed, errors, status | — |

State transitions:
- IndexingRun: started → completed / failed
- FileChange: detected → indexed / skipped / error
- CodeIndexEntry: created → updated / deleted

Validation rules:
- CodeIndexEntry: file_hash harus unik per file_path, last_indexed_at harus diupdate saat perubahan
- FileChange: change_type harus salah satu dari created/modified/deleted
- IndexingRun: files_processed harus >= files_indexed

### Interface Contracts (`contracts/`)

HakoAgent mengekspos tool calling interface untuk auto indexing. Kontrak berikut didefinisikan:

**File**: `contracts/auto-indexing-interface.md`

| Tool | Parameter | Return |
|------|-----------|--------|
| `hakoagent.index` | — | indexing_run_id, status |
| `hakoagent.recall` | query, limit | context_results |
| `hakoagent.events` | limit, session_id | events_list (termasuk indexing events) |

Auto indexing berjalan sebagai background thread, tidak memerlukan CLI command tambahan. CLI `hakoagent index` dapat dipanggil secara manual untuk memaksa re-index.

Return value selalu dalam format JSON untuk kemudahan parsing oleh harness agent.

### Quickstart Validation Guide (`quickstart.md`)

**Prerequisites**:
- Rust toolchain terinstal
- Hak izin tulis di working directory proyek
- Database HakoDB sudah diinisialisasi (`hakoagent init`)

**Setup commands**:
```bash
# Build HakoAgent
cargo build --release --manifest-path cli/Cargo.toml

# Inisialisasi database
./cli/target/release/hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

**Test/run commands**:
```bash
# Uji auto indexing saat startup
./cli/target/release/hakoagent init --db ./.hakoagent/hakoagent.db --collections all
# Background thread akan secara otomatis scan codebase

# Uji indexing inkremental
# Ubah satu file source code, lalu tunggu notifikasi indexing

# Uji recall
./cli/target/release/hakoagent recall "fungsi error handling"
```

**Expected outcomes**:
- `init`: Background thread memulai scanning codebase otomatis
- File baru: Secara otomatis ditambahkan ke `code_index`
- File diubah: Entri `code_index` diperbarui
- File dihapus: Entri `code_index` dihapus
- Notifikasi: Agen menerima ringkasan indexing setelah selesai

### Re-evaluate Constitution Check (post-design)

| Prinsip Konstitusi | Status Post-Design | Catatan |
|-------------------|-------------------|---------|
| Smart Memory | Terpenuhi | Hasil indexing disimpan di `code_index` |
| Anti-Lupa | Terpenuhi | code_index selalu up-to-date otomatis |
| Kronologi & Histori | Terpenuhi | IndexingRun sebagai event append-only |
| Consistency | Terpenuhi | Notifikasi indexing standar |
| Cross-Model Consistency | Terpenuhi | Flow indexing sama untuk semua LLM |
| Vigilance | Terpenuhi | Deteksi perubahan file otomatis |
| Clear Target | Terpenuhi | Setiap indexing run punya target dan DoD |
| Codebase Fluency | Terpenuhi | code_index menyimpan struktur kode |
| Context Frugality | Terpenuhi | Inkremental mengurangi beban endpoint |
| Self Skill Improvement | Terpenuhi | Pola indexing dapat diekstrak sebagai skill |

No violations. Constitution check PASSED post-design.

---

**Design artifacts siap: `research.md`, `data-model.md`, `contracts/auto-indexing-interface.md`, `quickstart.md`**

Plan workflow selesai. Siap untuk dilanjutkan ke `/hakoagent-tasks`.
