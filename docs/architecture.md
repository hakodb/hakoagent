# HakoAgent — Architecture Notes

Studi ringkas atas kode untuk kontributor baru. TL;DR periksa `AGENTS.md` (untuk agent AI)
dan `INSTALL.md` (untuk manusia).

## Komponen

| File | Isi |
|------|-----|
| `hakoagent` | Semua logika: CLI + MCP server, satu file Python 3 stdlib-only (~5.400 baris) |
| `hakoagent-cli` / `hakoagent-mcp` | Launcher tipis: set `HAKOAGENT_MODE`, pipindahkan `sys.argv`, lalu `runpy.run_path(hakoagent)` |
| `hakoagent-mcp-server` | Wrapper POSIX opsional (mkfifo) untuk sesi MCP persisten |
| `install.py` | Installer cross-platform (Python stdlib); mengunduh native lib dari release `hakodb/hakodb` |
| `test_hakoagent.py` | 92 test (unittest), memuat modul via `exec` dan mengarahkan ke dir `.hakoagent` temporer |
| `lib/` | Native library hasil unduhan installer (`.dll` Windows, `.so` Linux) — tidak di-commit |
| `specs/`, `docs/` | Riwayat spesifikasi fitur (spec-kit) |

## Mode eksekusi (satu implementasi, tiga pintu)

`main()` membaca `basename(sys.argv[0])` + env `HAKOAGENT_MODE`:
- `hakoagent` / `hakoagent-mcp` → MCP server default (JSON-RPC di stdin/stdout)
- `hakoagent-cli` → mode CLI sekali-jalan

## Engine hakodb (wajib, tanpa fallback)

- `_hakodb_lib_load()` mencari kandidat di `lib/` sesuai `sys.platform`
  (Windows: `hakodb-*.dll`, Linux: `libhakodb-*.so` dengan preferensi glibc paling tua dulu)
- Tanpa loadable library → tulis error + `sys.exit(1)` — **tidak ada fallback JSON**.
- Semua akses data lewat fungsi FFI `hk_*` (via `ctypes`, signature di `lib/hakodb.h`,
  sumber aslinya proyek `hakodb/hakodb` Rust + cbindgen).
- Engine satu instance (`_hako_engine`), dibuka pada `HAKO_DIR` (normally `.hakoagent/`,
  dicari dengan jalan naik dari CWD → script dir → `~/.hakoagent`).

## Penyimpanan

Semua di `HAKO_DIR` (`.hakoagent/`): koleksi hakodb (`sessions`, `events`, `code_index`,
`skills`, `tasks`, dll), direktori `memory/`, `logs/`, `sync/`, marker `mcp-enabled`.

## Perintah utama CLI

`init`, `index`, `recall`, `skill`, `task`, `events`, `vigilance`, `impact`, `bug_scan`,
`team`, `sync`, `cache`, `graph` (traverse/shortest-path/dependents/query/adr/...),
`revision`, `mcp`. `task complete` lakukan re-index diam bila ada working-tree changes.
Skill diekstrak dari tugas yang selesai, dedup via `skill.refine`/`skill.troubleshoot`.

## MCP

- Mati secara default; per-project `hakoagent mcp enable` menulis `mcp.servers.hakoagent`
  ke `opencode.json` proyek (Windows: `command` diisi `[python, <path hakoagent-mcp>]`).
- Tool surface: `save_doc`, `load_doc`, `recall`, `cache_*`, `events`, `skill.*`, `task.*`,
  `sync.*`, `graph.*`, `vigilance`, `bug_scan`, `team.*` (lihat `AGENTS.md` untuk daftar parameter).
- Saat MCP aktif: `_auto_init` diam + indexing background decision (`initialize` tidak diblok).

## Install dengan `install.py`

1. Unduh native lib (SHA256 diverifikasi dari `SHA256SUMS` release) → `lib/`, dipastikan
   loadable via `ctypes.CDLL`; varian glibc dicoba berurutan saat yang pertama gagal.
2. Pasang bin (Linux `~/.local/bin`, Windows `%LOCALAPPDATA%\hakoagent\bin` + shim `.cmd`),
   salin `AGENTS.md`, install skills/commands OpenCode + Claude.
3. MCP tetap OFF secara default (marka kebijakan), `hakoagent mcp enable` per project.
