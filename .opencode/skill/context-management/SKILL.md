---
name: context-management
description: Use when context is growing large, needing to prune/distill tool outputs, or managing conversation size - covers DCP slash commands and context budgets
---

# Context Management

Manage conversation context to prevent degradation. Uses DCP plugin.

## DCP Integration

This project uses the **DCP (Dynamic Context Pruning)** plugin. Prefer slash commands over tool calls for better reliability.

### Slash Commands (Recommended)

| Command                 | Purpose                                  | When to Use                         |
| ----------------------- | ---------------------------------------- | ----------------------------------- |
| `/dcp compress [focus]` | Collapse conversation range into summary | Phase complete, research done       |
| `/dcp sweep [count]`    | Prune all tools since last user message  | Cleanup noise, quick prune          |
| `/dcp distill [focus]`  | Distill key findings before removing     | Large outputs with valuable details |
| `/dcp context`          | Show token breakdown by category         | Check context usage                 |
| `/dcp stats`            | Show cumulative pruning stats            | Review efficiency                   |

### Tool Calls (Fallback)

Use tool calls when slash commands aren't suitable:

| Tool       | Purpose                       | When to Use                              |
| ---------- | ----------------------------- | ---------------------------------------- |
| `distill`  | Extract key info, then remove | Large outputs with valuable details      |
| `prune`    | Remove tool outputs (no save) | Noise, irrelevant reads, superseded info |
| `compress` | Collapse conversation range   | When slash command fails                 |

**Note:** Compress tool has boundary matching issues. Prefer `/dcp compress` slash command.

## DCP Auto-Strategies

DCP runs these automatically (zero LLM cost):

- **Deduplication** — removes duplicate tool calls (same tool + same args)
- **Supersede Writes** — removes write inputs when file is later read
- **Purge Errors** — removes errored tool inputs after 4 turns

You don't need to manually prune these.

## When to Evaluate

**DO evaluate context when:**

- Starting a new phase of work (best timing)
- Accessed something irrelevant
- Information superseded by newer outputs
- Large tool outputs with extractable details
- Phase complete (research, exploration, implementation)

**DO NOT manage when:**

- Output needed for upcoming edits
- Contains files you'll reference when editing
- Uncertain if you'll need it again

## Tool Usage

### Distill — Preserve + Remove (Preferred)

Extract high-fidelity knowledge from tool outputs, then remove the raw output. Your distillation must be a **complete technical substitute** — capture signatures, types, logic, constraints, everything essential.

```typescript
distill({
  targets: [
    {
      id: "10",
      distillation:
        "auth.ts: validateToken(token: string) -> User|null, uses bcrypt 12 rounds, throws on expired tokens",
    },
    {
      id: "11",
      distillation:
        "user.ts: interface User { id: string, email: string, permissions: Permission[], status: 'active'|'suspended' }",
    },
  ],
});
```

### Prune — Remove Noise (Last Resort)

Delete tool outputs entirely. No preservation. Use for noise, wrong targets, or superseded information.

```typescript
prune({ ids: ["5", "8"] }); // IDs from <prunable-tools> list
```

## Critical Rules

- IDs MUST come from the current `<prunable-tools>` list
- The list refreshes after every tool use — don't cache IDs
- Invalid IDs will error
- **Distill before prune** — if there's anything worth keeping, distill it
- **Batch operations** — accumulate several candidates before acting
- **Timing** — manage at the START of a new turn (after user message), not at the end of your turn

## Protected Content

Auto-protected from pruning:

- `.env*` files
- `AGENTS.md`
- `.opencode/**` config
- `.beads/**` tasks
- `package.json`, `tsconfig.json`

## Context Budget Guidelines

| Phase             | Target  | Action                                     |
| ----------------- | ------- | ------------------------------------------ |
| Starting work     | <50k    | Load only essential AGENTS.md + task spec  |
| Mid-task          | 50-100k | Distill completed reads, keep active files |
| Approaching limit | >100k   | Aggressive distill, prune remaining noise  |
| Near capacity     | >150k   | Session restart with handoff               |

## Quick Reference

```
DCP SLASH COMMANDS (preferred):
/dcp compress [focus]  → Collapse range into summary
/dcp distill [focus]   → Distill key findings
/dcp sweep [count]     → Prune all since last user
/dcp context           → Show token breakdown

TOOL CALLS (fallback):
distill({ targets: [{ id, distillation }] })
prune({ ids: [...] })

BUDGET: <50k start → 50-100k mid → >100k distill → >150k restart
TIMING: Manage at turn START, not turn END
```
