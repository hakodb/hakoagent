# Quickstart Validation Guide — HakoAgent

**Feature**: 001-refactor-hakoagent  
**Date**: 2026-10-29  
**Status**: Draft

## Purpose

Dokumentasi validasi akhir ke akhir (end-to-end) yang membuktikan fitur HakoAgent bekerja sesuai spesifikasi dan konstitusi. Panduan ini berisi skenario yang dapat dijalankan, bukan kode implementasi lengkap.

## Prerequisites

- Rust toolchain terinstal (cargo, rustc)
- Hak izin tulis di working directory proyek
- HakoDB 0.19 tersedia sebagai dependency

## Setup Commands

```bash
# 1. Build HakoAgent core dan CLI
cargo build --release --manifest-path cli/Cargo.toml

# 2. Inisialisasi database HakoDB dan semua koleksi
./cli/target/release/hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

Expected output:
```
Speckit database initialized at: ./.hakoagent/hakoagent.db
Collections: ["sessions", "events", "decisions", "findings", "code_index", "tasks", "context_cache", "skills", "lessons_learned"]
```

## Test/Run Commands

### Test 1: Inisialisasi database (FR-002, FR-003)

```bash
./cli/target/release/hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

**Expected**: Semua 9 koleksi dibuat di `.hakoagent/hakoagent.db`:
- sessions, events, decisions, findings, code_index, tasks, context_cache, skills, lessons_learned

### Test 2: Catat event append-only (FR-004)

```bash
./cli/target/release/hakoagent events
```

**Expected**: Tampilkan histori event (kosong pada inisialisasi pertama). Setiap event baru ditambahkan dengan timestamp dan tidak dapat di-overwrite.

### Test 3: Ambil konteks dari memori (FR-007)

```bash
./cli/target/release/hakoagent recall "bagaimana implementasi error handling Rust?"
```

**Expected**: Mengembalikan konteks relevan dari `code_index` melalui HNSW + FTS dalam waktu target (< X detik).

### Test 4: Kelola skill dalam format Markdown (FR-005)

```bash
./cli/target/release/hakoagent skill list
./cli/target/release/hakoagent skill add "rust_error_handling"
```

**Expected**: Skill baru dibuat sebagai file Markdown di `.hakoagent/skills/`, bukan YAML atau JSON.

### Test 5: Buat dan selesaikan task dengan DoD (FR-006)

```bash
./cli/target/release/hakoagent task list
./cli/target/release/hakoagent task create "Implement error handling"
./cli/target/release/hakoagent task complete <task_id>
```

**Expected**: Task dibuat dengan target dan definition_of_done. Setelah selesai, status berubah menjadi "done" dan `dod_verified` = true.

### Test 6: Deteksi regresi dan file terlupakan (FR-008)

```bash
./cli/target/release/hakoagent vigilance
```

**Expected**: Laporan berisi file yang diubah tapi tidak diuji, TODO yang belum disentuh, dan pemeriksaan regresi terhadap prinsip konstitusi.

## Expected Outcomes (Success Criteria)

| SC | Target | Hasil yang Diharapkan |
|----|--------|----------------------|
| SC-001 | Siklus tugas lengkap < 30 detik | `init → recall → event_log → task_create → skill_add → task_complete` selesai dalam waktu target |
| SC-002 | 100% task selesai memiliki DoD | Setiap task yang ditandai "done" memiliki `dod_verified` = true |
| SC-003 | 0 referensi ke "hakoagent" | Tidak ada kata "hakoagent" di seluruh file sumber, dokumentasi, dan konfigurasi |
| SC-004 | 100% skill sebagai Markdown | Semua file di `.hakoagent/skills/` berekstensi `.md` |
| SC-005 | Event tidak dapat di-overwrite | Setiap event memiliki timestamp ISO 8601 dan tidak dapat ditimpa |
| SC-006 | Tool calling mudah ditemukan | Semua tool `hakoagent.<command>` dapat dipanggil tanpa konfigurasi kompleks |

## Validation Steps

1. Jalankan semua perintah Setup di atas
2. Jalankan Test 1 s.d. Test 6 secara berurutan
3. Verifikasi Expected Outcomes sesuai tabel di atas
4. Jika semua lulus, fitur dianggap siap untuk fase implementasi selanjutnya

## References

- Spesifikasi fitur: `spec.md`
- Model data: `data-model.md`
- Kontrak antarmuka: `contracts/tool-calling-interface.md`
- Konstitusi: `.specify/memory/constitution.md`
