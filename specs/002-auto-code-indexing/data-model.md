# Data Model — Auto Codebase Indexing

**Feature**: 002-auto-code-indexing  
**Date**: 2026-10-29  
**Status**: Draft

## Entities

### CodeIndexEntry

Entri indeks kode yang disimpan di koleksi `code_index` HakoDB.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| entry_id | string | ID unik entri | Harus unik |
| file_path | string | Path file relatif dari root proyek | Tidak boleh kosong |
| symbol_name | string | Nama simbol (fungsi, class, struct, dll.) | Tidak boleh kosong |
| symbol_type | string | Tipe simbol (function, struct, trait, module, class, method, dll.) | Tidak boleh kosong |
| dependensi | array of string | Daftar dependensi yang diimpor/dipakai | Harus berupa array |
| line_number | integer | Nomor baris definisi simbol | Boleh null |
| last_indexed_at | string (ISO 8601) | Waktu terakhir file diindex | Format ISO 8601 |
| file_hash | string | Hash SHA-256 dari isi file | Tidak boleh kosong, unik per file_path |

**Constraint**: file_hash digunakan untuk mendeteksi perubahan. Jika hash sama, file tidak perlu di-reindex.

### FileChange

Catatan perubahan file yang terdeteksi oleh file system watcher.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| change_id | string | ID unik perubahan | Harus unik |
| file_path | string | Path file yang berubah | Tidak boleh kosong |
| change_type | string | Tipe perubahan (created/modified/deleted) | Harus salah satu dari nilai yang valid |
| timestamp | string (ISO 8601) | Waktu perubahan terdeteksi | Format ISO 8601 |
| indexed_status | string | Status indexing (indexed/skipped/error) | Harus salah satu dari nilai yang valid |

**State transitions**: detected → indexed / skipped / error

### IndexingRun

Catatan sesi indexing yang dilakukan background thread.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| run_id | string | ID unik sesi indexing | Harus unik |
| started_at | string (ISO 8601) | Waktu indexing dimulai | Format ISO 8601 |
| ended_at | string (ISO 8601) | Waktu indexing selesai | Format ISO 8601, boleh null |
| files_processed | integer | Jumlah file yang diproses | Harus >= 0 |
| files_indexed | integer | Jumlah file yang berhasil diindex | Harus >= 0, <= files_processed |
| errors | array of string | Daftar error yang terjadi | Harus berupa array |
| status | string | Status (started/completed/failed) | Harus salah satu dari nilai yang valid |

**State transitions**: started → completed / failed

## Relationships

- IndexingRun 1:N FileChange (satu sesi indexing dapat memiliki banyak perubahan file)
- FileChange N:1 CodeIndexEntry (satu perubahan file dapat menghasilkan/update satu entri code_index)

## Validation Rules

1. **File hash uniqueness**: file_hash harus unik per file_path. Jika file_path sudah ada dengan hash yang sama, tidak perlu di-reindex.
2. **Change type validity**: change_type harus salah satu dari created/modified/deleted.
3. **Indexing status validity**: indexed_status harus salah satu dari indexed/skipped/error.
4. **Required fields**: Semua field yang tidak boleh kosong harus diisi saat create.

## State Transitions

| Entity | From | To | Condition |
|--------|------|-----|-----------|
| IndexingRun | started | completed | Semua file diproses tanpa error fatal |
| IndexingRun | started | failed | Error fatal mencegah lanjutkan indexing |
| FileChange | detected | indexed | File berhasil diindex ke code_index |
| FileChange | detected | skipped | File dilewati (ekstensi tidak didukung, direktori diabaikan, terlalu besar) |
| FileChange | detected | error | Error saat memproses file |
| CodeIndexEntry | created | updated | File diubah, hash berbeda |
| CodeIndexEntry | updated | deleted | File dihapus dari repository |
