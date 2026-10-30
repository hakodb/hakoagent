# Data Model — Refactor HakoAgent to Constitution

**Feature**: 001-refactor-hakoagent  
**Date**: 2026-10-29  
**Status**: Draft

## Entities

### Event

Tindakan agen yang dicatat secara kronologis di koleksi `events`.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| event_id | string | ID unik event | Harus unik, tidak boleh di-overwrite |
| timestamp | string (ISO 8601) | Waktu event terjadi | Format ISO 8601 |
| session_id | string | Referensi ke sesi | Harus sesuai session_id yang valid |
| actor | string | Pelaku tindakan (contoh: "hakoagent") | Tidak boleh kosong |
| action | string | Jenis tindakan (contoh: "code_read", "task_complete") | Tidak boleh kosong |
| target | string | Target tindakan (contoh: file path, collection) | Tidak boleh kosong |
| change_type | string | Tipe perubahan (contoh: "read", "write", "delete") | Tidak boleh kosong |
| metadata | JSON | Data tambahan opsional | Boleh kosong |

**Constraint**: Append-only. event_id tidak dapat di-overwrite. Sistem memeriksa keberadaan event_id sebelum menulis (application-level guard).

### Session

Riwayat sesi agent di koleksi `sessions`.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| session_id | string | ID unik sesi | Harus unik |
| started_at | string (ISO 8601) | Waktu sesi dimulai | Format ISO 8601 |
| ended_at | string (ISO 8601) | Waktu sesi selesai | Format ISO 8601, boleh null |
| summary | string | Ringkasan sesi | Boleh kosong |
| status | string | Status sesi (contoh: "active", "completed") | Tidak boleh kosong |
| model_used | string | Model LLM yang digunakan | Boleh null |
| task_ids | array of string | Daftar task_id dalam sesi | Harus berupa array |

### Task

Tugas yang dikerjakan agent di koleksi `tasks`.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| task_id | string | ID unik tugas | Harus unik |
| title | string | Judul tugas | Tidak boleh kosong |
| description | string | Deskripsi tugas | Tidak boleh kosong |
| target | string | Target tujuan tugas | Tidak boleh kosong (Clear Target) |
| definition_of_done | string | Kriteria selesai yang terukur | Tidak boleh kosong (Clear Target) |
| priority | string | Prioritas (P1, P2, P3) | Harus salah satu dari P1/P2/P3 |
| status | string | Status (todo, in-progress, done, blocked) | Harus salah satu dari nilai yang valid |
| story_id | string | Referensi ke user story | Boleh null |
| dependencies | array of string | Daftar task_id yang menjadi dependensi | Harus berupa array |
| created_at | string (ISO 8601) | Waktu task dibuat | Format ISO 8601 |
| completed_at | string (ISO 8601) | Waktu task selesai | Format ISO 8601, boleh null |
| dod_verified | boolean | Apakah DoD telah diverifikasi | Default false |
| model_used | string | Model LLM yang digunakan | Boleh null |

**State transitions**: todo → in-progress → done (jika dod_verified=true) / blocked

### Skill

Pola sukses diekstrak dari tugas, disimpan sebagai file Markdown di `.hakoagent/skills/`.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| skill_id | string | ID unik skill | Harus unik |
| name | string | Nama skill | Tidak boleh kosong |
| description | string | Deskripsi skill | Tidak boleh kosong |
| context_tags | array of string | Tag konteks untuk pencarian | Harus berupa array |
| success_count | integer | Jumlah kesuksesan | Default 0 |
| failure_count | integer | Jumlah kegagalan | Default 0 |
| last_used | string (ISO 8601) | Waktu terakhir digunakan | Boleh null |
| example_code | string | Contoh kode | Boleh null |
| status | string | Status (active, deprecated, archived) | Harus salah satu dari nilai yang valid |

**Format**: File Markdown (`.md`), bukan YAML atau JSON.

### Finding

Temuan codebase di koleksi `findings`.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| finding_id | string | ID unik temuan | Harus unik |
| collection | string | Koleksi tempat temuan ditemukan | Tidak boleh kosong |
| content | string | Isi temuan | Tidak boleh kosong |
| finding_type | string | Tipe temuan (bug, pattern, error, note) | Tidak boleh kosong |
| file | string | File terkait | Boleh null |
| event_id | string | Referensi ke event asal | Boleh null |

### Decision

Keputusan arsitektur di koleksi `decisions`.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| decision_id | string | ID unik keputusan | Harus unik |
| title | string | Judul keputusan | Tidak boleh kosong |
| rationale | string | Alasan keputusan | Tidak boleh kosong |
| consequences | string | Konsekuensi keputusan | Tidak boleh kosong |
| event_id | string | Referensi ke event asal | Boleh null |
| status | string | Status (active, superseded) | Harus salah satu dari nilai yang valid |

### CodeIndex

Entri indeks kode di koleksi `code_index`.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| entry_id | string | ID unik entri | Harus unik |
| file_path | string | Path file | Tidak boleh kosong |
| symbol_name | string | Nama simbol | Tidak boleh kosong |
| symbol_type | string | Tipe simbol (function, struct, trait, module, dll.) | Tidak boleh kosong |
| dependencies | array of string | Daftar dependensi | Harus berupa array |
| line_number | integer | Nomor baris | Boleh null |

### ContextCacheEntry

Entri cache konteks di koleksi `context_cache`.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| cache_key | string | Kunci cache unik | Harus unik |
| query | string | Query asli | Tidak boleh kosong |
| summary | string | Ringkasan hasil pencarian | Tidak boleh kosong |
| source_documents | array of string | Daftar dokumen sumber | Harus berupa array |
| created_at | string (ISO 8601) | Waktu entri dibuat | Format ISO 8601 |
| ttl_seconds | integer | Waktu kadaluwarsa dalam detik | Harus > 0 |
| hit_count | integer | Jumlah kali diakses | Default 0 |

### Lesson

Pelajaran dari kegagalan di koleksi `lessons_learned`.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| lesson_id | string | ID unik pelajaran | Harus unik |
| title | string | Judul pelajaran | Tidak boleh kosong |
| description | string | Deskripsi pelajaran | Tidak boleh kosong |
| failure_context | string | Konteks kegagalan | Tidak boleh kosong |
| remediation | string | Tindak lanjut perbaikan | Tidak boleh kosong |
| tags | array of string | Tag pelajaran | Harus berupa array |
| status | string | Status (active, resolved) | Harus salah satu dari nilai yang valid |

## Relationships

- Session 1:N Event (satu sesi dapat memiliki banyak event)
- Task N:1 Session (satu task terkait satu sesi)
- Event N:1 Session (satu event terkait satu sesi)
- Finding N:1 Event (satu finding merujuk satu event asal)
- Decision N:1 Event (satu decision merujuk satu event asal)

## Validation Rules

1. **Event append-only**: Sebelum menulis event, sistem memeriksa apakah event_id sudah ada. Jika ada, operasi ditolak dengan error.
2. **Task completeness**: Task tidak dapat ditandai selesai jika `definition_of_done` kosong atau `dod_verified` false.
3. **Skill uniqueness**: skill_id harus unik dalam direktori `.hakoagent/skills/`.
4. **Required fields**: Semua field yang ditandai "Tidak boleh kosong" harus diisi saat create.

## State Transitions

| Entity | From | To | Condition |
|--------|------|-----|-----------|
| Task | todo | in-progress | Agent mulai bekerja pada task |
| Task | in-progress | done | Task selesai dan dod_verified=true |
| Task | in-progress | blocked | Task terhalang oleh dependensi atau masalah |
| Skill | active | deprecated | Skill tidak lagi direkomendasikan |
| Skill | deprecated | archived | Skill tidak digunakan dalam jangka waktu tertentu |
| Skill | active | archived | Skill langsung diarsipkan (tidak relevan lagi) |
