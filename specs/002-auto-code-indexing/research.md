# Research Findings — Auto Codebase Indexing

**Feature**: 002-auto-code-indexing  
**Date**: 2026-10-29  
**Status**: Complete

## Unknowns Resolution

Tidak ada NEEDS CLARIFICATION yang tersisa. Semua parameter telah diresolusi melalui spec dan clarifikasi sebelumnya:

| Unknown | Resolusi | Sumber |
|---------|----------|--------|
| Mekanisme startup scanning | Background thread dalam proses agen (tidak proses terpisah) | Clarification Session 2026-10-29 |
| Database belum ada vs sudah ada | Full scan jika belum ada, verifikasi + update jika sudah ada | Spec FR-001 |

## Technology Choices

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Rust 1.75+ sebagai bahasa core | HakoDB ditulis Rust, kompatibilitas FFI alami, performa tinggi | Python (lebih lambat untuk file system watcher) |
| notify crate untuk file system watching | Cross-platform (Linux inotify, macOS FSEvents, Windows ReadDirectoryChangesW), mature | Custom polling (lebih banyak resource), platform-specific API (tidak portable) |
| walkdir untuk directory traversal | Rekursif, bisa filter direktori, mature di Rust ecosystem | Manual recursion (rentan error), std::fs::read_dir (tidak rekursif) |
| HakoDB embedded (`--no-default-features`) | Footprint ringan, tidak perlu server/daemon, cocok untuk in-process agent | SQLite (tidak ada dukungan vektor/graph native), PostgreSQL (butuh server) |
| Background thread dalam proses agen | Sederhana, tidak perlu manajemen proses tambahan, berbagi memori dengan agen | Subprocess terpisah (memerlukan IPC, lebih kompleks) |

## Integration Patterns

- **File system watching**: notify crate memantau perubahan file secara real-time
- **Background thread**: std::thread::spawn untuk scanning startup dan watcher loop
- **HakoDB integration**: Memory Service untuk baca/tulis koleksi `code_index`
- **CLI integration**: `hakoagent init` memulai background thread otomatis

## Best Practices

- Setiap file yang diindex dicatat sebagai event append-only di koleksi `events`
- File hash digunakan untuk mendeteksi perubahan (hindari re-index file yang sama)
- Direktori yang diabaikan: node_modules, .git, target, .hakoagent, build output
- Error pada satu file tidak menghentikan indexing file lainnya
- Notifikasi ringkas dikirim ke agen setelah setiap sesi indexing selesai
