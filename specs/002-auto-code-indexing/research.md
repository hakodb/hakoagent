# Research Findings — Auto Codebase Indexing

**Feature**: 002-auto-code-indexing  
**Date**: 2026-10-29  
**Status**: Complete

## Unknowns Resolution

No NEEDS CLARIFICATION items remain. All parameters were resolved through the spec and prior clarifications:

| Unknown | Resolution | Source |
|---------|----------|--------|
| Startup scanning mechanism | Background thread within the agent process (not a separate process) | Clarification Session 2026-10-29 |
| Database not present vs. present | Full scan if absent, verify + update if present | Spec FR-001 |

## Technology Choices

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Rust 1.75+ as the core language | HakoDB is written in Rust, natural FFI compatibility, high performance | Python (slower for a file system watcher) |
| notify crate for file system watching | Cross-platform (Linux inotify, macOS FSEvents, Windows ReadDirectoryChangesW), mature | Custom polling (more resources), platform-specific API (not portable) |
| walkdir for directory traversal | Recursive, can filter directories, mature in the Rust ecosystem | Manual recursion (error-prone), std::fs::read_dir (not recursive) |
| HakoDB embedded (`--no-default-features`) | Light footprint, no server/daemon needed, suits an in-process agent | SQLite (no native vector/graph support), PostgreSQL (requires a server) |
| Background thread within the agent process | Simple, no extra process management, shares memory with the agent | Separate subprocess (requires IPC, more complex) |

## Integration Patterns

- **File system watching**: notify crate monitors file changes in real time
- **Background thread**: std::thread::spawn for startup scanning and the watcher loop
- **HakoDB integration**: Memory Service for read/write of the `code_index` collection
- **CLI integration**: `hakoagent init` starts the background thread automatically

## Best Practices

- Every indexed file is recorded as an append-only event in the `events` collection
- File hashes are used to detect changes (avoid re-indexing the same file)
- Ignored directories: node_modules, .git, target, .hakoagent, build output
- An error on one file does not stop indexing of other files
- A concise notification is sent to the agent after every indexing session finishes
