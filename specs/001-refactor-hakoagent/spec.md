# Feature Specification: Refactor HakoAgent to Constitution

**Feature Branch**: `001-refactor-hakoagent`

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "refactor hakoagent sesuai konstitusi terbaru"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agen menggunakan tool calling HakoAgent untuk mengelola memori dan skill (Priority: P1)

Agen AI dalam harness (OpenCode) dapat memanggil tool HakoAgent untuk menyimpan event, mencari konteks, membuat task, dan mengelola skill dalam format Markdown, semuanya melalui antarmuka yang konsisten dan terukur.

**Why this priority**: Ini adalah inti dari konstitusi — agen harus mampu berinteraksi dengan memori HakoDB dan skill melalui tool calling yang mudah digunakan, tanpa referensi ke tool eksternal seperti hakoagent.

**Independent Test**: Dapat diuji secara independen dengan memanggil setiap tool HakoAgent (init, recall, event_log, skill_add, task_create, dll.) dan memverifikasi bahwa file di `.hakoagent/` dibuat atau diperbarui dengan benar.

**Acceptance Scenarios**:

1. **Given** direktori `.hakoagent/` belum ada, **When** agen memanggil `hakoagent.init`, **Then** direktori `.hakoagent/` dan database `hakoagent.db` dibuat dengan semua 9 koleksi
2. **Given** agen telah menyelesaikan tugas, **When** agen memanggil `hakoagent.event_log` dengan action dan target, **Then** event ditambahkan ke koleksi `events` dengan timestamp dan tidak dapat di-overwrite
3. **Given** ada skill baru yang diekstrak dari tugas, **When** agen memanggil `hakoagent.skill_add` dengan konten Markdown, **Then** file skill baru dibuat di `.hakoagent/skills/` dengan format Markdown
4. **Given** agen ingin mencari konteks, **When** agen memanggil `hakoagent.recall` dengan query, **Then** hasil konteks relevan dikembalikan dalam waktu target

---

### User Story 2 - Agen menyimpan dan mengambil skill dalam format Markdown (Priority: P2)

Setiap pola sukses atau pelajaran dari tugas disimpan sebagai file skill Markdown di `.hakoagent/skills/`, dapat dicari, dan di-reuse untuk tugas serupa di masa depan.

**Why this priority**: Prinsip Self Skill Improvement memerlukan penyimpanan skill yang mudah dibaca, diedit, dan di-version control. Markdown dipilih karena tidak perlu parser khusus.

**Independent Test**: Dapat diuji dengan membuat file skill Markdown, lalu mencarinya melalui `hakoagent.skill_list` atau `hakoagent.skill_get`, dan memverifikasi konten yang dikembalikan.

**Acceptance Scenarios**:

1. **Given** agen mengekstrak pola sukses dari tugas, **When** agen menyimpan skill sebagai file Markdown di `.hakoagent/skills/`, **Then** file memiliki metadata (skill_id, name, status, tags, success_count, failure_count) dan contoh kode
2. **Given** ada beberapa skill aktif, **When** agen memanggil `hakoagent.skill_list`, **Then** semua skill aktif ditampilkan dengan nama dan jumlah kesuksesan/kegagalan
3. **Given** skill tertentu dibutuhkan, **When** agen memanggil `hakoagent.skill_get` dengan skill_id, **Then** konten lengkap skill dalam format Markdown dikembalikan

---

### User Story 3 - Agen melacak task dengan target dan DoD yang terukur (Priority: P2)

Setiap tugas yang dikerjakan agen memiliki target dan Definition of Done yang dicatat di koleksi `tasks`, sehingga progres dapat diverifikasi dan konsisten lintas model LLM.

**Why this priority**: Prinsip Clear Target memastikan setiap tugas memiliki tujuan yang terukur dan tidak ambigu, mendukung konsistensi lintas model.

**Independent Test**: Dapat diuji dengan membuat task baru via `hakoagent.task_create`, lalu memverifikasi via `hakoagent.task_list` bahwa target dan DoD tercatat dengan benar.

**Acceptance Scenarios**:

1. **Given** agen akan mulai tugas baru, **When** agen memanggil `hakoagent.task_create` dengan title, target, dan definition_of_done, **Then** task baru dibuat di koleksi `tasks` dengan status "todo"
2. **Given** task telah selesai, **When** agen memanggil `hakoagent.task_complete` dengan dod_verified=true, **Then** status task berubah menjadi "done" dan tanggal selesai dicatat
3. **Given** ada task yang belum selesai, **When** agen memanggil `hakoagent.task_list`, **Then** semua task dengan status "todo" atau "in-progress" ditampilkan

---

### User Story 4 - Agen mendeteksi regresi dan file terlupakan (Priority: P3)

Vigilance Checker secara otomatis mendeteksi file yang diubah tapi tidak diuji, TODO yang belum disentuh, dan regresi terhadap prinsip konstitusi.

**Why this priority**: Prinsip Vigilance membantu menjaga kualitas kode dan kepatuhan konstitusi tanpa intervensi manual yang berlebihan.

**Independent Test**: Dapat diuji dengan menjalankan `hakoagent.vigilance` pada direktori proyek dan memverifikasi laporan yang dihasilkan.

**Acceptance Scenarios**:

1. **Given** ada file yang diubah tapi tidak ada test yang sesuai, **When** agen menjalankan `hakoagent.vigilance`, **Then** file tersebut terdaftar dalam laporan unused files
2. **Given** ada komentar TODO atau FIXME di source code, **When** agen menjalankan `hakoagent.vigilance`, **Then** semua item TODO terdaftar dengan lokasi file dan baris
3. **Given** konstitusi ada di `.specify/memory/constitution.md`, **When** agen menjalankan `hakoagent.vigilance`, **Then** pemeriksaan regresi terhadap prinsip konstitusi dilaporkan (misal: apakah konstitusi masih ada, koleksi events tersedia)

---

### Edge Cases

- Agen memanggil tool dengan parameter yang kosong atau invalid → sistem mengembalikan error pesan yang jelas
- Database HakoDB sudah ada dari inisialisasi sebelumnya → inisialisasi tidak menimpa data yang ada
- Skill dengan nama yang sama sudah ada → sistem memberikan peringatan atau menambahkan suffix
- Direktori `.hakoagent/` tidak writable → error izin file yang jelas
- Query recall tidak cocok dengan dokumen apapun → hasil kosong dengan pesan yang informatif

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistem MUST menyediakan antarmuka tool calling untuk agen harness dengan nama yang diawali `hakoagent.`
- **FR-002**: Sistem MUST menyimpan semua data memori dalam database HakoDB tunggal di `.hakoagent/hakoagent.db`
- **FR-003**: Sistem MUST memiliki 9 koleksi: sessions, events, decisions, findings, code_index, tasks, context_cache, skills, lessons_learned
- **FR-004**: Sistem MUST menyimpan setiap tindakan agen sebagai event append-only di koleksi `events` dengan timestamp. Penegakan append-only dilakukan pada tingkat aplikasi: sistem memeriksa apakah `event_id` sudah ada sebelum menulis, dan menolak operasi overwrite.
- **FR-005**: Sistem MUST menyimpan skill sebagai file Markdown di `.hakoagent/skills/`, bukan format YAML atau JSON
- **FR-006**: Sistem MUST memiliki setiap task dengan `target` dan `definition_of_done` yang terdefinisi dan terukur
- **FR-007**: Sistem MUST menyediakan tool `hakoagent.recall` untuk mencari konteks via HNSW + FTS
- **FR-008**: Sistem MUST menyediakan tool `hakoagent.vigilance` untuk deteksi regresi, file terlupakan, dan TODO
- **FR-009**: Sistem MUST tidak memiliki referensi ke tool eksternal seperti hakoagent di seluruh kode dan dokumentasi
- **FR-010**: Sistem MUST menyimpan semua file terkait hakoagent di bawah direktori `.hakoagent/` atau root proyek

### Key Entities *(include if feature involves data)*

- **Event**: Tindakan agen yang dicatat dengan event_id, timestamp, session_id, actor, action, target, change_type, metadata
- **Session**: Riwayat sesi agen dengan session_id, started_at, ended_at, ringkasan, status, model_used
- **Task**: Tugas dengan task_id, title, target, definition_of_done, prioritas, status, dod_verified
- **Skill**: Pola sukses dalam format Markdown dengan skill_id, name, description, context_tags, success_count, failure_count, status
- **Finding**: Temuan codebase dengan finding_id, content, finding_type, file, referensi event
- **Decision**: Keputusan arsitektur dengan decision_id, title, rationale, consequences, referensi event
- **CodeIndex**: Entri indeks kode dengan entry_id, file_path, symbol_name, symbol_type, dependensi

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Agen dapat menyelesaikan siklus tugas lengkap (init → recall → event_log → task_create → skill_add → task_complete) dalam waktu < 30 detik
- **SC-002**: 100% task yang ditandai selesai memiliki `definition_of_done` yang terisi dan diverifikasi
- **SC-003**: 0 referensi ke "hakoagent" ditemukan di seluruh file sumber, dokumentasi, dan konfigurasi proyek
- **SC-004**: 100% skill disimpan sebagai file Markdown (`.md`) di `.hakoagent/skills/`
- **SC-005**: Setiap event yang ditulis ke koleksi `events` memiliki timestamp ISO 8601 dan tidak dapat di-overwrite
- **SC-006**: Tool calling HakoAgent dapat ditemukan dan dipanggil oleh harness agent tanpa konfigurasi tambahan yang kompleks

## Assumptions

- Agen harness (OpenCode) mendukung pemanggilan tool dengan nama yang dapat dikonfigurasi
- Database HakoDB dapat dibangun dan dijalankan sebagai embedded library tanpa server eksternal
- Rust toolchain tersedia untuk build core HakoAgent
- Direktori proyek memiliki izin tulis untuk membuat `.hakoagent/`
- Format Markdown cukup untuk merepresentasikan metadata skill dan contoh kode
- Semua interaksi agen dicatat sebagai event secara otomatis tanpa perlu intervensi manual

## Clarifications

### Session 2026-10-29

- Q: Bagaimana mekanisme penegakan append-only pada koleksi events diimplementasi secara teknis? → A: Application-level guard (kode memeriksa event_id sebelum tulis)

---
