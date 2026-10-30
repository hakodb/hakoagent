# Research — Hakodb MCP Server (US12-US14)

**Feature**: 010-hakodb-mcp-server  
**Date**: 2026-10-29  
**Status**: Draft

## MCP Protocol Analysis

### What is MCP?

Model Context Protocol (MCP) is a standard for connecting AI assistants to tools and data sources. It uses JSON-RPC 2.0 over various transports, with stdio being the simplest and most common for local servers.

### MCP Protocol Basics

| Aspect | Detail |
|--------|--------|
| Transport | Stdio (stdin = client→server, stdout = server→client) |
| Protocol | JSON-RPC 2.0 |
| Message format | One JSON object per line |
| Core methods | `initialize`, `initialized`, `tools/list`, `tools/call`, `shutdown`, `cancelRequest` |
| Notifications | `initialized`, `cancelRequest`, `progress` (no response expected) |
| Requests | `initialize`, `tools/list`, `tools/call`, `shutdown` (response expected) |

### Why MCP for HakoAgent?

The current hakoagent CLI has a fundamental limitation: each command spawns a new Python process, opens the hakodb engine, does work, and exits. This means:

1. **No cross-call context**: Each `hakoagent recall` call re-opens the engine, re-reads JSON files
2. **No persistent sync**: `hk_net_syncer_start` needs time to discover peers via mDNS/UDP. A CLI invocation opens, starts syncer, and exits immediately — sync never completes
3. **No continuous index**: `hakoagent index` builds the graph but the engine closes immediately

An MCP server solves this by staying alive:
- Engine opens once, stays loaded for session lifetime
- Net syncer starts once, maintains peer connections
- Multiple tool calls share the same engine instance
- Server shuts down when agent disconnects (stdin EOF)

### MCP Server Architecture for HakoAgent

```
┌─────────────────────────────────────────────────────────┐
│  Agent Process                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Agent sends JSON-RPC tool calls over stdin     │   │
│  │  Agent reads JSON-RPC responses from stdout     │   │
│  └─────────────────────────────────────────────────┘   │
│                           │                             │
│                           │ stdin/stdout                │
│                           ▼                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │  hakoagent-mcp server                           │   │
│  │  ┌─────────────────────────────────────────┐   │   │
│  │  │  HK Engine (opened once, stays alive)   │   │   │
│  │  │  HK NetSyncer (started on sync.enable)  │   │   │
│  │  │  Tool registry (all hakoagent commands) │   │   │
│  │  └─────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Why Not a Custom Daemon?

A custom daemon would require:
- Socket/pipe communication (Unix socket on Linux/macOS, named pipes on Windows)
- Connection management, reconnection logic
- Process lifecycle management

MCP over stdio is simpler:
- Stdio works identically on Linux, macOS, Windows
- No socket management, no reconnection logic
- Process lifecycle is tied to the parent (when agent exits, stdin closes, server exits)
- JSON-RPC 2.0 is a well-known standard

### MCP vs HTTP Server

| Aspect | MCP (stdio) | HTTP Server |
|--------|-------------|-------------|
| Transport | stdin/stdout | TCP port |
| Cross-platform | ✅ Identical on all platforms | ✅ Works everywhere |
| Process lifecycle | Tied to parent process | Independent daemon |
| Connection management | None (stdio is automatic) | Socket management needed |
| Firewall issues | None | May be blocked |
| Complexity | Low | Medium |

MCP over stdio is the simplest cross-platform option.

---

## Implementation Plan

### Files to Modify

1. **`hakoagent`** — Add `cmd_mcp()` function and `_mcp_json_rpc_loop()`
2. **`hakoagent-mcp`** — New executable (copy of hakoagent with `--mcp` flag, or symlink)
3. **`install.sh`** — Install `hakoagent-mcp` alongside `hakoagent`

### Files to Create

1. **`specs/010-hakodb-mcp-server/`** — All spec documents (this feature)

### Implementation Steps

1. Add `_mcp_json_rpc_loop()` — reads stdin lines, parses JSON-RPC, dispatches, writes stdout
2. Add `_mcp_tool_dispatch(method, params)` — routes to existing hakoagent functions
3. Add `_mcp_shutdown()` — frees engine, stops net syncer, exits
4. Add `cmd_mcp(args)` — entry point for `hakoagent-mcp`
5. Add `hakoagent-mcp` to install script
6. Add tests for MCP server functionality
7. Run full test suite

### MCP Server Implementation Sketch

```python
def cmd_mcp(args):
    """Entry point for hakoagent-mcp. Runs as JSON-RPC 2.0 server over stdio."""
    _ensure_dirs()
    engine = _get_engine()  # Open once, keep alive
    if not engine:
        print(json.dumps({"jsonrpc":"2.0","error":{"code":-32603,"message":"Cannot open hakodb engine"}}))
        return 1
    
    # Read stdin line by line, process JSON-RPC
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            result = _mcp_handle_request(req, engine)
            if "id" in req:
                print(json.dumps({"jsonrpc":"2.0","id":req.get("id"),"result":result}))
                sys.stdout.flush()
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc":"2.0","id":None,"error":{"code":-32700,"message":"Parse error"}}))
            sys.stdout.flush()
    
    # Stdin EOF — shutdown
    _mcp_shutdown(engine)
    return 0

def _mcp_handle_request(req, engine):
    method = req.get("method", "")
    params = req.get("params", {})
    
    if method == "initialize":
        return {"capabilities": {"tools": True}}
    elif method == "tools/list":
        return {"tools": _mcp_tool_list()}
    elif method == "tools/call":
        name = params.get("name", "")
        arguments = params.get("arguments", {})
        return _mcp_tool_call(name, arguments)
    elif method == "shutdown":
        return {}
    else:
        raise Exception(f"Method not found: {method}")
```

---

## Output

`research.md` documents the MCP protocol analysis and server design.
