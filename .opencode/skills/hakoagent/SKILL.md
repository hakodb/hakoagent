---
name : hakoagent
description : >
  HakoAgent CLI reference — context caching with TTL, vector search (TF-IDF + cosine)
  across code_index/events/decisions/findings/skills, skills with dedup/refine/troubleshoot,
  tasks with target+DoD, vigilance checks, graph traversal (BFS/Dijkstra/dependents),
  impact analysis, bug scanning, and multi-agent team context.
license : MIT
compatibility : opencode
metadata :
  audience : agent
  workflow : memory-cache-graph-impact
---
# hakoagent

Standard pattern for using hakoagent CLI as agent memory and codebase understanding tool.
Call hakoagent via shell tool before starting tasks, during work for context caching, and
after completion for skill/task logging.

## Example Usage

```bash
# 1. Before starting work — vector search across ALL memory collections
hakoagent recall "error handling Rust" --limit 5

# 2. List available skills and tasks
hakoagent skill list
hakoagent task list

# 3. During work — store context in cache to reduce LLM calls
hakoagent cache put "my-query" "summary of findings" 300

# 4. After completing work — log skill and task (auto-extracts skill, dedupes)
hakoagent skill add "rust-error-handling-pattern"
hakoagent task create "Fix error handling" "All pub fn return Result" "Tests pass" P1
hakoagent task complete <task_id>

# 5. Refine a skill when you learn something new
hakoagent skill refine rust-error-handling-pattern "Also covers async error handling with ?"

# 6. Troubleshoot a skill that has issues
hakoagent skill troubleshoot rust-error-handling-pattern "Does not cover panic propagation"

# 7. Monitor codebase health
hakoagent vigilance
hakoagent events

# 8. Codebase dependency graph
hakoagent graph traverse <node> out 3
hakoagent graph shortest-path <from> <to>

# 9. Impact analysis before editing
hakoagent impact <file>

# 10. Scan for bug patterns
hakoagent bug_scan

# 11. Get recall suggestions
hakoagent suggest

# 12. Team context (multi-agent)
hakoagent team init --team "frontend" --members "alice,bob"
hakoagent team status
hakoagent team context
hakoagent team assign <task_id> <member>
```

## Usage Context

Use before every agent task session to load relevant context from memory. Vector search
(TF-IDF + cosine) searches code_index, events, decisions, findings, and skills collections
simultaneously. Use `cache put` after learning something new to avoid re-querying. Use
`vigilance` periodically to detect regressions.

## Lessons Learned

- Always run `hakoagent recall <query>` before manual codebase search — cache hit avoids
  LLM endpoint call
- Run `hakoagent index` after significant code changes to refresh dependency graph
- Every hakoagent command logs to `events` (append-only) — review with `hakoagent events`
- Run `hakoagent impact <file>` before editing to see blast radius (transitive dependents)
- Skills auto-deduplicate by name — completing the same task twice bumps success_count, not
  creates duplicate
- Use `skill refine` to update skills with new knowledge (creates new version, deprecates
  old)
- Use `skill troubleshoot` to flag issues; 3 failures auto-deprecates the skill
- Use `bug_scan` to find code quality issues (bare except, print debug, hardcoded secrets,
  eval/exec)
- Skills are stored as Markdown in `.hakoagent/skills/` and JSON in
  `.hakoagent/memory/skills/`
- Keep skills small (~300 char summary max) to avoid context bloat
