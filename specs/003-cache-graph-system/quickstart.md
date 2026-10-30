# Quickstart Validation Guide — System Caching dan Graph Traversal

**Feature**: 003-cache-graph-system  
**Date**: 2026-10-29  
**Status**: Draft

## Purpose

Dokumentasi validasi akhir ke akhir (end-to-end) yang membuktikan fitur caching dan graph traversal bekerja sesuai spesifikasi dan konstitusi HakoAgent. Panduan ini berisi skenario yang dapat dijalankan, bukan kode implementasi lengkap.

## Prerequisites

- Python 3 (stdlib only, no external dependencies)
- Hak izin tulis di working directory proyek
- Prebuilt HakoDB library tersedia di `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` + header `lib/hakodb.h`
- Codebase sudah diindex melalui `hakoagent index`

## Setup Commands

```bash
# 1. Inisialisasi database HakoDB dan semua koleksi
./hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

Expected output:
```
HakoAgent database initialized at: ./.hakoagent/hakoagent.db
Collections: ["sessions", "events", "decisions", "findings", "code_index", "tasks", "context_cache", "skills", "lessons_learned"]
```

Jalankan `./hakoagent index` untuk memindai codebase dan membangun `code_index`.

## Test/Run Commands

### Test 1: Cache miss dan store (FR-001, FR-002)

```bash
# Pertama kali query - harus memanggil endpoint LLM
./hakoagent recall "bagaimana implementasi error handling Python?"

# Kedua kali query yang sama - harus dari cache
./hakoagent recall "bagaimana implementasi error handling Python?"

# Lihat statistik cache
./hakoagent cache stats
```

**Expected**:
- Query pertama: panggilan endpoint LLM, hasil disimpan ke cache
- Query kedua: cache hit, tidak ada panggilan endpoint LLM
- `./hakoagent cache stats`: menampilkan total_hits ≥ 1, total_misses ≥ 1

### Test 2: Cache expiry (FR-001, SC-004)

```bash
# Tunggu hingga TTL habis (5 menit) atau manipulasi TTL untuk testing
./hakoagent recall "bagaimana implementasi error handling Python?"
```

**Expected**: Setelah TTL habis, sistem memanggil endpoint LLM lagi dan memperbarui cache.

### Test 3: Graph traversal BFS (FR-003, FR-007)

```bash
# Traversal dari simbol ke arah in (siapa yang memanggil)
./hakoagent graph traverse validate_input in 2
```

**Expected**: Mengembalikan semua node yang dapat dijangkau dari `validate_input` dalam depth 2, tanpa siklus tak terbatas.

### Test 4: Shortest path Dijkstra (FR-004)

```bash
# Cari jalur terpendek dari main ke error_handler
./hakoagent graph shortest-path main error_handler
```

**Expected**: Mengembalikan rantai dependensi terpendek dari `main` ke `error_handler`.

### Test 5: Dependents lookup (FR-005, FR-006)

```bash
# Lihat siapa yang menggunakan file utils.rs
./hakoagent graph dependents src/utils.rs

# Lihat apa saja yang dipanggil oleh file utils.rs
./hakoagent graph dependents-reverse src/utils.rs
```

**Expected**: Mengembalikan daftar node yang bergantung pada `src/utils.rs` dan node yang dipanggil oleh `src/utils.rs`.

### Test 6: Notifikasi indexing (FR-008, SC-005)

```bash
# Lihat histori event termasuk caching dan traversal
./hakoagent events
```

**Expected**: Agen menerima notifikasi ringkas tentang jumlah file yang diindex, status sukses/error.

## Expected Outcomes (Success Criteria)

| SC | Target | Hasil yang Diharapkan |
|----|--------|----------------------|
| SC-001 | Cache hit ratio ≥ 50% | Query yang diulang ≥ 50% dari cache |
| SC-002 | Waktu ambil konteks < 100ms (cache hit) | Cache hit response < 100ms |
| SC-003 | Graph traversal depth ≤ 10 | Traversal tidak melebihi depth 10 tanpa degradasi |
| SC-004 | 0 entri cache expired | Tidak ada entri expired yang masih digunakan |
| SC-005 | 0 referensi ke "hakoagent" | Tidak ada kata "hakoagent" di source/dokumentasi |
| SC-006 | Semua file di `.hakoagent/` atau root | Semua file terkait hakoagent di lokasi yang benar |

## Validation Steps

1. Jalankan semua perintah Setup di atas
2. Jalankan Test 1 s.d. Test 6 secara berurutan
3. Verifikasi Expected Outcomes sesuai tabel di atas
4. Jika semua lulus, fitur caching dan graph traversal dianggap siap

## References

- Spesifikasi fitur: `spec.md`
- Model data: `data-model.md`
- Kontrak antarmuka: `contracts/cache-graph-interface.md`
- Konstitusi: `.specify/memory/constitution.md`
