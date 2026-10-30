# Research Findings — Refactor HakoAgent to Constitution

**Feature**: 001-refactor-hakoagent  
**Date**: 2026-10-29  
**Status**: Complete

## Unknowns Resolution

No NEEDS CLARIFICATION items remain. All technical parameters were resolved through the spec and prior clarifications:

| Unknown | Resolution | Source |
|---------|----------|--------|
| Append-only mechanism on the events collection | Application-level guard (code checks event_id before write) | Clarification Session 2026-10-29 |
| Skill format | Markdown (`.md`) under `.hakoagent/skills/` | Constitution Section 4 + Spec FR-005 |
| HakoDB database location | `.hakoagent/hakoagent.db` | Constitution Section 3 |

## Technology Choices

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Rust 1.75+ as the core language | HakoDB is written in Rust, high performance, memory safe, mature ecosystem | Python (slower for an embedded DB), Go (adequate but Rust is more natural for HakoDB FFI) |
| cbindgen for C ABI generation | Standard in the Rust ecosystem, generates `hakodb.h` automatically | Hand-write the C header (error-prone, hard to keep in sync) |
| HakoDB embedded (`--no-default-features`) | Light footprint, no server/daemon needed, suits an in-process agent | SQLite (no native vector/graph support), PostgreSQL (requires a server) |
| Markdown for skills | Easy for humans/agents to read, version control friendly, code examples with syntax highlighting | YAML (poor fit for long code examples), JSON (less readable) |
| Application-level append-only guard | Practical for an embedded DB, clear error messages, requires no special HakoDB feature | Database-level constraint (unavailable in HakoDB 0.19), File-system immutable (not portable) |

## Integration Patterns

- **Tool calling interface**: Each tool is exposed with the name `hakoagent.<command>`, defined parameters, JSON return
- **FFI/C ABI**: HakoDB shared library via cbindgen, Rust wrappers for host languages (Go, Python, JS/TS)
- **CLI**: `hakoagent` binary with subcommands (init, index, recall, skill, task, events, vigilance)

## Best Practices

- All events are written append-only with ISO 8601 timestamps
- Skills are stored as separate Markdown files for easy editing and version control
- Every task must have a measurable target and definition_of_done
- No references to external tools (hakoagent) anywhere in code or documentation
- All hakoagent-related files live under `.hakoagent/` or the project root
