# Tool Calling Interface Contract — HakoAgent

**Feature**: 001-refactor-hakoagent  
**Date**: 2026-10-29  
**Status**: Draft

## Overview

HakoAgent mengekspos antarmuka tool calling untuk harness agent (OpenCode dan sejenisnya). Setiap tool memiliki nama yang diawali dengan `hakoagent.`, parameter yang terdefinisi dengan jelas, dan nilai kembali dalam format JSON untuk kemudahan parsing oleh agen.

## Tool List

| Tool | Deskripsi | Parameter Utama | Return |
|------|-----------|-----------------|--------|
| `hakoagent.init` | Inisialisasi database HakoDB dan semua koleksi | `db_path` (string), `collections` (array of string) | `status` (string), `collections_created` (array) |
| `hakoagent.index` | Scan dan index codebase ke `code_index` | `root_path` (string) | `indexed_count` (integer) |
| `hakoagent.recall` | Ambil konteks dari memori (HNSW + FTS) | `query` (string), `limit` (integer) | `context_results` (array) |
| `hakoagent.skill_list` | Lihat semua skill aktif dari `.hakoagent/skills/` | — | `skills_list` (array) |
| `hakoagent.skill_add` | Tambah skill baru dalam format Markdown | `name` (string), `content` (string) | `skill_id` (string), `status` (string) |
| `hakoagent.skill_get` | Ambil detail skill tertentu | `skill_id` (string) atau `name` (string) | `skill_content` (string, Markdown) |
| `hakoagent.task_list` | Lihat tugas dan status dari koleksi `tasks` | — | `tasks_list` (array) |
| `hakoagent.task_create` | Buat task baru dengan target + DoD | `title` (string), `target` (string), `definition_of_done` (string), `priority` (string) | `task_id` (string), `status` (string) |
| `hakoagent.task_complete` | Tandai task selesai dengan verifikasi DoD | `task_id` (string), `dod_verified` (boolean) | `status` (string), `completed_at` (string) |
| `hakoagent.events` | Lihat histori kronologis dari koleksi `events` | `limit` (integer), `session_id` (string) | `events_list` (array) |
| `hakoagent.event_log` | Catat tindakan baru ke koleksi `events` (append-only) | `action` (string), `target` (string), `actor` (string), `metadata` (JSON) | `event_id` (string), `timestamp` (string) |
| `hakoagent.vigilance` | Deteksi file terlupakan, regresi, TODO | `root_path` (string) | `vigilance_report` (object) |
| `hakoagent.finding_save` | Simpan temuan ke koleksi `findings` | `content` (string), `finding_type` (string), `file` (string) | `finding_id` (string) |
| `hakoagent.decision_save` | Simpan keputusan ke koleksi `decisions` | `title` (string), `rationale` (string), `consequences` (string) | `decision_id` (string) |

## Response Format

Semua respons dalam format JSON:

```json
{
  "status": "success|error",
  "data": { ... },
  "error": null | { "code": "...", "message": "..." }
}
```

Contoh respons sukses:
```json
{
  "status": "success",
  "data": { "event_id": "evt_001", "timestamp": "2026-10-29T08:05:00Z" },
  "error": null
}
```

Contoh respons error:
```json
{
  "status": "error",
  "data": null,
  "error": { "code": "APPEND_ONLY_VIOLATION", "message": "event_id already exists and cannot be overwritten" }
}
```

## Integration Notes

- Nama tool diawali dengan `hakoagent.` untuk menghindari konflik dengan tool lain di harness agent.
- Parameter harus diverifikasi tipe sebelum dieksekusi.
- Return value selalu terstruktur JSON agar mudah di-parse oleh agen AI.
- Semua operasi bersifat idempotent kecuali `event_log` (append-only, tidak dapat diulang dengan event_id yang sama).

## Integration Example (Pseudocode)

```python
# Sebelum mulai tugas
context = hakoagent.recall(query="bagaimana implementasi error handling Rust?", limit=5)
skills = hakoagent.skill_list()

# Selama bekerja - catat setiap tindakan
hakoagent.event_log(action="code_read", target="src/main.rs", actor="agent")

# Simpan temuan
hakoagent.finding_save(content="Polanya menggunakan Result<T, E>", finding_type="pattern", file="src/main.rs")

# Setelah selesai tugas - ekstraksi skill
hakoagent.skill_add(name="rust_error_handling", content="...markdown content...")

# Tandai task selesai
hakoagent.task_complete(task_id="task_001", dod_verified=True)
```
