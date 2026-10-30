# HakoAgent — Hakodb Sync Path Research

## 1. Hakodb v0.20.0 — What It Is

Based on research of https://github.com/hakodb/hakodb and https://hakodb.github.io/docs:

| Attribute | Value |
|-----------|-------|
| **Type** | Embedded document database (library, not server) |
| **Language** | Rust |
| **Latest version** | 0.20.0 |
| **Storage model** | Typed JSON-like documents in collections, WAL + tiered-segment |
| **C ABI** | Flat opaque handles: `HK_Engine`, `HK_Doc`, `HK_Query`, `HK_Batch`, `HK_Transaction`, `HK_Watch`, `HK_ResultSet` |
| **Query** | `where/orderBy/limit`, eq/ne/gt/gte/lt/lte/in/notIn/arrayContains/match/contains/startsWith |
| **Indexes** | B-Tree, composite, FTS, HNSW vector (KNN), graph backlinks (BFS + Dijkstra) |
| **Durability** | WAL + tiered-segment storage, configurable (`Always`/`Interval`/`Manual`/`OnCommit`) |
| **Encryption** | ChaCha20-Poly1305 for WAL and segment payloads |
| **Change stream** | `watch_collection()` — real-time change notifications |

## 2. Sync Capabilities in v0.20.0

Hakodb has **two optional sync features**, both additive behind feature flags:

| Feature | Transport | Topology | Best For |
|---------|-----------|----------|----------|
| `net-sync` | LAN mDNS + delta replication | Peer-to-peer mesh | Real-time collaboration on one LAN |
| `cloud-sync` | WebSocket + MessagePack | Client-server hub | Offline-first apps syncing to a backend |

### Key sync characteristics:

1. **Rooms isolate data** — `room_name` + `room_key` pair; wrong-room handshakes rejected before data moves
2. **Index definitions replicate** — but derived state (HNSW graphs, backlink indexes) **rebuilds locally** from replicated documents
3. **No on-disk format change** — sync features are additive (no breaking changes)
4. **No automatic multi-master conflict resolution** — last-writer-wins implied; application must handle conflicts
5. **Cloud sync server is room-agnostic** — hosts any room; server uses `<prefix>_<collection>` storage names
6. **Encryption posture** — at-rest encryption and sync-time plaintext are **independent**; encrypted collections replicate as plaintext on wire unless E2E room keys match

### What sync does NOT do:
- No automatic conflict resolution for concurrent edits to the same document
- No built-in user authentication beyond room keys
- No built-in presence/awareness (who is online)
- No automatic task assignment or workload balancing

## 3. Sync Architecture for HakoAgent

Since hakodb is **embedded (in-process)**, hakoagent itself is the database host. Two agents cannot share a single `.hakoagent/` directory simultaneously (embedded DB = single writer). Team collaboration requires **application-level sync**:

```
┌─────────────────┐      net-sync mesh        ┌─────────────────┐
│   Agent A       │◀──────────────────────────│   Agent B       │
│  (Python)       │   (hakodb net-sync)       │  (Python)       │
│   .hakoagent/   │◀──────────────────────────│   .hakoagent/   │
│   memory/       │   (delta replication)     │   memory/       │
│   events/       │◀──────────────────────────│   events/       │
│   code_index/   │                           │   code_index/   │
└─────────────────┘                           └─────────────────┘
         ▲                                          ▲
         │                                          │
         └────── cloud-sync hub (optional) ─────────┘
                    (WebSocket hub for remote agents)
```

### Data flow for team context:

1. **Agent A** completes a task → `task_complete` event → hakodb `watch_collection("events")` fires → delta replicated via net-sync/cloud-sync → Agent B's `events` collection updated → Agent B's `suggest()` can recommend recalling that task's context
2. **Agent B** indexes a new file → `code_index` entry → synced to Agent A → Agent A's `graph traverse` sees new dependencies
3. **Agent C** creates a skill → `skills` collection entry → synced → Agent A's `recall` can recommend it

### Conflict handling (application level):

| Conflict Type | Detection | Resolution |
|--------------|-----------|------------|
| Two agents edit same task | `assignee` differs, `completed_at` differs | Last-write-wins by `completed_at` timestamp; loser notified |
| Two agents create same skill name | Dedup check by name | Bump `success_count`, don't duplicate |
| Two agents index same file | Hash mismatch on re-index | Latest hash wins; re-index on change |
| Two agents edit same skill | Version field differs | Higher version wins; older marked `deprecated` |

## 4. Team/Group Context Design

### New Collections (existing 9 + new):

| Collection | Purpose | Team-relevant fields |
|-----------|---------|---------------------|
| `sessions` | Per-agent session | `agent_name`, `agent_type` ("harness"/"human"/"subagent") |
| `events` | Append-only log | `actor` (agent name), `action`, `target`, `metadata` |
| `tasks` | Task board | `assignee` (member name), `created_by`, `priority`, `status` |
| `skills` | Shared skill library | `name` (dedup key), `version`, `status` (active/deprecated), `success_count`, `failure_count`, `issues` |
| `code_index` | Symbol/dependency index | `file_path`, `symbol_name`, `dependinsi`, `file_hash` |
| `context_cache` | Per-agent cache | Not shared (local-only) |
| `decisions` | Architecture decisions | `actor`, `rationale`, `consequence` |
| `findings` | Codebase findings | `actor`, `severity`, `status` |
| `lessons_learned` | Failure patterns | `actor`, `task_id`, `lesson` |

### New metadata (team.json in `.hakoagent/team/`):

```json
{
  "team_name": "frontend-team",
  "members": ["alice", "bob", "charlie"],
  "remote": "https://cloud.hakodb.example/rooms/frontend",
  "room_name": "frontend-team",
  "room_key": "...",
  "created_at": "...",
  "sync_mode": "cloud-sync"
}
```

### New Commands:

| Command | Purpose |
|---------|---------|
| `hakoagent team init --team <name> --members <a,b,c> [--remote <url>]` | Initialize team metadata |
| `hakoagent team status` | Show who's online, task assignments, active skills |
| `hakoagent team sync [--push|--pull]` | Push/pull changes via hakodb sync |
| `hakoagent team assign <task_id> <member>` | Assign task to member |
| `hakoagent team context` | Show shared context summary |

## 5. Implementation Strategy (Ponytail: Minimum That Works)

### Phase 1: Task Ownership (no hakodb sync needed)
- Add `assignee` field to tasks
- Add `agent_name` to sessions
- `hakoagent team init/status/assign/context` — JSON file ops, no sync
- `hakoagent task complete` auto-extracts skill with dedup (already implemented)

### Phase 2: Hakodb Sync Integration
- Add `hakodb = { version = "0.20", features = ["net-sync"] }` dependency
- `hakoagent team sync` — push/pull via hakodb sync API
- Watch `watch_collection("events")` → replicate changes to remote

### Phase 3: Real-time Collaboration
- `watch_collection` event listener → push to team members
- Conflict detection on concurrent edits
- Presence awareness (who is online)

## 6. YAGNI Boundaries (What We Are NOT Building)

| Item | Reason |
|------|--------|
| Multi-master database replication | hakodb embedded = single writer per process |
| User authentication/authorization | Filesystem permissions + room keys suffice |
| Automatic conflict resolution | Requires semantic understanding; manual review safer |
| WebRTC / WebSocket server | Cloud sync server exists separately; hakoagent is client |
| Distributed consensus (Raft/Paxos) | Not needed for embedded DB per-agent |

## 7. Implementation Priority

1. **Immediate**: `team init/status/assign/context` (JSON-only, no sync dependency)
2. **Next**: Add `hakodb = "0.20"` with `net-sync` feature; `team sync` command
3. **Later**: `watch_collection` replication for real-time awareness
4. **Later**: Cloud sync hub for remote agents

## Files to Modify

- `hakoagent` — add `cmd_team()` + `cmd_task` assignee field + session `agent_name`
- `AGENTS.md` — document team workflow
- `.opencode/skills/hakoagent-usage-pattern/SKILL.md` — update with team commands
- `install.sh` — no changes needed
- `specs/004-team-context/spec.md` — this document

---

**PONYTAIL**: Team context uses Git file sync + JSON metadata — simple, offline-first, zero dependencies.

**Ceiling**: Not real-time, merge conflicts possible on same-doc edits, no automatic conflict resolution.

**Upgrade path**: Add `hakodb` sync features (`net-sync`/`cloud-sync`) for real-time replication between agents.