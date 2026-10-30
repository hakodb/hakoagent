# Feature Specification: Auto Codebase Indexing

**Feature Branch**: `002-auto-code-indexing`

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "auto codebase indexing tanpa agent manual indexing"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agen tidak perlu memulai indexing secara manual (Priority: P1)

Sistem secara otomatis mendeteksi perubahan codebase dan menjalankan indexing tanpa perlu agen memanggil perintah `hakoagent index` secara manual. Indexing terjadi secara inkremental setiap kali ada file yang ditambahkan, diubah, atau dihapus.

**Why this priority**: Ini adalah inti fitur auto indexing — mengurangi beban agen dan memastikan code_index selalu up-to-date tanpa intervensi manual.

**Independent Test**: Dapat diuji secara independen dengan memodifikasi file di repository lalu memverifikasi bahwa code_index telah diperbarui secara otomatis tanpa agen memanggil perintah index.

**Acceptance Scenarios**:

1. **Given** sistem sudah diinisialisasi, **When** agen membuat file baru di repository, **Then** file baru tersebut secara otomatis diindex dalam code_index tanpa agen memanggil `hakoagent index`
2. **Given** sistem sudah diinisialisasi, **When** agen mengubah file yang sudah ada, **Then** entri code_index untuk file tersebut diperbarui secara otomatis
3. **Given** sistem sudah diinisialisasi, **When** agen menghapus file dari repository, **Then** entri code_index untuk file tersebut dihapus secara otomatis

---

### User Story 2 - Indexing inkremental tanpa memproses ulang seluruh codebase (Priority: P2)

Sistem hanya memproses file yang berubah sejak indexing terakhir, bukan seluruh codebase dari awal. Ini menjaga performa tetap baik meski codebase besar.

**Why this priority**: Penting untuk skalabilitas — codebase besar tidak boleh menyebabkan indexing lambat setiap kali ada perubahan kecil.

**Independent Test**: Dapat diuji dengan mengukur waktu indexing untuk satu file yang diubah dibandingkan indexing seluruh codebase.

**Acceptance Scenarios**:

1. **Given** codebase sudah diindex sebelumnya, **When** satu file diubah, **Then** waktu indexing untuk satu file jauh lebih cepat dari re-index seluruh codebase
2. **Given** banyak file diubah sekaligus, **Then** hanya file-file yang berubah yang diproses, bukan seluruh codebase

---

### User Story 3 - Agen mendapat notifikasi saat indexing selesai (Priority: P3)

Setiap kali indexing otomatis selesai, agen mendapat notifikasi ringkas tentang apa yang diindex dan apakah ada error.

**Why this priority**: Memberi agen visibilitas ke status code_index tanpa perlu memeriksa secara manual.

**Independent Test**: Dapat diuji dengan memicu perubahan file lalu memverifikasi bahwa notifikasi indexing muncul.

**Acceptance Scenarios**:

1. **Given** indexing otomatis berjalan, **When** indexing selesai, **Then** agen menerima notifikasi ringkas (jumlah file diindex, status sukses/error)
2. **Given** indexing gagal pada satu file, **Then** agen mendapat notifikasi error untuk file tersebut tanpa menghentikan indexing file lainnya

---

### Edge Cases

- File dengan ekstensi yang tidak didukung (bukan source code) → dilewati saat indexing
- File yang terlalu besar → dilewati atau diindex sebagian
- Direktori yang harus diabaikan (node_modules, .git, target, dll.) → tidak diindex
- Koneksi terputus saat indexing berjalan → indexing dilanjutkan dari titik terbaru saat kembali online
- File dengan karakter khusus dalam nama → tetap diindex dengan aman

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistem MUST secara otomatis mendeteksi perubahan file di repository tanpa agen memanggil perintah index secara manual. Saat sesi startup, scanning codebase dijalankan sebagai background thread dalam proses agen yang sama (tidak perlu proses terpisah). Jika database belum ada, scanning dilakukan penuh; jika sudah ada, diverifikasi dan diperbarui hanya file yang berubah.
- **FR-002**: Sistem MUST melakukan indexing inkremental — hanya memproses file yang berubah sejak indexing terakhir
- **FR-003**: Sistem MUST menyimpan hasil indexing ke koleksi `code_index` di HakoDB
- **FR-004**: Sistem MUST mengabaikan direktori dan file yang tidak relevan (node_modules, .git, target, build output, dll.)
- **FR-005**: Sistem MUST memberi notifikasi kepada agen saat indexing otomatis selesai atau gagal
- **FR-006**: Sistem MUST menangani file yang dihapus dengan menghapus entri code_index terkait
- **FR-007**: Sistem MUST menangani file baru dengan membuat entri code_index baru
- **FR-008**: Sistem MUST menangani file yang diubah dengan memperbarui entri code_index existing
- **FR-009**: Sistem MUST tidak memiliki referensi ke tool eksternal seperti hakoagent di seluruh kode dan dokumentasi
- **FR-010**: Sistem MUST menyimpan semua file terkait hakoagent di bawah direktori `.hakoagent/` atau root proyek

### Key Entities *(include if feature involves data)*

- **CodeIndexEntry**: Entri indeks kode dengan entry_id, file_path, symbol_name, symbol_type, dependensi, line_number, last_indexed_at, file_hash
- **FileChange**: Catatan perubahan file dengan change_id, file_path, change_type (created/modified/deleted), timestamp, indexed_status
- **IndexingRun**: Catatan sesi indexing dengan run_id, started_at, ended_at, files_processed, files_indexed, errors, status

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Agen tidak perlu memanggil `hakoagent index` secara manual untuk menjaga code_index up-to-date
- **SC-002**: Waktu indexing inkremental untuk satu file yang diubah < 5 detik
- **SC-003**: 100% file source code yang relevan terindex dalam code_index
- **SC-004**: 0 entri code_index untuk file yang telah dihapus dari repository
- **SC-005**: Agen menerima notifikasi setelah setiap sesi indexing otomatis selesai
- **SC-006**: 0 referensi ke "hakoagent" ditemukan di seluruh file sumber, dokumentasi, dan konfigurasi proyek

## Assumptions

- File system watcher tersedia di platform target (Linux, macOS, Windows)
- Agen memiliki izin untuk membaca file di repository
- Database HakoDB sudah diinisialisasi sebelum indexing otomatis berjalan
- Format file yang didukung adalah source code (Rust, Python, JavaScript, TypeScript, Go, dll.)

## Clarifications

### Session 2026-10-29

- Q: Saat sesi startup, apakah scanning codebase dijalankan sebagai proses terpisah di background, atau sebagai thread dalam proses agen yang sama? → A: Background thread dalam proses agen yang sama

---
