# Research Findings — Refactor HakoAgent to Constitution

**Feature**: 001-refactor-hakoagent  
**Date**: 2026-10-29  
**Status**: Complete

## Unknowns Resolution

Tidak ada NEEDS CLARIFICATION yang tersisa. Semua parameter teknis telah diresolusi melalui spec dan clarifikasi sebelumnya:

| Unknown | Resolusi | Sumber |
|---------|----------|--------|
| Mekanisme append-only pada koleksi events | Application-level guard (kode memeriksa event_id sebelum tulis) | Clarification Session 2026-10-29 |
| Format skill | Markdown (`.md`) di `.hakoagent/skills/` | Constitution Section 4 + Spec FR-005 |
| Lokasi database HakoDB | `.hakoagent/hakoagent.db` | Constitution Section 3 |

## Technology Choices

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Rust 1.75+ sebagai bahasa core | HakoDB ditulis Rust, performa tinggi, memory safe, ekosistem mature | Python (lebih lambat untuk embedded DB), Go (cukup baik tapi Rust lebih alami untuk HakoDB FFI) |
| cbindgen untuk C ABI generation | Standar dalam ekosistem Rust, generate `hakodb.h` otomatis | Tulis C header manual (rentan error, sulit disinkronkan) |
| HakoDB embedded (`--no-default-features`) | Footprint ringan, tidak perlu server/daemon, cocok untuk in-process agent | SQLite (tidak ada dukungan vektor/graph native), PostgreSQL (butuh server) |
| Markdown untuk skill | Mudah dibaca manusia/agent, version control friendly, contoh kode dengan syntax highlighting | YAML (tidak cocok untuk contoh kode panjang), JSON (kurang readable) |
| Application-level append-only guard | Praktis untuk embedded DB, pesan error jelas, tidak memerlukan fitur khusus HakoDB | Database-level constraint (tidak tersedia di HakoDB 0.19), File-system immutable (tidak portabel) |

## Integration Patterns

- **Tool calling interface**: Setiap tool diexpose dengan nama `hakoagent.<command>`, parameter terdefinisi, return JSON
- **FFI/C ABI**: HakoDB shared library via cbindgen, wrapper Rust untuk bahasa host (Go, Python, JS/TS)
- **CLI**: Binary `hakoagent` dengan subcommands (init, index, recall, skill, task, events, vigilance)

## Best Practices

- Semua event ditulis append-only dengan timestamp ISO 8601
- Skill disimpan sebagai file Markdown terpisah untuk kemudahan editing dan version control
- Setiap task harus memiliki target dan definition_of_done yang terukur
- Tidak ada referensi ke tool eksternal (hakoagent) di seluruh kode dan dokumentasi
- Semua file terkait hakoagent berada di bawah `.hakoagent/` atau root proyek
