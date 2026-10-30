# HakoAgent — Architecture Notes

A short code study for new contributors. TL;DR: see `assets/AGENTS.md` (for AI agents)
and `INSTALL.md` (for humans).

## Components

| File | Role |
|------|------|
| `hakoagent` | All logic: CLI + MCP server, single Python 3 stdlib-only file (~5,400 lines) |
| `hakoagent-cli` / `hakoagent-mcp` | Thin launchers: set `HAKOAGENT_MODE`, remap `sys.argv`, then `runpy.run_path(hakoagent)` |
| `hakoagent-mcp-server` | Optional POSIX wrapper (mkfifo) for a persistent MCP session |
| `install.py` | Cross-platform installer (Python stdlib); downloads the native lib from the hakodb release |
| `test_hakoagent.py` | 92 tests (unittest); loads the module via `exec` and points it at a temp `.hakoagent` dir |
| `lib/` | Native library downloaded by the installer (`.dll` Windows, `.so` Linux) — not committed |
| `specs/`, `docs/` | Historical feature specifications (spec-kit) |

## Execution modes (one implementation, three doors)

`main()` reads `basename(sys.argv[0])` + the `HAKOAGENT_MODE` env var:
- `hakoagent` / `hakoagent-mcp` → MCP server by default (JSON-RPC over stdin/stdout)
- `hakoagent-cli` → one-shot CLI mode

## The hakodb engine (required, no fallback)

- `_hakodb_lib_load()` picks candidates from `lib/` by `sys.platform`
  (Windows: `hakodb-*.dll`; Linux: `libhakodb-*.so`, oldest-glibc build first)
- No loadable library → error message + `sys.exit(1)` — **no JSON fallback**.
- All data flows through the `hk_*` FFI functions (via `ctypes`; signatures in `lib/hakodb.h`,
  upstream source in the `hakodb/hakodb` Rust crate + cbindgen).
- One engine instance (`_hako_engine`), opened at `HAKO_DIR` (normally `.hakoagent/`,
  found by walking up from CWD → script dir → `~/.hakoagent`).

## Storage

Everything lives under `HAKO_DIR` (`.hakoagent/`): hakodb collections (`sessions`, `events`,
`code_index`, `skills`, `tasks`, etc.), `memory/`, `logs/`, `sync/` directories,
and the `mcp-enabled` marker.

## Main CLI verbs

`init`, `index`, `recall`, `skill`, `task`, `events`, `vigilance`, `impact`, `bug_scan`,
`team`, `sync`, `cache`, `graph` (traverse/shortest-path/dependents/query/adr/...),
`revision`, `mcp`. `task complete` performs a quiet re-index when the working tree has
changes. Completed tasks auto-extract into skills, deduplicated via
`skill.refine` / `skill.troubleshoot`.

## MCP

- Off by default; per-project `hakoagent mcp enable` writes `mcp.servers.hakoagent`
  to the project's `opencode.json` (Windows: `command` is `[python, <hakoagent-mcp path>]`).
- Tool surface: `save_doc`, `load_doc`, `recall`, `cache_*`, `events`, `skill.*`, `task.*`,
  `sync.*`, `graph.*`, `vigilance`, `bug_scan`, `team.*` (see `assets/AGENTS.md` for the full list).
- When MCP is enabled: quiet `_auto_init` + background indexing keeps `initialize` responsive.

## Installing via `install.py`

1. Download the native lib (SHA256-verified against the release `SHA256SUMS`) into `lib/`,
   then prove it loads via `ctypes.CDLL`; glibc variants are tried in order when one fails.
2. Install binaries (Linux: `~/.local/bin`; Windows: `%LOCALAPPDATA%\hakoagent\bin` + `.cmd` shims),
   copy `AGENTS.md` (from `assets/`, never installed into this repo itself),
   and deploy OpenCode + Claude skills/commands.
3. MCP stays OFF by default (policy marker); `hakoagent mcp enable` turns it on per project.
