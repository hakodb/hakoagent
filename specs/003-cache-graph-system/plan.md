# Implementation Plan: System Caching dan Graph Traversal Tools

**Branch**: `003-cache-graph-system` | **Date**: 2026-10-29 | **Spec**: `specs/003-cache-graph-system/spec.md`

**Input**: Feature specification from `/specs/003-cache-graph-system/spec.md`

## Summary

System Caching dan Graph Traversal Tools adalah fitur yang memungkinkan HakoAgent untuk menyimpan hasil pencarian konteks dalam cache (mengurangi panggilan endpoint LLM) serta menjelajahi dependensi codebase melalui graph traversal (BFS, Dijkstra, dependents lookup). Fitur ini melengkapi HakoAgent dengan kemampuan irit context dan pemahaman codebase yang lebih dalam.

## Technical Context

**Language/Version**: Python 3.11+ (stdlib only, no external dependencies, no build step)

**Primary Dependencies**: Python standard library only; prebuilt HakoDB shared library (`lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so`) loaded via `ctypes`, C ABI header `lib/hakodb.h` (v0.20.0)

**Storage**: JSON files under `.hakoagent/memory/<collection>/` (9 collections: sessions, events, decisions, findings, code_index, tasks, context_cache, skills, lessons_learned), with optional HakoDB FFI passthrough via the prebuilt shared library

**Testing**: `test_hakoagent.py` (Python stdlib unittest, 31 tests)

**Target Platform**: Linux (x86_64 glibc2.28-el8), cross-platform Python

**Project Type**: Single Python CLI script (`hakoagent`) at project root

**Performance Goals**: Cache hit ratio ≥ 50%, waktu respons cache hit < 100ms, graph traversal depth maksimal 10 level

**Constraints**: No build step; embedded (no server/daemon); irit context dan endpoint request; semua file di bawah `.hakoagent/` atau root proyek; tidak ada referensi ke hakoagent; skill dalam format Markdown di `.hakoagent/skills/`

**Scale/Scope**: Single project per database; koleksi `context_cache` untuk caching, `code_index` untuk graph; file source code (.py, .js, .ts, .go, .rs, dll.)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Prinsip Konstitusi | Status | Catatan |
|-------------------|--------|---------|
| Smart Memory | Terpenuhi | Hasil caching dan graph traversal disimpan di HakoDB |
| Anti-Lupa | Terpenuhi | Cache tetap tersimpan untuk reuse |
| Kronologi & Histori | Terpenuhi | Setiap operasi caching dan traversal dicatat sebagai event append-only |
| Consistency | Terpenuhi | Template output standar untuk notifikasi caching dan traversal |
| Cross-Model Consistency | Terpenuhi | Flow caching dan traversal sama untuk semua model LLM |
| Vigilance | Terpenuhi | Deteksi cache expired, graph cycle, file yang dihapus |
| Clear Target | Terpenuhi | Setiap tugas caching dan traversal punya target dan DoD |
| Codebase Fluency | Terpenuhi | Graph traversal untuk navigasi codebase |
| Context Frugality | Terpenuhi | Cache mengurangi panggilan endpoint LLM |
| Self Skill Improvement | Terpenuhi | Pola caching dan traversal sukses dapat diekstrak sebagai skill |

No violations. Constitution check PASSED.

## Project Structure

### Documentation (this feature)

```text
specs/003-cache-graph-system/
├── spec.md          # Spesifikasi fitur (/hakoagent.specify output)
├── plan.md          # Rencana teknis (ini, /hakoagent.plan output)
├── research.md      # Phase 0 output (/hakoagent.plan command)
├── data-model.md    # Phase 1 output (/hakoagent.plan command)
├── quickstart.md    # Phase 1 output (/hakoagent.plan command)
├── contracts/       # Phase 1 output (/hakoagent.plan command)
└── tasks.md         # Phase 2 output (/hakoagent.tasks command - NOT created by /hakoagent.plan)
```

### Source Code (repository root)

```text
.hakoagent/                      # Directory data HakoAgent (runtime data)
├── hakoagent.db                 # Database HakoDB (single file, via FFI)
├── skills/                      # Skill files dalam format Markdown
├── sessions/                    # Export sesi (opsional)
├── logs/                        # Log operasi (opsional)
└── memory/                      # JSON files per collection (9 collections)

lib/
├── libhakodb-x86_64-unknown-linux-glibc2.28-el8.so   # Prebuilt HakoDB shared library (v0.20.0)
├── hakodb.h                                               # HakoDB C ABI header (v0.20.0)
└── SHA256SUMS.txt                                         # Release checksums

hakoagent                      # Python CLI script (stdlib only, project root)
lib/                           # HakoDB prebuilt lib + header
specs/                         # Feature specs (001-005)
docs/                          # T057 perf, T059 security
examples/
├── performance_benchmark.rs
test_hakoagent.py              # Python stdlib unittest (31 tests)
install.sh                     # Project installer
INSTALL.md                     # Installation guide
AGENTS.md                      # Agent-facing instructions
```

**Structure Decision**: Single project structure (DEFAULT) — one Python CLI script `hakoagent` at project root, stdlib only, no build step. HakoDB prebuilt shared library + C header live in `lib/`. All runtime data stays under `.hakoagent/` or project root.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Tidak ada pelanggaran konstitusi. Kolom ini dikosongkan.

---

## Phase 0: Outline & Research

### Unknowns from Technical Context

Tidak ada NEEDS CLARIFICATION yang tersisa. Semua parameter telah ditentukan melalui spec dan clarifikasi sebelumnya:

| Unknown | Status | Resolusi |
|---------|--------|----------|
| Default TTL untuk cache | Resolved | 300 detik (5 menit) (Clarification Session 2026-10-29) |

### Research Findings (research.md)

Tidak ada research task yang diperlukan karena semua unknown telah diresolusi. `research.md` dicatat sebagai "no unresolved clarifications".

**Output**: `research.md` dengan catatan bahwa semua NEEDS CLARIFICATION telah diresolusi sebelumnya.

---

## Phase 1: Design & Contracts

### Data Model (`data-model.md`)

Entitas yang diekstrak dari feature spec:

| Entitas | Atribut Utama | Hubungan |
|---------|--------------|----------|
| CacheEntry | cache_key, query, summary, source_documents, created_at, ttl_seconds, hit_count | — |
| GraphNode | node_id, node_type (file/function/class/trait), file_path, symbol_name | — |
| GraphEdge | edge_id, from_node, to_node, edge_type (import/call/depends_on), weight | — |
| GraphTraversalResult | traversal_id, start_node, visited_nodes, edges_traversed, timestamp, status | — |
| CacheStats | total_hits, total_misses, eviction_count, cache_size | — |

State transitions:
- CacheEntry: created → hit (on retrieval) → expired (after TTL) → evicted (LRU)
- GraphTraversalResult: started → completed / failed
- GraphNode: created → updated (when file changes) → deleted (when file removed)

Validation rules:
- CacheEntry: cache_key harus unik, ttl_seconds harus > 0
- GraphEdge: from_node dan to_node harus valid (exist dalam GraphNode)
- GraphTraversalResult: start_node harus valid, status harus salah satu dari started/completed/failed

### Interface Contracts (`contracts/`)

HakoAgent mengekspos tool calling interface untuk caching dan graph traversal. Kontrak berikut didefinisikan:

**File**: `contracts/cache-graph-interface.md`

| Tool | Parameter | Return |
|------|-----------|--------|
| `hakoagent.cache.get` | query, limit | context_results, cache_hit (bool) |
| `hakoagent.cache.put` | query, summary, ttl_seconds | cache_key, status |
| `hakoagent.cache.stats` | — | total_hits, total_misses, eviction_count, cache_size |
| `hakoagent.graph.traverse` | start_node, direction, max_depth | visited_nodes, edges_traversed |
| `hakoagent.graph.shortest-path` | from_node, to_node | path_nodes, total_cost |
| `hakoagent.graph.dependents` | node_id | dependent_nodes |
| `hakoagent.graph.dependents-reverse` | node_id | dependent_reverse_nodes |
| `hakoagent.events` | limit, session_id | events_list (termasuk caching dan traversal events) |

Return value selalu dalam format JSON untuk kemudahan parsing oleh harness agent.

### Quickstart Validation Guide (`quickstart.md`)

**Prerequisites**:
- Python 3 (stdlib only, no external dependencies)
- Hak izin tulis di working directory proyek
- Database HakoDB sudah diinisialisasi (`./hakoagent init --db ./.hakoagent/hakoagent.db --collections all`)
- Prebuilt HakoDB library tersedia di `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` + header `lib/hakodb.h`

**Setup commands**:
```bash
# Inisialisasi database
./hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

**Test/run commands**:
```bash
# Uji cache
./hakoagent recall "error handling Rust"  # First call - LLM call
./hakoagent recall "error handling Rust"  # Second call - cache hit
./hakoagent cache stats                   # Lihat statistik cache

# Uji graph traversal
./hakoagent graph traverse func_a out 3
./hakoagent graph shortest-path func_a func_c
./hakoagent graph dependents n2
./hakoagent graph dependents-reverse n1

# Uji seluruh test suite
python3 test_hakoagent.py
```

**Expected outcomes**:
- `./hakoagent recall`: Kedua kali query sama → cache hit (tidak ada panggilan LLM)
- `./hakoagent cache stats`: Menampilkan total_hits, total_misses, eviction_count
- `./hakoagent graph traverse`: Mengembalikan semua node yang terhubung dari start_node
- `./hakoagent graph shortest-path`: Mengembalikan jalur terpendek dari from_node ke to_node
- `./hakoagent graph dependents`: Mengembalikan semua file yang mengimpor file tertentu
- `python3 test_hakoagent.py`: 31 tests passing

### Re-evaluate Constitution Check (post-design)

| Prinsip Konstitusi | Status Post-Design | Catatan |
|-------------------|-------------------|---------|
| Smart Memory | Terpenuhi | Hasil caching dan traversal disimpan di HakoDB |
| Anti-Lupa | Terpenuhi | Cache tetap tersimpan untuk reuse |
| Kronologi & Histori | Terpenuhi | Setiap operasi dicatat sebagai event append-only |
| Consistency | Terpenuhi | Template output standar |
| Cross-Model Consistency | Terpenuhi | Flow caching dan traversal sama untuk semua LLM |
| Vigilance | Terpenuhi | Deteksi cache expired, graph cycle |
| Clear Target | Terpenuhi | Setiap tugas caching dan traversal punya target dan DoD |
| Codebase Fluency | Terpenuhi | Graph traversal untuk navigasi codebase |
| Context Frugality | Terpenuhi | Cache mengurangi panggilan endpoint LLM |
| Self Skill Improvement | Terpenuhi | Pola caching dan traversal dapat diekstrak sebagai skill |

No violations. Constitution check PASSED post-design.

---

**Design artifacts siap: `research.md`, `data-model.md`, `contracts/cache-graph-interface.md`, `quickstart.md`**

Plan workflow selesai. Siap untuk dilanjutkan ke `/hakoagent-tasks`.
