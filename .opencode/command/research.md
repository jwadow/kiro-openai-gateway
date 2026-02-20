---
description: Research a topic or bead before implementation
argument-hint: "<topic-or-bead-id> [--quick|--thorough]"
agent: scout
---

# Research: $ARGUMENTS

Gather information before implementation. Find answers, document findings, stop when done.

> Research can happen at any phase when you need external information or codebase understanding.

## Load Skills

```typescript
skill({ name: "beads" });
// For --thorough mode:
skill({ name: "deep-research" });
```

## Parse Arguments

| Argument         | Default  | Description                         |
| ---------------- | -------- | ----------------------------------- |
| Topic or bead ID | required | What to research                    |
| `--quick`        | false    | ~10 tool calls, single question     |
| `--thorough`     | false    | ~100+ calls, comprehensive analysis |

Default depth: ~30 tool calls for moderate exploration.

## Determine Input Type

| Input Type | Detection                   | Action                            |
| ---------- | --------------------------- | --------------------------------- |
| Bead ID    | Matches `br-xxx` or numeric | Research within that bead context |
| Topic      | String                      | Standalone research               |

## Before You Research

- **Be certain**: Only research what you need for implementation
- **Don't over-research**: Stop when you have enough to proceed
- **Use source priority**: Codebase → Docs → Source → GitHub → Web
- **Verify confidence**: Medium+ confidence required before stopping
- **Document findings**: Write to research.md for beads, report for topics

## Available Tools

| Tool         | Use When                        |
| ------------ | ------------------------------- |
| `explore`    | Codebase patterns, LSP analysis |
| `scout`      | External docs, best practices   |
| `context7`   | Official API references         |
| `opensrc`    | Package source code inspection  |
| `codesearch` | Real-world usage examples       |
| `grepsearch` | GitHub code search              |

## Phase 1: Load Context

If argument is a bead ID:

```bash
br show $ARGUMENTS
```

Read PRD if it exists and extract questions that need answering.

Check memory for previous research on this topic.

## Phase 2: Research

### Source Priority

1. **Codebase patterns** — delegate to `explore` agent for LSP analysis
2. **Official docs** — `context7` for API references
3. **Source code** — `npx opensrc <package>` when docs are insufficient
4. **GitHub examples** — `codesearch` / `grepsearch` for real-world patterns
5. **Web search** — only if tiers 1-4 don't answer

### Delegation

| What              | Agent                        | When                                   |
| ----------------- | ---------------------------- | -------------------------------------- |
| Codebase analysis | `explore`                    | Internal patterns, file structure, LSP |
| External docs     | `scout` (this agent)         | Library APIs, best practices           |
| Multiple domains  | Parallel `explore` + `scout` | 3+ independent questions               |

### Confidence Levels

- **High**: Multiple authoritative sources agree, verified in codebase
- **Medium**: Single good source, plausible but unverified
- **Low**: Conflicting info, speculation — discard without corroboration

## Phase 3: Stop When

- All questions answered with medium+ confidence
- Tool budget exhausted for depth level
- Last 5 tool calls yielded no new insights
- Blocked and need human input

## Phase 4: Document

Write findings to `.beads/artifacts/$ARGUMENTS/research.md` (if bead) or report directly (if topic):

- Questions asked → answered/partial/unanswered with confidence
- Key findings with sources (file paths, docs)
- Recommendation based on findings
- Open items needing resolution

## Output

Report:

1. Depth level and tool call count
2. Questions with answer status and confidence
3. Key insights (bullet points)
4. Open items remaining
5. Next step suggestion

## Related Commands

| Need          | Command       |
| ------------- | ------------- |
| Create spec   | `/create`     |
| Plan details  | `/plan <id>`  |
| Start working | `/start <id>` |
