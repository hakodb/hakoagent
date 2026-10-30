# Research Findings — Auto Codebase Indexing

**Feature**: 003-cache-graph-system  
**Date**: 2026-10-29  
**Status**: Complete

## Unknowns Resolution

Tidak ada NEEDS CLARIFICATION yang tersisa. Semua parameter telah ditentukan melalui spec dan clarifikasi sebelumnya:

| Unknown | Resolusi | Sumber |
|---------|----------|--------|
| Default TTL untuk cache konteks | 300 detik (5 menit) | Clarification Session 2026-10-29 |

## Technology Choices

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Python 3 (stdlib only) sebagai bahasa implementasi | Tidak ada build step, mudah dipelihara, kompatibel dengan ctypes FFI ke HakoDB | Rust (memerlukan cargo build, toolchain eksternal) |
| Prebuilt HakoDB shared library (`libhakodb-...so`) via ctypes | Library asli HakoDB digunakan langsung, header `hakodb.h` sebagai referensi ABI | Build dari sumber dengan Rust/cargo (memerlukan toolchain Rust) |
| HakoDB embedded (via prebuilt .so) | Footprint ringan, tidak perlu server/daemon, cocok untuk in-process agent | SQLite (tidak ada dukungan vektor/graph native), PostgreSQL (butuh server) |
| LRU eviction untuk cache | Standar untuk cache management, efisien memori | FIFO (lebih sederhana tapi kurang optimal), LFU (lebih kompleks) |
| BFS untuk graph traversal | Cocok untuk eksplorasi dependensi level-by-level | DFS (lebih dalam tapi bisa terjebak dalam cabang yang salah) |
| Dijkstra untuk shortest path | Standar untuk weighted shortest path | BFS (hanya untuk unweighted), A* (perlu heuristic) |
| Manual indexing (`hakoagent index`) | Sederhana, tidak perlu manajemen proses tambahan | Background thread / file watcher (memerlukan manajemen proses, lebih kompleks) |

## Integration Patterns

- **FFI via ctypes**: Memuat `libhakodb-...so` dan memanggil fungsi C ABI seperti `hk_engine_insert_json`, `hk_engine_get_json`, `hk_engine_delete`
- **Header referensi**: `lib/hakodb.h` (v0.20.0, hash-verified) sebagai sumber kebenaran untuk tanda tangan fungsi C
- **HakoDB integration**: Memory Service untuk baca/tulis koleksi `context_cache`, `code_index` melalui FFI atau JSON file
- **CLI integration**: `./hakoagent init` untuk inisialisasi database, `./hakoagent index` untuk scanning codebase

## Best Practices

- Setiap file yang diindex dicatat sebagai event append-only di koleksi `events`
- File hash digunakan untuk mendeteksi perubahan (hindari re-index file yang sama)
- Direktori yang diabaikan: node_modules, .git, target, .hakoagent, build output
- Error pada satu file tidak menghentikan indexing file lainnya
- Notifikasi ringkas dikirim ke agen setelah setiap sesi indexing selesai
- Cache TTL 300 detik untuk keseimbangan antara freshness dan pengurangan panggilan LLM
- Graph traversal dengan visited set untuk menghindari siklus tak terbatas
