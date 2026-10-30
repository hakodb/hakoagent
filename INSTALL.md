# HakoAgent - Instalasi dan Penggunaan

## 1. Instalasi

### Prasyarat
- Python 3 (stdlib only, no external dependencies)

### Instalasi

```bash
# Clone repositori
git clone https://github.com/hakodb/hakoagent.git
cd hakoagent

# Pasang (installer cross-platform, Python stdlib only)
python install.py            # project-local: ./hakoagent + ./lib/ + ./AGENTS.md + .opencode/
python install.py --global   # global: ~/.local/bin (Linux) | %LOCALAPPDATA%\hakoagent\bin + shims .cmd (Windows)
export PATH="$HOME/.local/bin:$PATH"   # Linux saja; Windows: setx PATH (diprint oleh installer)

# Verifikasi instalasi
hakoagent --help
```

Catatan:
- `install.py` mengunduh native hakodb library dari release terbaru `github.com/hakodb/hakodb`
  (Windows x86_64: `.dll`, Linux x86_64: `.so`) serta memverifikasinya via `SHA256SUMS`.
- **HakoAgent menolak berjalan tanpa native library** (tidak ada fallback JSON).
- macOS belum didukung (belum ada native library) — installer berhenti dengan pesan jelas.
- Windows: eksekusi script via interpreter, contoh `python hakoagent --help`; MCP config
  ditulis dengan `python "<path hakoagent-mcp>"` sebagai command.
- `--remove-data` pada uninstall ikut menghapus `.hakoagent/`.

### Inisialisasi Database (sekali saja per proyek)

```bash
cd /path/to/proyek
hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

Ini akan membuat:
- Direktori `.hakoagent/` di root proyek
- 9 koleksi: sessions, events, decisions, findings, code_index, tasks, context_cache, skills, lessons_learned
- File konfigurasi OpenCode: `.opencode/skills/hakoagent-usage-pattern/SKILL.md` dan `.opencode/commands/hakoagent.md`

---

## 2. Inisialisasi Database

Setiap proyek yang akan menggunakan HakoAgent perlu diinisialisasi terlebih dahulu:

```bash
cd /path/to/proyek
hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

Ini akan membuat:
- Direktori `.hakoagent/` di root proyek
- File database `hakoagent.db`
- 9 koleksi: sessions, events, decisions, findings, code_index, tasks, context_cache, skills, lessons_learned

---

## 3. Perintah CLI (Command Line Interface)

| Command | Deskripsi | Contoh Penggunaan |
|---------|-----------|-------------------|
| `hakoagent init` | Inisialisasi database dan koleksi | `hakoagent init --db ./.hakoagent/hakoagent.db --collections all` |
| `hakoagent index` | Scan dan index codebase | `hakoagent index` |
| `hakoagent recall` | Ambil konteks dari memori (HNSW + FTS) | `hakoagent recall "error handling Rust"` |
| `hakoagent skill list` | Lihat semua skill aktif | `hakoagent skill list` |
| `hakoagent skill add` | Tambah skill baru | `hakoagent skill add "rust-error-handling"` |
| `hakoagent task list` | Lihat tugas dan status | `hakoagent task list` |
| `hakoagent events` | Lihat histori kronologis | `hakoagent events` |
| `hakoagent vigilance` | Deteksi file terlupakan / regresi | `hakoagent vigilance` |
| `hakoagent cache stats` | Lihat statistik cache | `hakoagent cache stats` |
| `hakoagent cache get` | Ambil konteks dari cache | `hakoagent cache get "query"` |
| `hakoagent cache put` | Simpan konteks ke cache | `hakoagent cache put "query" "summary"` |
| `hakoagent graph traverse` | Traversal graph dependensi | `hakoagent graph traverse <node> <dir> <depth>` |
| `hakoagent graph shortest-path` | Jalur terpendek (Dijkstra) | `hakoagent graph shortest-path <from> <to>` |
| `hakoagent graph dependents` | File yang bergantung pada node | `hakoagent graph dependents <node>` |
| `hakoagent graph dependents-reverse` | File yang bergantung oleh node | `hakoagent graph dependents-reverse <node>` |
| `hakoagent revision prune` | Hapus revisi koleksi volatil | `hakoagent revision prune --dry-run` |
| `hakoagent mcp enable` | Aktifkan MCP untuk proyek ini | `hakoagent mcp enable` |
| `hakoagent mcp disable` | Nonaktifkan MCP proyek ini | `hakoagent mcp disable` |
| `hakoagent mcp status` | Cek status MCP proyek | `hakoagent mcp status` |

---

## 4. Contoh Penggunaan

### 4.1 Inisialisasi dan Pengaturan Awal

Inisialisasi database di root proyek Anda:

```bash
cd /proyek-anda
hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

Output:

```
HakoAgent database initialized at: ./.hakoagent/hakoagent.db
Collections: ["sessions", "events", "decisions", "findings", "code_index", "tasks", "context_cache", "skills", "lessons_learned"]
```

### 4.2 Mengambil Konteks (Anti-Lupa dan Codebase Fluency)

Sebelum mencari informasi di codebase secara manual, jalankan `hakoagent recall` terlebih dahulu:

```bash
hakoagent recall "bagus implementasi error handling Rust" --limit 5
```

Output:

```
Query: bagus implementasi error handling Rust
Context retrieval initialized (HNSW + FTS + summarizer + cache).
  Results:
    - speckit-core/src/memory/mod.rs :: mod
    - specs/001-refactor-hakoagent/plan.md :: plan
    - speckit-core/src/memory/events.rs :: events
```

### 4.3 Manajemen Skill (Self Skill Improvement)

```bash
# Lihat semua skill aktif
hakoagent skill list

# Tambah skill baru
hakoagent skill add "python-error-handling-pattern"

# Simpan ke cache untuk reuse
hakoagent cache put "error-handling-python" "Gunakan try/except yang spesifik, hindari bare except, propagasi dengan raise ... from exc"

# Ambil dari cache (cepat, tanpa panggilan LLM)
hakoagent cache get "error-handling-python"
```

### 4.4 Manajemen Task (Clear Target)

```bash
# Lihat semua tugas
hakoagent task list

# Buat task baru dengan target dan DoD
hakoagent task create "Implement error handling" "Semua fungsi publik harus menggunakan Result<T, E>" "Unit test >= 80% coverage, dokumen diupdate" P1

# Tandai task selesai
hakoagent task complete <task_id>

# Lihat semua tugas
hakoagent task list
```

### 4.5 Vigilance Check (Cekatan)

```bash
# Deteksi file yang diubah tapi tidak diuji, TODO tertinggal, regresi
hakoagent vigilance
```

### 4.6 Cache Management (Context Frugality)

```bash
# Lihat statistik cache
hakoagent cache stats

# Simpan konteks manual ke cache
hakoagent cache put "query-contoh" "ringkasan hasil pencarian" 300

# Ambil konteks dari cache (cepat, tanpa panggilan LLM)
hakoagent cache get "query-contoh"
```

### 4.7 Graph Traversal (Codebase Fluency)

```bash
# Traversal dari simbol tertentu (misal: fungsi validate_input)
hakoagent graph traverse validate_input in 2

# Cari jalur terpendek antara dua simbol
hakoagent graph shortest-path main error_handler

# Lihat apa yang bergantung pada suatu file
hakoagent graph dependents src/utils.rs

# Lihat apa yang dipanggil oleh suatu fungsi
hakoagent graph dependents-reverse src/main.rs

# Lihat blast radius sebelum mengedit file
hakoagent impact src/main.rs
```

---

## 5. Koleksi Data (HakoDB)

Semua data disimpan di `./.hakoagent/hakoagent.db` dengan 9 koleksi:

| Koleksi | Fungsi |
|---------|--------|
| `sessions` | Riwayat sesi agent (started_at, ended_at, status) |
| `events` | Histori kronologis semua tindakan (append-only) |
| `decisions` | Keputusan arsitektur + alasan + konsekuensi |
| `findings` | Temuan codebase, bug, pola, catatan error |
| `code_index` | Simbol, file, dependensi (untuk graph traversal) |
| `tasks` | Tugas dengan target, prioritas, DoD, status |
| `context_cache` | Cache konteks ringkas untuk mengurangi panggilan LLM |
| `skills` | Skill/pola berhasil untuk reuse |
| `lessons_learned` | Pelajaran dari kegagalan untuk dihindari |

---

## 6. Integrasi dengan Harness Agent (OpenCode)

HakoAgent dirancang sebagai addon/skill untuk harness agent seperti OpenCode. Untuk mengintegrasikan:

1. **Tambahkan hakoagent ke konfigurasi agent** Anda agar dapat memanggil perintah `hakoagent` dari dalam chat
2. **Gunakan template interaksi** berikut dalam prompt sistem agent:

```
Anda adalah agen AI dengan akses ke HakoAgent Memory System. Gunakan perintah berikut:

- hakoagent recall <query> - Ambil konteks dari memori (jangan lupa untuk mengecek cache dulu)
- hakoagent skill list - Lihat skill yang tersedia
- hakoagent task list - Lihat tugas dan status
- hakoagent events - Lihat histori tindakan
- hakoagent vigilance - Deteksi regresi dan file terlupakan
- hakoagent graph traverse <node> <dir> <depth> - Telusuri dependensi codebase
- hakoagent graph shortest-path <from> <to> - Cari jalur terpendek antar simbol
- hakoagent cache stats - Lihat statistik cache
- hakoagent cache put <query> <summary> [ttl] - Simpan konteks ke cache

Selalu gunakan hakoagent recall sebelum mencari informasi di codebase untuk mengurangi panggilan endpoint LLM.
```

### 6.1 MCP Server (opsional, per proyek)

MCP **mati secara default**. Instalasi global tidak menulis konfigurasi MCP ke `~/.claude.json`
maupun `~/.config/opencode/opencode.jsonc`.

```bash
cd /path/to/proyek
hakoagent mcp enable    # buat .hakoagent/mcp-enabled + tulis mcp.servers.hakoagent
hakoagent mcp status    # cek status
hakoagent mcp disable   # hapus marker + entri konfigurasi
```

`mcp enable` menulis entri OpenCode V2 berikut ke `opencode.json` (atau
`.opencode/opencode.json`) dengan path absolut:

```json
{
  "mcp": {
    "servers": {
      "hakoagent": {
        "type": "local",
        "command": ["/home/user/.local/bin/hakoagent-mcp"]
      }
    }
  }
}
```

Jika proyek hanya punya `opencode.jsonc`, perintah akan mencetak snippet untuk ditempel manual
agar komentar tidak hilang. Setelah enable, restart sesi OpenCode atau jalankan `hakoagent-mcp`.

---

## 7. Arsitektur Data

Semua data disimpan di `./.hakoagent/memory/<koleksi>/` sebagai file JSON:

```
.hakoagent/
├── memory/          # JSON files per collection
│   ├── sessions/
│   ├── events/
│   ├── decisions/
│   ├── findings/
│   ├── code_index/
│   ├── tasks/
│   ├── context_cache/
│   ├── skills/
│   └── lessons_learned/
├── skills/          # File skill dalam format Markdown
├── sessions/        # Export sesi (opsional)
└── logs/            # Log operasi (opsional)
```

## 8. Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `hakoagent: command not found` | Pastikan `~/.local/bin` ada di PATH: `export PATH="$HOME/.local/bin:$PATH"` |
| `Database not found` | Jalankan `hakoagent init --db ./.hakoagent/hakoagent.db --collections all` dulu |
| `Cache empty` | Jalankan `hakoagent recall <query>` minimal sekali untuk mengisi cache |
| `Graph empty` | Pastikan codebase sudah diindex dengan `hakoagent init` atau `hakoagent index` |

---

## 9. Lisensi

MIT License - sama dengan HakoDB. Lihat `LICENSE-MIT` di repositori HakoDB.

---

## 10. Kontak dan Dukungan

- Repositori: https://github.com/hakodb/hakoagent
- Dokumentasi: /docs/
- Lisensi: MIT