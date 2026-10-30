# Auto Indexing Interface Contract — HakoAgent

**Feature**: 002-auto-code-indexing  
**Date**: 2026-10-29  
**Status**: Draft

## Overview

Auto Codebase Indexing diekspos sebagai bagian dari tool calling interface HakoAgent. Background thread berjalan otomatis saat `hakoagent init` dieksekusi. Tidak ada CLI command khusus untuk auto indexing — semua terintegrasi ke dalam inisialisasi dan file system watcher.

## Tool List

| Tool | Deskripsi | Parameter Utama | Return |
|------|-----------|-----------------|--------|
| `hakoagent.init` | Inisialisasi database HakoDB dan memulai background thread auto indexing | `db_path` (string), `collections` (array of string) | `status` (string), `collections_created` (array), `indexing_started` (boolean) |
| `hakoagent.index` | Memaksa re-index seluruh codebase (manual override) | — | `indexing_run_id` (string), `status` (string) |
| `hakoagent.recall` | Ambil konteks dari memori (HNSW + FTS pada code_index) | `query` (string), `limit` (integer) | `context_results` (array) |
| `hakoagent.events` | Lihat histori kronologis termasuk indexing events | `limit` (integer), `session_id` (string) | `events_list` (array) |

## Response Format

Semua respons dalam format JSON:

```json
{
  "status": "success|error",
  "data": { ... },
  "error": null | { "code": "...", "message": "..." }
}
```

Contoh respons sukses `hakoagent.init`:
```json
{
  "status": "success",
  "data": {
    "collections_created": ["sessions", "events", "decisions", "findings", "code_index", "tasks", "context_cache", "skills", "lessons_learned"],
    "indexing_started": true
  },
  "error": null
}
```

Contoh respons sukses `hakoagent.recall`:
```json
{
  "status": "success",
  "data": {
    "context_results": [
      {
        "file_path": "src/error_handling.rs",
        "symbol_name": "handle_error",
        "symbol_type": "function",
        "relevance_score": 0.95
      }
    ]
  },
  "error": null
}
```

## Integration Notes

- Background thread dimulai otomatis saat `hakoagent.init` dieksekusi
- File system watcher memantau perubahan secara real-time
- Setiap indexing event dicatat ke koleksi `events` (append-only)
- Error pada satu file tidak menghentikan indexing file lainnya
- Notifikasi ringkas dikirim ke agen setelah setiap sesi indexing selesai

## Integration Example (Pseudocode)

```python
# Inisialisasi HakoAgent (background thread auto indexing mulai otomatis)
result = hakoagent.init(db_path="./.hakoagent/hakoagent.db", collections="all")
print(f"Indexing started: {result['data']['indexing_started']}")

# Agen bekerja, file berubah di background
# Background thread secara otomatis mendeteksi dan mengindex

# Ambil konteks dari code_index
context = hakoagent.recall(query="error handling pattern", limit=5)

# Lihat histori indexing
events = hakoagent.events(limit=10)
```
