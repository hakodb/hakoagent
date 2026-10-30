# Quickstart Validation Guide — Auto Codebase Indexing

**Feature**: 002-auto-code-indexing  
**Date**: 2026-10-29  
**Status**: Draft

## Purpose

Dokumentasi validasi akhir ke akhir (end-to-end) yang membuktikan fitur auto codebase indexing bekerja sesuai spesifikasi dan konstitusi HakoAgent. Panduan ini berisi skenario yang dapat dijalankan, bukan kode implementasi lengkap.

## Prerequisites

- Rust toolchain terinstal (cargo, rustc)
- Hak izin tulis di working directory proyek
- HakoDB 0.19 tersedia sebagai dependency
- HakoAgent sudah di-build

## Setup Commands

```bash
# 1. Build HakoAgent core dan CLI
cargo build --release --manifest-path cli/Cargo.toml

# 2. Inisialisasi database HakoDB dan semua koleksi
./cli/target/release/hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

Expected output:
```
HakoAgent database initialized at: ./.hakoagent/hakoagent.db
Collections: ["sessions", "events", "decisions", "findings", "code_index", "tasks", "context_cache", "skills", "lessons_learned"]
```

Background thread auto indexing akan secara otomatis memindai codebase setelah inisialisasi.

## Test/Run Commands

### Test 1: Startup auto indexing (FR-001)

```bash
# Pastikan database diinisialisasi
./cli/target/release/hakoagent init --db ./.hakoagent/hakoagent.db --collections all

# Buat file source code baru
echo "fn hello() { println!(\"hello\"); }" > src/hello.rs

# Tunggu background thread mendeteksi dan mengindex
# Verifikasi dengan recall
./cli/target/release/hakoagent recall "hello"
```

**Expected**: File `hello.rs` secara otomatis diindex dalam code_index tanpa agen memanggil `hakoagent index`. Hasil recall menampilkan symbol dari file tersebut.

### Test 2: Indexing inkremental (FR-002, SC-002)

```bash
# Ubah file yang sudah diindex
echo "fn hello() { println!(\"hello world\"); }" > src/hello.rs

# Tunggu background thread mendeteksi perubahan
# Verifikasi code_index diperbarui
./cli/target/release/hakoagent recall "hello world"
```

**Expected**: Hasil recall menampilkan isi yang diupdate. Waktu indexing satu file < 5 detik.

### Test 3: File dihapus (FR-006, SC-004)

```bash
# Hapus file
rm src/hello.rs

# Tunggu background thread mendeteksi penghapusan
# Verifikasi entri code_index dihapus
./cli/target/release/hakoagent recall "hello"
```

**Expected**: Hasil recall tidak lagi menampilkan symbol dari `hello.rs` karena file sudah dihapus.

### Test 4: Notifikasi indexing (FR-005, SC-005)

```bash
# Buat beberapa file baru
echo "fn foo() {}" > src/foo.rs
echo "fn bar() {}" > src/bar.rs

# Tunggu background thread selesai indexing
# Periksa notifikasi/events
./cli/target/release/hakoagent events
```

**Expected**: Agen menerima notifikasi ringkas tentang jumlah file yang diindex dan status sukses/error.

### Test 5: Direktori diabaikan (FR-004)

```bash
# Buat direktori yang harus diabaikan
mkdir -p target/debug
echo "fn ignored() {}" > target/debug/ignored.rs

# Verifikasi file di target/ tidak diindex
./cli/target/release/hakoagent recall "ignored"
```

**Expected**: File di `target/` tidak muncul dalam hasil recall.

## Expected Outcomes (Success Criteria)

| SC | Target | Hasil yang Diharapkan |
|----|--------|----------------------|
| SC-001 | Tidak perlu `hakoagent index` manual | Background thread otomatis mengindex saat startup dan perubahan |
| SC-002 | Indexing inkremental < 5 detik/file | Satu file yang diubah diindex dalam waktu < 5 detik |
| SC-003 | 100% file source terindex | Semua file .rs, .py, .js, .ts, .go dalam code_index |
| SC-004 | 0 entri untuk file dihapus | File yang dihapus tidak ada dalam code_index |
| SC-005 | Notifikasi setelah indexing | Events menunjukkan status indexing selesai |
| SC-006 | 0 referensi hakoagent | Tidak ada kata "hakoagent" di source/dokumentasi |

## Validation Steps

1. Jalankan semua perintah Setup di atas
2. Jalankan Test 1 s.d. Test 5 secara berurutan
3. Verifikasi Expected Outcomes sesuai tabel di atas
4. Jika semua lulus, fitur auto codebase indexing dianggap siap

## References

- Spesifikasi fitur: `spec.md`
- Model data: `data-model.md`
- Kontrak antarmuka: `contracts/auto-indexing-interface.md`
- Konstitusi: `.specify/memory/constitution.md`
