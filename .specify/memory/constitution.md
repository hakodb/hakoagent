# HakoAgent Constitution

Konstitusi resmi pengembangan tool pendukung harness agent untuk proyek **hakoagent**, didukung oleh [HakoDB](https://github.com/hakodb/hakodb) — embedded document database dengan native vector + graph search, flat C ABI, WAL durability — menggunakan **Python saja (stdlib only)** dan **FFI library asli HakoDB** (`lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` + `lib/hakodb.h`).

Konstitusi ini mengatur bagaimana agen AI dalam harness (misal OpenCode) menjadi **smart, tidak mudah lupa, konsisten, cekatan, target jelas, mengerti codebase dengan cepat, dan irit context / endpoint request** sambil tetap efektif — dengan penekanan pada **kualitas kode, pengujian, dan maintainability** dalam implementasi Python.

---

## 1. Preamble / Visi

HakoAgent adalah lapis memori dan pemahaman codebase untuk harness agent. Dengan HakoDB sebagai backend memori jangka panjang melalui FFI asli, agen AI diharapkan:

- **Smart** — memahami konteks tugas dan riwayat sebelumnya
- **Tidak mudah lupa** — menyimpan setiap temuan, keputusan, dan pelajaran di HakoDB
- **Konsisten** — flow, output, dan target sama terlepas dari model LLM yang digunakan
- **Cekatan** — mendeteksi regresi, file yang terlupakan, dan tugas yang belum selesai
- **Target jelas** — setiap tugas memiliki definisi selesai (DoD) yang terukur
- **Mengerti codebase dengan cepat** — indeks struktural file, simbol, dan dependensi
- **Irit context dan endpoint request** — hanya mengambil konteks relevan, tetap efektif
- **Python only** — implementasi murni Python (stdlib), tanpa Rust, tanpa build step, tanpa tool eksternal
- **Real hakodb FFI** — komunikasi langsung dengan library asli HakoDB melalui ctypes dan header `hakodb.h`
- **Kualitas kode & maintainability** — kode bersih, terdokumentasi, mudah dipelihara, dan diuji secara menyeluruh

---

## 2. Prinsip Intan

| # | Prinsip | Artinya dalam implementasi |
|---|---------|---------------------------|
| 1 | **Smart Memory** | Setiap interaksi signifikan disimpan ke koleksi HakoDB (`sessions`, `decisions`, `findings`, `skills`) melalui FFI asli atau JSON file di `.hakoagent/memory/` |
| 2 | **Anti-Lupa** | Sebelum mulai tugas baru, agent wajib query `findings` dan `skills` terkait dulu |
| 3 | **Kronologi & Histori** | Setiap tindakan dicatat sebagai event berurutan waktu (append-only, tidak pernah diedit/dihapus) |
| 4 | **Consistency** | Template output, naming, dan error handling dipaksa untuk semua model LLM |
| 5 | **Cross-Model Consistency** | Flow, template, dan target sama terlepas dari model LLM yang dipakai harness |
| 6 | **Vigilance** | Pemeriksaan otomatis: file yang diubah tapi tidak diuji, TODO yang belum disentuh, regresi |
| 7 | **Clear Target** | Setiap task harus memiliki `target` dan `definition_of_done` yang dicatat |
| 8 | **Codebase Fluency** | Index file, simbol, dan dependensi untuk navigasi cepat |
| 9 | **Context Frugality** | Ambil hanya potongan code yang relevan, rangkum sebelum kirim ke endpoint |
| 10 | **Self Skill Improvement** | Agent mengevaluasi setiap tugas, mengekstrak pola sukses sebagai skill, dan menyimpannya untuk ditingkatkan berkelanjutan |
| 11 | **Python Only** | Implementasi murni Python stdlib; tidak ada Rust, tidak ada Cargo, tidak ada build step, tidak ada dependency eksternal |
| 12 | **Real Hakodb FFI** | Menggunakan library asli HakoDB (`lib/libhakodb-...so`) melalui `ctypes` dengan header `lib/hakodb.h` sebagai sumber kebenaran ABI |
| 13 | **Code Quality** | Kode Python bersih, konsisten gaya penulisan, fungsi kecil dan terfokus, penanganan error yang tepat, tidak ada hardcoded secret / print debug / bare except |
| 14 | **Testing** | Setiap fitur baru harus memiliki unit test di `test_hakoagent.py`; semua tes harus lulus (31+ tes) sebelum perubahan dianggap selesai |
| 15 | **Maintainability** | Dokumentasi selalu diupdate bersama kode, tidak ada referensi ke tool yang sudah dihapus (Rust/cargo), struktur file jelas, dan perubahan dicatat di `decisions` |

---

## 3. Arsitektur Data (HakoDB Collections)

HakoDB menyimpan typed JSON-like dokument dalam koleksi. Koleksi yang digunakan oleh HakoAgent:

| Koleksi | Fungsi |
|---------|--------|
| `sessions` | Riwayat sesi agent (started_at, ended_at, ringkasan, status, model_used) |
| `events` | Histori kronologis semua tindakan agent (append-only event log) |
| `decisions` | Keputusan arsitektur + alasan + konsekuensi + referensi event asal |
| `findings` | Temuan codebase, bug, pola, catatan error |
| `code_index` | Simbol, file, dependensi (dari scanner lokal, diupdate inkremental) |
| `tasks` | Tugas dengan target, prioritas, DoD, status |
| `context_cache` | Cache konteks ringkas untuk mengurangi panggilan ulang ke endpoint |
| `skills` | Skill/pola berhasil yang diekstraksi dari tugas sebelumnya |
| `lessons_learned` | Pelajaran dari kegagalan atau perbaikan yang perlu dihindari |

### Lokasi Database

Database HakoDB disimpan di direktori proyek hakoagent:

```
.hakoagent/
├── hakoagent.db              # Database HakoDB (single file, via FFI)
├── skills/                   # File skill dalam format Markdown
├── sessions/                 # Export sesi (opsional)
├── logs/                     # Log operasi (opsional)
└── memory/                   # JSON files per collection (9 collections)

lib/
├── libhakodb-x86_64-unknown-linux-glibc2.28-el8.so   # Prebuilt HakoDB shared library (v0.20.0)
├── hakodb.h                                               # HakoDB C ABI header (v0.20.0, hash-verified)
└── SHA256SUMS.txt                                         # Release checksums
```

### Schema contoh (JSON-like)

```json
// events (append-only)
{
  "event_id": "evt_001",
  "timestamp": "2026-10-29T08:05:00Z",
  "session_id": "sess_001",
  "actor": "hakoagent",
  "action": "code_read",
  "target": "src/main.py",
  "change_type": "read",
  "metadata": {}
}

// tasks (dengan target dan DoD)
{
  "task_id": "task_001",
  "title": "Implement error handling",
  "target": "Semua fungsi publik harus menggunakan penanganan error yang tepat",
  "definition_of_done": "Unit test >= 80% coverage, dokumen diupdate, kode direview",
  "priority": "P1",
  "status": "done",
  "dod_verified": true
}
```

---

## 4. Skill Format (Markdown)

Setiap skill disimpan sebagai file Markdown terpisah di direktori `.hakoagent/skills/`. Format Markdown dipilih karena mudah dibaca oleh manusia dan agent, serta dapat di-version control dengan baik.

### Template Skill

```markdown
# skill_001 — Python Error Handling Pattern

## Metadata
- **skill_id**: skill_001
- **name**: python_error_handling_pattern
- **status**: active
- **created_at**: 2026-10-29T08:00:00Z
- **last_used**: 2026-10-29T10:00:00Z
- **success_count**: 12
- **failure_count**: 1
- **context_tags**: python, error-handling

## Deskripsi
Gunakan pengecualian (exception) dengan blok `try/except` yang spesifik dan jangan gunakan `bare except` dalam kode produksi Python.

## Contoh Kode
```python
def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise RuntimeError(f"Gagal membaca {path}") from exc
```

## Konteks Penggunaan
Saat menulis fungsi Python yang dapat menghasilkan error I/O, parsing, atau validasi.

## Pelajaran
Jangan gunakan `bare except:` atau `except:` tanpa mengecualikan tipe error tertentu. Selalu tangani error secara eksplisit atau propagasi dengan `raise ... from exc`.
```

### Manfaat Format Markdown

- Mudah diedit oleh manusia dan agent
- Dapat di-version control (git diff readable)
- Tidak perlu parser YAML/JSON khusus
- Dapat berisi contoh kode dengan syntax highlighting
- Mudah dicari dengan full-text search

---

## 5. Modul Implementasi (Urutan Prioritas)

| Prioritas | Modul | Deskripsi |
|-----------|-------|-----------|
| 1 | **Hakodb Binding Layer (Python ctypes)** | Wrapper FFI ke library asli HakoDB via `ctypes`, menggunakan `lib/hakodb.h` sebagai referensi ABI |
| 2 | **Memory Service** | Baca/tulis ke semua koleksi HakoDB di atas FFI atau JSON file |
| 3 | **Codebase Indexer** | Scan repository, bangun `code_index`, update inkremental |
| 4 | **Context Retriever** | Ambil konteks minimal (TF-IDF + cosine), rangkum sebelum kirim ke endpoint LLM |
| 5 | **Task Planner** | Buat task dengan target & DoD yang konsisten lintas model |
| 6 | **Skill Engine** | Rifleksi pasca-tugas, ekstraksi skill, update `skills` / `lessons_learned`, ambil skill terbaik |
| 7 | **Vigilance Checker** | Deteksi file yang lupa, regresi, konsistensi output, TODO tertinggal |

---

## 6. Aturan Interaksi dengan Harness Agent

### Sebelum bekerja

1. Query `sessions` terbaru untuk memahami konteks sesi sebelumnya
2. Query `findings` terkait tugas yang akan dikerjakan
3. Query `skills` yang relevan dengan konteks tugas
4. Buat atau ambil task dengan target dan DoD terdefinisi
5. Jalankan `hakoagent recall <query>` sebelum mencari informasi di codebase secara manual

### Selama bekerja

1. Ikuti **flow yang sama** terlepas dari model LLM yang digunakan:
   - Ambil konteks → Rencanakan → Eksekusi → Verifikasi → Rifleksi → Simpan
2. Gunakan template output standar (tidak bervariasi per model)
3. Catat setiap tindakan signifikan ke koleksi `events` (append-only, dengan timestamp)
4. Catat keputusan ke `decisions` dan temuan ke `findings` segera (jangan ditunda)
5. Setiap fungsi baru harus diikut sertai unit test di `test_hakoagent.py`

### Setelah selesai

1. Lakukan rifleksi pasca-tugas: apa yang berhasil, apa yang gagal, pola apa yang muncul
2. Ekstrak pola sukses sebagai skill baru atau perbaiki skill existing di `skills`
3. Simpan pelajaran dari kegagalan ke `lessons_learned`
4. Update status task di `tasks`, tandai DoD terpenuhi
5. Tulis ringkasan sesi dan set `ended_at`
6. Pastikan semua tes `test_hakoagent.py` masih lulus

### Jika context penuh

- Gunakan `context_cache` dan ambil ringkasan, bukan file mentah
- Priorkan dokumen terdekat dari vector search

---

## 7. Instalasi dan Penggunaan

### 7.1 Prasyarat

- Python 3 (stdlib only, no external dependencies)
- Hak izin untuk menulis file database di working directory proyek
- Prebuilt HakoDB library di `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` + header `lib/hakodb.h`

### 7.2 Instalasi

```bash
# Clone repositori
git clone <repository-url>
cd hakoagent

# Pasang executable dan konfigurasi
chmod +x hakoagent install.sh
./install.sh          # project-local: ./hakoagent + ./AGENTS.md + .opencode/

# Verifikasi instalasi
./hakoagent --help

# Inisialisasi database (sekali saja per proyek)
./hakoagent init --db ./.hakoagent/hakoagent.db --collections all

# Jalankan test suite
python3 test_hakoagent.py
```

### 7.3 Inisialisasi Database

```bash
cd /path/to/proyek
./hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

Ini akan membuat:
- Direktori `.hakoagent/` di root proyek
- File database `hakoagent.db`
- 9 koleksi: sessions, events, decisions, findings, code_index, tasks, context_cache, skills, lessons_learned

### 7.4 Perintah CLI

| Command | Deskripsi | Contoh Penggunaan |
|---------|-----------|-------------------|
| `hakoagent init` | Inisialisasi database dan koleksi | `hakoagent init --db ./.hakoagent/hakoagent.db --collections all` |
| `hakoagent index` | Scan dan index codebase | `hakoagent index` |
| `hakoagent recall` | Ambil konteks dari memori (HNSW + FTS) | `hakoagent recall "error handling Rust"` |
| `hakoagent skill list` | Lihat semua skill aktif | `hakoagent skill list` |
| `hakoagent skill add` | Tambah skill baru | `hakoagent skill add "rust-error-handling"` |
| `hakoagent task list` | Lihat tugas dan status | `hakoagent task list` |
| `hakoagent events` | Lihat histori kronologis | `hakoagent events` |
| `hakoagent vigilance` | Deteksi regresi, file terlupakan, TODO | `hakoagent vigilance` |
| `hakoagent cache stats` | Lihat statistik cache | `hakoagent cache stats` |
| `hakoagent cache get` | Ambil konteks dari cache | `hakoagent cache get "query"` |
| `hakoagent cache put` | Simpan konteks ke cache | `hakoagent cache put "query" "summary"` |
| `hakoagent graph traverse` | Traversal graph dependensi | `hakoagent graph traverse <node> <dir> <depth>` |
| `hakoagent graph shortest-path` | Jalur terpendek (Dijkstra) | `hakoagent graph shortest-path <from> <to>` |
| `hakoagent graph dependents` | File yang bergantung pada node | `hakoagent graph dependents <node>` |
| `hakoagent graph dependents-reverse` | File yang bergantung oleh node | `hakoagent graph dependents-reverse <node>` |

---

## 8. Target & Metrik Keberhasilan

| Metrik | Target |
|--------|--------|
| Konsistensi lintas model | Flow dan output standar untuk semua model LLM (0 variasi struktural) |
| Waktu ambil konteks terkait tugas | < X detik |
| Pengurangan panggilan endpoint LLM per task | ≥ N% (via cache + rangkuman + reuse skill) |
| Task selesai tanpa DoD terpenuhi | 0 |
| File yang diubah dalam task tercatat di `code_index` | 100% |
| Jumlah skill aktif di `.hakoagent/skills/` | Meningkat seiring waktu; skill tidak efektif direvisi atau diarsip |
| Histori event tersimpan | Append-only, dapat diakses kembali (time travel) |
| Skill dalam format Markdown | 100% skill disimpan sebagai `.md` (tidak ada YAML/JSON untuk skill) |
| Tes yang lulus | 100% tes di `test_hakoagent.py` harus lulus (31+ tes) |
| Kode Python only | 0 referensi ke Rust / cargo / build.rs di seluruh kode dan dokumentasi |
| Real hakodb FFI | Library `libhakodb-...so` + header `hakodb.h` tersedia dan hash-verified di `lib/` |

---

## 9. Roadmap (Fase Pengembangan)

| Fase | Fokus | Deliverable |
|------|-------|-------------|
| **Fase 1** | Binding hakodb FFI + Memory service (Python) | `hakoagent init`, baca/tulis `sessions`, `events`, `decisions`, `findings` via ctypes |
| **Fase 2** | Codebase indexer + Context retriever | `hakoagent index`, `hakoagent recall`, vector search |
| **Fase 3** | Task planner + Vigilance checker | `hakoagent task list`, `hakoagent vigilance`, DoD tracking |
| **Fase 4** | Skill engine (self-improvement, Markdown) | `hakoagent skill list/add`, rifeksi otomatis, `lessons_learned` |
| **Fase 5** | Optimasi context + integrasi penuh + kualitas kode | `context_cache`, rerank, integrasi ke harness agent target, tes 100% lulus |

---

## 10. Governance

Konstitusi ini menyelimuti semua praktik pengembangan hakoagent. Perubahan pada prinsip atau arsitektur harus melalui update pada file ini dan dicatat di koleksi `decisions` HakoDB.

- Amendmen harus didokumentasikan dengan alasan yang jelas dan versi baru yang diincremen sesuai semantic versioning
- Semua PR/review harus memverifikasi kepatuhan terhadap konstitusi
- Kompleksitas harus dijustifikasi; gunakan file panduan runtime untuk arah pengembangan
- Konstitusi adalah sumber kebenaran tertinggi; implementasi yang melanggar prinsip MUST harus diremediasi segera
- Skill harus selalu disimpan dalam format Markdown (`.md`), bukan YAML atau JSON
- Semua file terkait hakoagent harus berada di bawah direktori `.hakoagent/` atau root proyek (tidak ada referensi ke tool lain di luar hakoagent)
- **Python only**: tidak ada Rust, Cargo, atau build step dalam implementasi
- **Real hakodb FFI**: library asli HakoDB digunakan melalui `ctypes` dengan header `hakodb.h`
- **Code quality**: tidak ada hardcoded secret, print debug, bare except, atau eval/exec dalam kode
- **Testing**: setiap fitur baru harus memiliki unit test; semua tes harus lulus sebelum perubahan dianggap selesai

**Version**: 2.0.0 | **Ratified**: 2026-10-29 | **Last Amended**: 2026-10-29