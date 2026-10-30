# Quickstart — Hakodb MCP Server (US12-US14)

**Feature**: 010-hakodb-mcp-server  
**Date**: 2026-10-29  
**Status**: Draft

## Prerequisites

- Python 3 (stdlib only, no external dependencies)
- Prebuilt hakodb library at `lib/libhakodb-x86_64-unknown-linux-glibc2.28-el8.so` + header `lib/hakodb.h`
- Write permission in working directory

## Setup

```bash
# Install HakoAgent globally (installs hakoagent, hakoagent-mcp, hakoagent-cli)
./install.sh --global

# Add to PATH
export PATH="$HOME/.local/bin:\$PATH"

# Verify installation
hakoagent --help
hakoagent-mcp --help
hakoagent-cli --help

# Initialize database (project root)
./hakoagent init --db ./.hakoagent/hakoagent.db --collections all
```

## Validation Scenarios

### 1. Start MCP server and initialize

```bash
# Start the MCP server (blocks, waiting for stdin)
./hakoagent-mcp

# In another terminal, send initialize
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"capabilities":{}}}' | ./hakoagent-mcp
```

**Expected**: Server starts, returns initialize result with capabilities

### 2. List available tools

```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | ./hakoagent-mcp
```

**Expected**: Returns list of all available MCP tools with input schemas

### 3. Save and load a document (engine stays loaded)

```bash
# Save a document
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"save_doc","arguments":{"collection":"findings","doc_id":"f1","doc":{"content":"test finding","actor":"agent-a"}}}}' | ./hakoagent-mcp

# Load the same document (engine stays loaded from previous call)
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"load_doc","arguments":{"collection":"findings","doc_id":"f1"}}}' | ./hakoagent-mcp
```

**Expected**: Both calls succeed in the same session (engine stayed loaded between calls)

### 4. Enable sync and sync-now (net syncer stays alive)

```bash
# Enable mesh sync
echo '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"sync.enable","arguments":{"type":"mesh","room_key":"test-room","port":9900,"actor":"agent-a"}}}' | ./hakoagent-mcp

# Check status
echo '{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"sync.status","arguments":{}}}' | ./hakoagent-mcp

# Sync now
echo '{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"sync.sync_now","arguments":{}}}' | ./hakoagent-mcp
```

**Expected**: Sync stays enabled across multiple calls (net syncer stayed alive)

### 5. Shutdown server gracefully

```bash
echo '{"jsonrpc":"2.0","id":8,"method":"shutdown","params":{}}' | ./hakoagent-mcp
```

**Expected**: Server shuts down cleanly, engine freed, net syncer stopped

### 6. Server shuts down on stdin EOF

```bash
# Start server in background
./hakoagent-mcp &
MCP_PID=$!

# Send a command
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"cache_stats","arguments":{}}}' | ./hakoagent-mcp

# Close stdin (no shutdown message)
echo '' | ./hakoagent-mcp

# Server exits after stdin EOF
# Verify server is gone
ps aux | grep hakoagent-mcp | grep -v grep
```

**Expected**: Server exits within 5 seconds of stdin closing

### 7. Test with agent-like workflow

```bash
# Agent workflow: save, recall, graph trace, sync
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"save_doc","arguments":{"collection":"findings","doc_id":"bug_1","doc":{"content":"null pointer","actor":"agent-a"}}}}' | ./hakoagent-mcp

echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"recall","arguments":{"query":"null pointer","actor":"agent-a"}}}' | ./hakoagent-mcp

echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"graph.traverse","arguments":{"node":"hakoagent","direction":"outbound","depth":3}}}' | ./hakoagent-mcp

echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"sync.enable","arguments":{"type":"mesh","room_key":"team-room","actor":"agent-a"}}}}' | ./hakoagent-mcp
```

**Expected**: All calls succeed in one session — engine and net syncer stay loaded

### 8. Full test suite

```bash
python3 test_hakoagent.py
```

**Expected**: All tests pass

### 9. Verify `hakoagent-mcp` is installed globally

```bash
which hakoagent-mcp
# Output: ~/.local/bin/hakoagent-mcp

hakoagent-mcp --help
# Output: HakoAgent MCP Server — JSON-RPC 2.0 over stdio
```

**Expected**: `hakoagent-mcp` is available globally

---
