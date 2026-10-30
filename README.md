# HakoAgent

HakoAgent is an agent memory, skill, and code-graph engine backed by the HakoDB
embedded database. It gives coding agents — OpenCode, Claude Code, or your own
harness — persistent context across sessions while keeping LLM token use low.

## What it does

- **Memory** — save/recall decisions, findings, and notes with vector search (TF-IDF +
  cosine) and full-text retrieval over a local hakodb database.
- **Skills** — completed tasks auto-extract into reusable skills with deduping, refine,
  and troubleshoot flows.
- **Code graph** — index a codebase into a dependency graph: traversal, shortest path,
  blast radius analysis, coverage gaps, architecture summaries.
- **Context cache** — TTL'd cache so repeated questions cost one local call, zero LLM calls.
- **Tasks & events** — task tracking with targets and definitions of done; append-only
  event log of every agent action.
- **MCP server** — serves all of the above over stdio JSON-RPC; off by default, enabled
  per project.
- **Multi-agent** — team context and sync primitives for a group of agents on one project.

Everything runs locally: one Python stdlib file plus the hakodb native library.
No server, no telemetry, no cloud — unless you enable sync yourself.

## Install

```sh
git clone https://github.com/hakodb/hakoagent.git
cd hakoagent
python install.py              # project-local install in the current project
# or: python install.py --global   # install into your bin dir + skills/commands
```

The installer downloads the matching native hakodb library from the
[hakodb releases](https://github.com/hakodb/hakodb/releases) and verifies it (Windows x86_64
and Linux x86_64; other platforms are not supported yet — hakoagent requires the native
engine and does not fall back to anything else).

## Quick start

```sh
hakoagent index              # index your codebase
hakoagent recall "query"     # retrieve context instead of searching by hand
hakoagent impact src/main.rs # blast radius before you edit
hakoagent cache stats        # see how much context was saved
```

Full command reference, MCP integration, and the agent-instruction template:
see the docs below.

## Documentation

- Full manual: <https://hakodb.github.io/docs/hakoagent.html>
- Agent connection guide: [`assets/AGENTS.md`](assets/AGENTS.md) (copied into your project by the installer)
- Installation details: [`INSTALL.md`](INSTALL.md)
- Compatible engine: <https://github.com/hakodb/hakodb>

## License

Same as the HakoDB project — MIT.
