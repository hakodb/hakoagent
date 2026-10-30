# Tasks: Hakodb MCP Server (US12-US14)

**Input**: Design documents from `specs/010-hakodb-mcp-server/` (spec.md, plan.md)

**Prerequisites**: spec.md (required), plan.md (required)

**Organization**: Tasks are grouped by phase corresponding to the plan.md phases.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US12, US13, US14)
- Include exact file paths in descriptions

---

## Phase 0: Research

- [ ] T001 [P] [US12-US14] Verify Python stdlib has `json`, `sys`, `ctypes` for MCP server
- [ ] T002 [P] [US12-US14] Verify stdin/stdout JSON-RPC works in Python 3.6
- [ ] T003 [P] [US12-US14] Confirm stdin EOF detection works (`sys.stdin.readline()` returns `""` on EOF)

---

## Phase 1: MCP Server Core

- [ ] T004 [P] [US12] Implement `_mcp_json_rpc_loop()` — read stdin, parse JSON-RPC, dispatch, write stdout
- [ ] T005 [P] [US12] Implement `_mcp_tool_dispatch(method, params)` — route to existing hakoagent functions
- [ ] T006 [P] [US12] Implement `_mcp_shutdown(engine)` — free engine, stop net syncer, exit
- [ ] T007 [P] [US12] Implement `cmd_mcp(args)` — entry point for `hakoagent-mcp`
- [ ] T008 [P] [US12] Create `hakoagent-mcp` executable (copy of hakoagent with `--mcp` flag or symlink)
- [ ] T009 [P] [US12] Add `hakoagent-mcp` to `install.sh --global` installation
- [ ] T010 [US12] Add test: `hakoagent-mcp` starts and responds to `initialize`
- [ ] T011 [US12] Add test: `tools/list` returns all available tools
- [ ] T012 [US12] Add test: `tools/call save_doc` succeeds and document is stored
- [ ] T013 [US12] Add test: `tools/call load_doc` retrieves previously saved document (engine stayed loaded)
- [ ] T014 [US12] Add test: `shutdown` method causes server to exit
- [ ] T015 [US12] Add test: stdin EOF causes server to exit within 5 seconds

---

## Phase 2: Sync Integration

- [ ] T016 [US13] Implement `sync.enable` in MCP tool dispatch — call `hk_net_syncer_new`, `hk_net_syncer_set_discovery`, `hk_net_syncer_start`
- [ ] T017 [US13] Implement `sync.disable` in MCP tool dispatch — stop net syncer
- [ ] T018 [US13] Implement `sync.status` in MCP tool dispatch — call `hk_net_syncer_status`
- [ ] T019 [US13] Implement `sync.sync_now` in MCP tool dispatch — check syncer status
- [ ] T020 [US13] Implement `sync.backup` in MCP tool dispatch — call `hk_engine_backup`
- [ ] T021 [US13] Add test: `sync.enable` mesh starts net syncer successfully
- [ ] T022 [US13] Add test: `sync.status` returns enabled=true, type=mesh
- [ ] T023 [US13] Add test: `sync.sync_now` returns changes_synced count
- [ ] T024 [US13] Add test: `sync.disable` stops sync

---

## Phase 3: All HakoAgent Tools as MCP Tools

- [ ] T025 [US12-US14] Implement `save_doc` MCP tool
- [ ] T026 [US12-US14] Implement `load_doc` MCP tool
- [ ] T027 [US12-US14] Implement `recall` MCP tool
- [ ] T028 [US12-US14] Implement `cache_put` MCP tool
- [ ] T029 [US12-US14] Implement `cache_get` MCP tool
- [ ] T030 [US12-US14] Implement `cache_stats` MCP tool
- [ ] T031 [US12-US14] Implement `events` MCP tool
- [ ] T032 [US12-US14] Implement `revision.list` MCP tool
- [ ] T033 [US12-US14] Implement `graph.traverse` MCP tool
- [ ] T034 [US12-US14] Implement `graph.shortest_path` MCP tool
- [ ] T035 [US12-US14] Implement `graph.impact` MCP tool
- [ ] T036 [US12-US14] Implement `graph.search` MCP tool
- [ ] T037 [US12-US14] Implement `graph.query` MCP tool
- [ ] T038 [US12-US14] Implement `graph.detect_changes` MCP tool
- [ ] T039 [US12-US14] Implement `graph.get_snippet` MCP tool
- [ ] T040 [US12-US14] Implement `graph.architecture` MCP tool
- [ ] T041 [US12-US14] Implement `graph.adr.add/list/get` MCP tools
- [ ] T042 [US12-US14] Implement `graph.ingest_traces` MCP tool
- [ ] T043 [US12-US14] Implement `graph.list_projects` MCP tool
- [ ] T044 [US12-US14] Implement `graph.delete_project` MCP tool
- [ ] T045 [US12-US14] Implement `skill.list/add/refine/troubleshoot/get` MCP tools
- [ ] T046 [US12-US14] Implement `task.list/create/complete` MCP tools
- [ ] T047 [US12-US14] Implement `vigilance` MCP tool
- [ ] T048 [US12-US14] Implement `bug_scan` MCP tool
- [ ] T049 [US12-US14] Implement `team.init/status/assign/context` MCP tools

---

## Phase 4: Session Lifecycle

- [ ] T050 [US13] Test: server exits when stdin EOF (agent disconnects)
- [ ] T051 [US13] Test: net syncer stopped before server exit on shutdown
- [ ] T052 [US13] Test: engine freed on server shutdown
- [ ] T053 [US13] Test: cloud sync enable/disable works in MCP session
- [ ] T054 [US13] Test: local-only collections respected in MCP sync

---

## Phase 5: Polish

- [ ] T055 [US12-US14] Run full test suite: 89+ tests passing
- [ ] T056 [US12-US14] Run `hakoagent bug_scan` on MCP server code
- [ ] T057 [US12-US14] Run `hakoagent vigilance` — constitution check pass
- [ ] T058 [US12-US14] Reinstall globally via `./install.sh --global`
- [ ] T059 [US12-US14] End-to-end validation: start `hakoagent-mcp`, send multiple tool calls, verify engine stays loaded, close stdin, verify server exits
- [ ] T060 [US12-US14] Update `AGENTS.md` with MCP server usage
- [ ] T061 [US12-US14] Update module docstring with `hakoagent-mcp` command

---

**Design artifacts ready**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/mcp-server-interface.md`, `quickstart.md`

Plan workflow complete. Ready to proceed to `/speckit-implement`.
