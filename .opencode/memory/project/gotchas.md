---
purpose: Footguns, edge cases, and warnings discovered during development
updated: 2026-02-12
---

# Gotchas

Track unexpected behaviors, edge cases, and warnings here. Update when you hit something surprising.

## LLM Coding (Harness Problem)

The edit tool (`str_replace`) is the #1 source of failures in LLM coding. Models fail at reproducing content with exact whitespace/encoding, not at understanding tasks.

### Edit Tool Failures

- **Whitespace mismatch** — Tabs vs spaces, trailing spaces, line endings (CRLF vs LF)
- **Content changed** — File modified since last read
- **Multiple matches** — Same string appears twice, edit fails
- **Stale context** — Editing from memory instead of fresh read

### Mitigation Strategies

1. **Always read fresh** before editing — no assumptions
2. **Use LSP tools** to locate symbols precisely (goToDefinition, findReferences)
3. **Include unique context** — 2-3 lines before/after for uniqueness
4. **Prefer smaller files** — <400 lines reduces edit complexity
5. **Verify after edit** — read back to confirm success

### File Size Guidance

| Size          | Strategy                                   |
| ------------- | ------------------------------------------ |
| < 100 lines   | Full rewrite often easier than str_replace |
| 100-400 lines | Structured edit with good context          |
| > 400 lines   | Strongly prefer structured edits           |

**Use the `structured-edit` skill for reliable edits.**

### Context Hygiene

- Distill large tool outputs immediately after use
- Prune irrelevant reads before proceeding
- Token budget: <50k start → 50-100k mid → >150k restart session
- Subagent outputs can leak tokens — be aggressive about distilling

## OpenCode Config

- **`compaction` key invalid**: Not in official schema at opencode.ai/config.json. Remove if present.
- **`experimental` key invalid**: Not in schema. Remove if present.
- **`tools` key invalid**: Not in schema. Remove if present.
- **`formatter` valid but undocumented**: Works but missing from schema (schema incomplete).

## Memory System

- Subagents (explore, scout, review) should NOT write to memory - only leader agents
- Use `observation: false` and `memory-update: false` in agent configs to enforce

## Build System

- `dist/` is generated - never edit directly
- Build copies `.opencode/` to `dist/template/` via rsync
- Run `npm run build` to regenerate

## Beads

- Only leader agents (build, plan) should modify beads state
- Subagents read with `br show <id>`, report findings back
