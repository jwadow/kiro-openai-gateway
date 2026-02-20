---
description: Show project status - tasks, git state, recent sessions
argument-hint: "[--git] [--sessions]"
agent: build
---

# Status: $ARGUMENTS

Quick project status dashboard. Runs read-only commands and reports state.

> **No arguments required.** Flags are optional filters.

## Parse Arguments

| Argument     | Default | Description             |
| ------------ | ------- | ----------------------- |
| `--git`      | false   | Focus on git state only |
| `--sessions` | false   | Focus on sessions only  |

## Load Skills

```typescript
skill({ name: "beads" });
```

## Determine Input Type

| Input Type   | Detection     | Action              |
| ------------ | ------------- | ------------------- |
| No arguments | Default       | Show full dashboard |
| `--git`      | Flag provided | Git state only      |
| `--sessions` | Flag provided | Sessions only       |

## Before You Status

- **Be certain**: This is a read-only command, no changes are made
- **Use actual data**: Don't invent data, use real command output
- **No modifications**: Don't create beads or modify state from status
- **Single recommendation**: Only suggest ONE next action

## Available Tools

| Tool            | Use When                          |
| --------------- | --------------------------------- |
| `br`            | Task status and stats             |
| `git`           | Git state and history             |
| `list_sessions` | Recent sessions                   |
| `action-queue`  | Pending approvals and ready tasks |

## Phase 1: Gather State (Parallel)

Run all checks simultaneously:

```bash
br stats
br list --status in_progress
br ready
```

```bash
git status --porcelain
git branch --show-current
git log --oneline -5
```

```typescript
list_sessions({ since: "today", limit: 5 });
action - queue({ op: "status" });
```

---

## Phase 2: Format Report

Present results in simple sections. Use the actual output from Phase 1 — don't invent data.

```
Status
━━━━━━

TASKS
  In Progress: [list from br list --status in_progress]
  Ready:       [list from br ready]
  Stats:       [summary from br stats]

GIT
  Branch:  [from git branch]
  Changes: [from git status, or "clean"]
  Recent:  [from git log]

SESSIONS TODAY
  [from list_sessions]

ACTION QUEUE
  Pending approvals: [from action-queue pending_approvals]
  Ready tasks:       [from action-queue ready_tasks]
  Idle workers:      [from action-queue idle_workers]
```

---

## Phase 3: Suggest Next Action

Based on gathered state, recommend ONE next step:

| State                        | Suggestion                    |
| ---------------------------- | ----------------------------- |
| Has in_progress tasks        | `/ship <id>` (continue work)  |
| Has ready tasks, none active | `/start <id>` (pick up work)  |
| Uncommitted changes          | Review and commit             |
| Nothing active or ready      | `/create "<desc>"` (new work) |

---

## Output

```
Status
━━━━━━

[Sections from Phase 2]

Next: [single recommendation from Phase 3]
```
