# Feature Specification: System Caching dan Graph Traversal Tools

**Feature Branch**: `003-cache-graph-system`

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "implementasi system caching, fitur dan tools graph traversal"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agen menggunakan cache konteks untuk mengurangi panggilan endpoint LLM (Priority: P1)

Sistem secara otomatis menyimpan hasil pencarian konteks dan rangkuman dalam cache agar agen tidak perlu memanggil endpoint LLM berulang kali untuk query yang sama atau serupa.

**Why this priority**: Mengurangi biaya dan latency endpoint LLM, serta meningkatkan kecepatan respons agen.

**Independent Test**: Dapat diuji secara independen dengan melakukan query yang sama dua kali dan memverifikasi bahwa panggilan kedua berasal dari cache, bukan endpoint LLM.

**Acceptance Scenarios**:

1. **Given** cache kosong, **When** agen melakukan query pertama kali, **Then** sistem memanggil endpoint LLM dan menyimpan hasilnya ke cache
2. **Given** cache sudah memiliki hasil query, **When** agen melakukan query yang sama, **Then** sistem mengembalikan hasil dari cache tanpa memanggil endpoint LLM
3. **Given** cache sudah expired (ttl habis), **When** agen melakukan query yang sama, **Then** sistem memanggil endpoint LLM lagi dan memperbarui cache

---

### User Story 2 - Agen menjelajahi graph dependensi codebase (Priority: P1)

Agen dapat menavigasi dan menelusuri dependensi antar simbol, file, dan komponen dalam codebase menggunakan graph traversal (BFS, Dijkstra, dependents lookup).

**Why this priority**: Memahami struktur codebase dan dampak perubahan adalah kritikal untuk pengembangan yang aman dan efisien.

**Independent Test**: Dapat diuji secara independen dengan memulai traversal dari simbol tertentu dan memverifikasi bahwa semua node terhubung ditemukan dengan benar.

**Acceptance Scenarios**:

1. **Given** codebase sudah diindex, **When** agen meminta dependents dari file X, **Then** sistem mengembalikan semua file yang mengimpor atau menggunakan file X
2. **Given** dua simbol dalam codebase, **When** agen mencari jalur terpendek antar keduanya, **Then** sistem mengembalikan rantai dependensi terpendek
3. **Given** simbol awal dan depth maksimum, **When** agen melakukan traversal BFS, **Then** sistem mengembalikan semua node yang dapat dijangkau dalam depth tersebut

---

### User Story 3 - Agen menerima notifikasi dan laporan setelah operasi caching dan graph traversal (Priority: P2)

Setiap kali operasi caching dan graph traversal selesai, agen mendapat notifikasi ringkas tentang apa yang diproses dan apakah ada error.

**Why this priority**: Memberi agen visibilitas ke status operasi internal tanpa perlu memeriksa secara manual.

**Independent Test**: Dapat diuji secara independen dengan memicu perubahan file atau query cache lalu memverifikasi bahwa notifikasi muncul.

**Acceptance Scenarios**:

1. **Given** cache hit occurs, **When** operasi selesai, **Then** agen menerima notifikasi ringkas (jumlah file, status sukses/error)
2. **Given** graph traversal selesai, **When** operasi selesai, **Then** agen menerima ringkasan jumlah node dan edge yang dijelajahi
3. **Given** operasi gagal, **Then** agen menerima notifikasi error untuk operasi tersebut tanpa menghentikan operasi lainnya

---

### Edge Cases

- Cache penuh: sistem harus mengeluarkan entri terlama (LRU eviction)
- Graph dengan siklus: traversal tidak boleh terjebak dalam loop tak terbatas
- File yang dihapus saat graph sedang ditraverse: sistem harus menangani graceful degradation
- Query kosong atau tidak valid: sistem mengembalikan error yang informatif
- Direktori yang tidak ada: sistem memberikan error yang jelas
- File dengan ekstensi yang tidak didukung: dilewati saat indexing untuk graph

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistem MUST menyimpan hasil pencarian konteks dan rangkuman dalam koleksi `context_cache` dengan TTL konfigurabel. Default TTL adalah 300 detik (5 menit). Setelah TTL habis, entri cache dianggap expired dan sistem harus mengambil ulang dari endpoint LLM.
- **FR-002**: Sistem MUST melakukan cache lookup sebelum memanggil endpoint LLM untuk query yang sama atau serupa
- **FR-003**: Sistem MUST menyediakan graph traversal (BFS/DFS) untuk menelusuri dependensi codebase dari koleksi `code_index`
- **FR-004**: Sistem MUST menyediakan shortest path (Dijkstra) antara dua simbol dalam codebase
- **FR-005**: Sistem MUST menyediakan dependents lookup (siapa yang mengimpor/menggunakan file atau fungsi X)
- **FR-006**: Sistem MUST menyediakan dependents reverse (apa saja yang dipanggil oleh file atau fungsi X)
- **FR-007**: Sistem MUST menangani siklus dalam graph tanpa terjebak dalam loop tak terbatas (visited set)
- **FR-008**: Sistem MUST memberikan notifikasi kepada agen setelah setiap operasi caching dan graph traversal selesai atau gagal
- **FR-009**: Sistem MUST tidak memiliki referensi ke tool eksternal seperti hakoagent di seluruh kode dan dokumentasi
- **FR-010**: Sistem MUST menyimpan semua file terkait hakoagent di bawah direktori `.hakoagent/` atau root proyek

### Key Entities *(include if feature involves data)*

- **CacheEntry**: Entri cache dengan cache_key, query, summary, source_documents, created_at, ttl_seconds, hit_count
- **GraphNode**: Node dalam graph codebase dengan node_id, node_type (file/function/class/trait), file_path, symbol_name
- **GraphEdge**: Edge dalam graph dengan edge_id, from_node, to_node, edge_type (import/call/depends_on), weight
- **GraphTraversalResult**: Hasil traversal dengan traversal_id, start_node, visited_nodes, edges_traversed, timestamp, status
- **CacheStats**: Statistik cache dengan total_hits, total_misses, eviction_count, cache_size

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cache hit ratio ≥ 50% untuk query yang sering diulang
- **SC-002**: Waktu respons cache hit < 100ms
- **SC-003**: Graph traversal depth maksimal 10 level tanpa degradasi performa signifikan
- **SC-004**: 0 entri cache yang expired masih digunakan
- **SC-005**: 0 referensi ke "hakoagent" ditemukan di seluruh file sumber, dokumentasi, dan konfigurasi proyek
- **SC-006**: Semua file terkait hakoagent disimpan di bawah direktori `.hakoagent/` atau root proyek

## Assumptions

- HakoDB sudah diinisialisasi sebelum caching dan graph traversal berjalan
- Codebase sudah diindex melalui fitur auto codebase indexing (fitur 002)
- File system watcher tersedia untuk mendeteksi perubahan codebase
- Format file yang didukung untuk graph traversal adalah source code (.rs, .py, .js, .ts, .go, dll.)

---

## Clarifications

### Session 2026-10-29

- Q: Berapa detik waktu kedaluwarsa (TTL) default untuk entri cache konteks sebelum sistem harus mengambil ulang dari endpoint LLM? → A: 300 detik (5 menit)

---
