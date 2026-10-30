# Speckit Addon — Spesifikasi Implementasi

**Slug**: `hakoagent-addon`  
**Versi**: 1.0.0  
**Tanggal**: 2026-10-28  
**Dasar**: `.specify/memory/constitution.md` (HakoDB Agent Memory Constitution v1.0.0)

---

## 1. Tujuan

Membangun **Speckit Addon** — sebuah skill/addon plug-and-play untuk harness agent yang didukung oleh HakoDB sebagai memori jangka panjang. Tujuan utamanya adalah menjadikan agent AI lebih **smart**, **tidak mudah lupa**, **konsisten lintas model LLM**, **cekat**, memiliki **target jelas**, **mengerti codebase dengan cepat**, dan **irit context / endpoint request** sambil tetap efektif.

---

## 2. Latar Belakang

Konstitusi Speckit (v1.0.0) telah ditetapkan sebagai landasan pengembangan. Konstitusi ini menetapkan 10 prinsip intan, arsitektur data HakoDB (9 koleksi), 7 modul implementasi, aturan interaksi agent, serta panduan instalasi sebagai addon/skill. Spesifikasi ini menterjemahkan konstitusi menjadi rencana implementasi teknis yang dapat dikerjakan oleh agent.

---

## 3. Kebutuhan Fungsional

### 3.1 Hakodb Binding Layer (Modul 1)

| ID | Kebutuhan |
|----|-----------|
| FR-1.1 | Menyediakan wrapper FFI/C ABI dari HakoDB untuk bahasa host harness (Go, Python, JS/TS, Rust). |
| FR-1.2 | Mendukung operasi CRUD dasar ke semua koleksi HakoDB melalui binding yang dipakai oleh Memory Service. |
| FR-1.3 | Build output: `libhakodb.so` (Linux), `.dylib` (macOS), `.dll` (Windows) + `hakodb.h` per target. |
| FR-1.4 | Dukungan fitur minimal `--no-default-features` (embedded core) untuk footprint ringan. |

### 3.2 Memory Service (Modul 2)

| ID | Kebutuhan |
|----|-----------|
| FR-2.1 | Baca/tulis ke semua koleksi: `sessions`, `events`, `decisions`, `findings`, `code_index`, `tasks`, `context_cache`, `skills`, `lessons_learned`. |
| FR-2.2 | Setiap event ditulis sebagai append-only (tidak pernah diedit/dihapus) dengan timestamp ISO 8601. |
| FR-2.3 | Setiap sesi agent memiliki `started_at` dan `ended_at` yang terdefinisi. |
| FR-2.4 | Setiap `decision` dan `finding` merujuk ke `event_id` asalnya (kausalitas). |

### 3.3 Codebase Indexer (Modul 3)

| ID | Kebutuhan |
|----|-----------|
| FR-3.1 | Scan repository untuk mengumpulkan simbol, file, dan dependensi ke koleksi `code_index`. |
| FR-3.2 | Update `code_index` secara inkremental menggunakan `watch_collection` (change stream HakoDB). |
| FR-3.3 | Mencatat perubahan antara versi (diff), bukan hanya snapshot. |

### 3.4 Context Retriever (Modul 4)

| ID | Kebutuhan |
|----|-----------|
| FR-4.1 | Mencari konteks relevan menggunakan HNSW vector search (KNN) + Full-Text Search. |
| FR-4.2 | Merangkum hasil pencarian sebelum mengirim ke endpoint LLM (context frugality). |
| FR-4.3 | Menyimpan rangkuman ke `context_cache` untuk menghindari panggilan ulang ke endpoint. |
| FR-4.4 | Waktu ambil konteks terkait tugas < X detik (target metrik). |

### 3.5 Task Planner (Modul 5)

| ID | Kebutuhan |
|----|-----------|
| FR-5.1 | Setiap task harus memiliki `target` dan `definition_of_done` (DoD) yang terukur. |
| FR-5.2 | Flow tugas konsisten lintas model LLM: Ambil konteks → Rencanakan → Eksekusi → Verifikasi → Rifleksi → Simpan. |
| FR-5.3 | Template output standar (tidak bervariasi per model). |
| FR-5.4 | Pelacakan progres task (status: todo, in-progress, done, blocked). |

### 3.6 Skill Engine (Modul 6)

| ID | Kebutuhan |
|----|-----------|
| FR-6.1 | Setelah selesai tugas, agent melakukan rifleksi pasca-tugas (apa yang berhasil, gagal, pola apa). |
| FR-6.2 | Mengekstrak pola sukses sebagai skill baru atau memperbaiki skill existing di koleksi `skills`. |
| FR-6.3 | Menyimpan pelajaran dari kegagalan ke koleksi `lessons_learned`. |
| FR-6.4 | Saat tugas baru datang, agent mengambil skill terbaik dari `skills` melalui semantic search. |
| FR-6.5 | Skill yang tidak efektif direvisi atau diarsip; jumlah skill aktif meningkat seiring waktu. |

### 3.7 Vigilance Checker (Modul 7)

| ID | Kebutuhan |
|----|-----------|
| FR-7.1 | Mendeteksi file yang diubah tetapi tidak diuji. |
| FR-7.2 | Mendeteksi TODO yang belum disentuh. |
| FR-7.3 | Mendeteksi regresi terhadap prinsip konstitusi. |
| FR-7.4 | Melaporkan file yang terlupakan dalam suatu task. |

---

## 4. Kebutuhan Non-Fungsional

| ID | Kebutuhan |
|----|-----------|
| NF-1 | **Embedded**: Tidak perlu server/daemon eksternal; berjalan in-process seperti SQLite. |
| NF-2 | **Bahasa-agnostik**: Dapat dipanggil dari bahasa apa pun melalui flat C ABI. |
| NF-3 | **Durability**: WAL + tiered-segment storage; data survive crash/restart. |
| NF-4 | **Consistensi lintas model**: Flow, template, dan target sama untuk semua model LLM. |
| NF-5 | **Context frugality**: Pengurangan panggilan endpoint LLM per task ≥ N% melalui cache + rangkuman + reuse skill. |
| NF-6 | **Append-only histori**: Event log tidak dapat diubah secara sepihak; mendukung time travel. |

---

## 5. Arsitektur Data (HakoDB Collections)

| Koleksi | Fungsi |
|---------|--------|
| `sessions` | Riwayat sesi agent (started_at, ended_at, ringkasan, status, model_used) |
| `events` | Histori kronologis semua tindakan (append-only event log) |
| `decisions` | Keputusan arsitektur + alasan + konsekuensi + referensi event asal |
| `findings` | Temuan codebase, bug, pola, catatan error |
| `code_index` | Simbol, file, dependensi (dari scanner lokal, update inkremental) |
| `tasks` | Tugas dengan target, prioritas, DoD, status |
| `context_cache` | Cache konteks ringkas untuk mengurangi panggilan ulang endpoint |
| `skills` | Skill/pola berhasil yang diekstraksi dari tugas sebelumnya |
| `lessons_learned` | Pelajaran dari kegagalan atau perbaikan yang perlu dihindari |

---

## 6. Antarmuka (API / CLI)

### 6.1 CLI Commands

| Command | Deskripsi |
|---------|-----------|
| `hakoagent init --db <path> --collections all` | Inisialisasi database HakoDB dan semua koleksi |
| `hakoagent index` | Scan dan index codebase ke `code_index` |
| `hakoagent recall <query>` | Ambil konteks dari memori (HNSW + FTS) |
| `hakoagent skill list` | Lihat semua skill aktif |
| `hakoagent skill add <name>` | Tambah skill baru |
| `hakoagent task list` | Lihat tugas dan status |
| `hakoagent events` | Lihat histori kronologis |
| `hakoagent vigilance` | Deteksi file terlupakan / regresi |

### 6.2 Integrasi ke Harness Agent (Pseudocode)

```python
from hakoagent import SpeckitMemory

hakoagent = SpeckitMemory(db_path="./hakoagent.db")

# Sebelum tugas
context = hakoagent.retrieve_context(query="bagaimana implementasi error handling Rust?")
skills = hakoagent.get_skills(tags=["rust", "error-handling"])

# Selama tugas (flow konsisten lintas model)
hakoagent.log_event(action="code_read", target="src/main.rs")
hakoagent.save_finding(collection="findings", doc={...})

# Setelah tugas (self-improvement)
hakoagent.reflect_and_extract_skill(task_id="task_001")
hakoagent.complete_task(task_id="task_001", dod_met=True)
```

---

## 7. Metrik Keberhasilan

| Metrik | Target |
|--------|--------|
| Konsistensi lintas model | Flow dan output standar untuk semua model LLM (0 variasi struktural) |
| Waktu ambil konteks terkait tugas | < X detik |
| Pengurangan panggilan endpoint LLM per task | ≥ N% (via cache + rangkuman + reuse skill) |
| Task selesai tanpa DoD terpenuhi | 0 |
| File yang diubah dalam task tercatat di `code_index` | 100% |
| Jumlah skill aktif di `skills` | Meningkat seiring waktu; skill tidak efektif direvisi atau diarsip |
| Histori event tersimpan | Append-only, dapat diakses kembali (time travel) |

---

## 8. Roadmap Implementasi (7 Fase)

| Fase | Modul | Deliverable |
|------|-------|-------------|
| Fase 1 | Hakodb Binding Layer | Wrapper C ABI / FFI, build shared library |
| Fase 2 | Memory Service | CRUD semua koleksi, event append-only |
| Fase 3 | Codebase Indexer | `hakoagent index`, inkremental via `watch_collection` |
| Fase 4 | Context Retriever | `hakoagent recall`, HNSW + FTS, `context_cache` |
| Fase 5 | Task Planner | `hakoagent task list`, target + DoD, flow standar |
| Fase 6 | Skill Engine | `hakoagent skill list/add`, rifeksi otomatis, `lessons_learned` |
| Fase 7 | Vigilance Checker + Integrasi | `hakoagent vigilance`, deteksi regresi, integrasi penuh ke harness |

---

## 9. Kriteria Penerimaan (Acceptance Criteria)

- [ ] HakoDB shared library dapat dibangun untuk Linux/macOS/Windows.
- [ ] Semua 9 koleksi HakoDB dapat diakses melalui Memory Service.
- [ ] Event log append-only terverifikasi (tidak ada data yang ter-overwrite).
- [ ] `hakoagent init` membuat database dan koleksi dengan benar.
- [ ] `hakoagent recall` mengembalikan konteks relevan dalam waktu target.
- [ ] Flow tugas konsisten untuk minimal 2 model LLM berbeda.
- [ ] Skill engine dapat mengekstrak dan menyimpan minimal 1 skill dari satu tugas uji coba.
- [ ] Vigilance checker mendeteksi minimal 1 kasus file yang diubah tapi tidak diuji.
- [ ] Dokumentasi instalasi (Cargo, standalone binary, skill.yaml) lengkap dan diuji.

---

## 10. Pertanyaan Terbuka (Open Questions)

1. Nilai metrik `X` (detik) dan `N` (%) masih perlu ditentukan oleh tim proyek.
2. Bahasa host utama untuk binding FFI pertama perlu dipilih (Go? Python? Rust?).
3. Apakah akan ada dukungan multi-tenant (banyak proyek dalam satu database HakoDB)?
4. Apakah enkripsi at-rest ChaCha20-Poly1305 akan diaktifkan secara default?

---

## 11. Referensi

- [HakoDB Repository](https://github.com/hakodb/hakodb)
- [Spec Kit Repository](https://github.com/github/spec-kit)
- [Speckit Constitution v1.0.0](.specify/memory/constitution.md)

---

**Spesifikasi ini siap untuk dilanjutkan ke `/hakoagent-plan` dan `/hakoagent-tasks`.**
