---
name: beads
description: >
  Multi-agent task coordination using br (beads_rust) CLI. Use when work spans multiple
  sessions, has dependencies, needs file locking, or requires agent coordination. Covers
  claim/reserve/done cycle, dependency management, hierarchical decomposition, and session protocols.
version: "2.0.0"
license: MIT
---

# Beads Workflow - Multi-Agent Task Coordination

Graph-based task tracker with file locking for multi-agent coordination. Persists across sessions.

**Note:** `br` (beads_rust) is non-invasive and never executes git commands. After `br sync --flush-only`, you must manually run `git add .beads/ && git commit`.

## Overview

**br (beads_rust) CLI** replaces the old `bd` (beads) CLI with a faster Rust implementation.

**Key Distinction**:

- **br CLI**: Multi-session work, dependencies, file locking, agent coordination
- **TodoWrite**: Single-session tasks, linear execution, conversation-scoped

**When to Use br vs TodoWrite**:

- "Will I need this context in 2 weeks?" → **YES** = br
- "Does this have blockers/dependencies?" → **YES** = br
- "Multiple agents editing same codebase?" → **YES** = br
- "Will this be done in this session?" → **YES** = TodoWrite

**Decision Rule**: If resuming in 2 weeks would be hard without beads, use beads.

## Essential Commands

```bash
br ready              # Show issues ready to work (no blockers)
br list --status open # All open issues
br show <id>          # Full issue details with dependencies
br create --title "Fix bug" --type bug --priority 2 --description "Details here"
br update <id> --status in_progress
br close <id> --reason "Completed"
br sync --flush-only  # Export to JSONL (then git add/commit manually)
```

## Hierarchical Structure: Epic → Task → Subtask

**Beads supports up to 3 levels of hierarchy using hierarchical IDs:**

```
br-a3f8        (Epic - parent feature)
├── br-a3f8.1  (Task - first child)
├── br-a3f8.2  (Task - second child)
│   ├── br-a3f8.2.1  (Subtask - child of .2)
│   └── br-a3f8.2.2  (Subtask - child of .2)
└── br-a3f8.3  (Task - third child)
```

### When to Decompose

| Scenario                     | Structure                            |
| ---------------------------- | ------------------------------------ |
| Bug fix, config change       | Single bead                          |
| Small feature (1-2 files)    | Single bead                          |
| Feature crossing FE/BE       | Epic + tasks by domain               |
| New system/service           | Epic + tasks by component            |
| Multi-day work               | Epic + tasks for parallelization     |
| Work needing multiple agents | Epic + tasks (agents claim children) |

### Creating Hierarchical Beads

```bash
# Step 1: Create Epic (parent)
br create --title "User Authentication System" --type epic --priority 1 \
  --description "Complete auth with OAuth, sessions, and protected routes"
# Returns: br-a3f8

# Step 2: Create child tasks with parent
br create --title "Database schema for auth" --type task --priority 2 \
  --parent br-a3f8 --description "Create user and session tables"
# Returns: br-a3f8.1  ← Hierarchical ID!

# Step 3: Create dependent tasks
br create --title "OAuth integration" --type task --priority 2 \
  --parent br-a3f8 --blocked-by br-a3f8.1
# Returns: br-a3f8.2
```

### Dependency Types

Beads supports four dependency types:

| Type              | Meaning                   | Use Case            |
| ----------------- | ------------------------- | ------------------- |
| `blocks`          | Task A blocks Task B      | Sequential work     |
| `related`         | Tasks are connected       | Cross-references    |
| `parent-child`    | Hierarchy (via `parent:`) | Epic → Task         |
| `discovered-from` | Found during work         | New work discovered |

### Parallel Execution with Dependencies

```
br-a3f8.1 [Database] ──┬──> br-a3f8.2 [Backend] ──┐
     (READY)           │                          │
                       │                          ▼
                       └──> br-a3f8.3 [Frontend]  br-a3f8.5 [Testing]
                       │         │                     ▲
                       └──> br-a3f8.4 [Docs] ──────────┘

Parallel tracks:
• Agent 1 (backend): .1 → .2
• Agent 2 (frontend): wait for .1, then .3
• Agent 3 (qa): wait for .2 and .3, then .5
```

**Key insight**: After br-a3f8.1 completes, .2, .3, and .4 all become READY simultaneously. Multiple agents can claim them in parallel.

### Querying Hierarchy

```bash
# See all open issues
br list --status open

# See ready work (unblocked tasks)
br ready
# Returns tasks where all dependencies are closed
```

## Session Start Protocol

**Every session, follow these steps:**

### Step 1: Find Ready Work

```bash
br ready
```

Returns highest priority task with no blockers.

If no tasks returned, check all open work:

```bash
br list --status open
```

### Step 2: Claim Task

```bash
br update <id> --status in_progress
```

### Step 3: Get Full Context

```bash
br show <id>
```

Shows full description, dependencies, notes, history.

### Step 4: Do the Work

Implement the task, adding notes as you learn.

### Step 5: Complete and Sync

```bash
br close <id> --reason "Implemented auth with JWT tokens"
br sync --flush-only
git add .beads/
git commit -m "sync beads"
# RESTART SESSION - fresh context
```

Always restart session after closing a task. One task per session.

## Task Creation

### When to Create Tasks

Create tasks when:

- User mentions tracking work across sessions
- User says "we should fix/build/add X"
- Work has dependencies or blockers
- Discovered work while implementing (>2 min effort)

### Basic Task Creation

```bash
br create --title "Fix authentication bug" --priority 0 --type bug
# Priority: 0=critical, 1=high, 2=normal, 3=low, 4=backlog
# Types: task, bug, feature, epic, chore
```

### With Description

```bash
br create --title "Implement OAuth" --type feature --priority 1 \
  --description "Add OAuth2 support for Google, GitHub. Use passport.js."
```

### Epic with Children

```bash
# Create parent epic
br create --title "Epic: OAuth Implementation" --priority 0 --type epic
# Returns: oauth-abc

# Create child tasks with parent
br create --title "Research OAuth providers" --priority 1 --parent oauth-abc
br create --title "Implement auth endpoints" --priority 1 --parent oauth-abc
br create --title "Add frontend login UI" --priority 2 --parent oauth-abc
```

## Git Sync

### Manual Sync (Non-Invasive)

**Important:** `br` never executes git commands. You must manually commit changes.

```bash
# Export changes to JSONL
br sync --flush-only

# Then manually commit
git add .beads/
git commit -m "sync beads"
git push
```

**Use when**: End of session, before handoff, after major progress.

### Cleanup Old Issues

```bash
br cleanup --days 7
```

Removes closed issues older than N days. Run weekly.

## Error Handling

### Common Issues

**No ready tasks**

- Run `br list --status open` to see all tasks
- Some may be blocked - check dependencies with `br show <id>`

**Sync failures**

- Run `br doctor` to repair database
- Check git remote access

## Examples

### Example 1: Standard Session

```bash
# 1. Find and claim work
br ready
br update auth-123 --status in_progress

# 2. Get context
br show auth-123

# 3. Do the work...
# [implementation]

# 4. Complete and sync
br close auth-123 --reason "Login form with validation, hooks for auth state"
br sync --flush-only
git add .beads/
git commit -m "close auth-123"
# RESTART SESSION
```

### Example 2: Discovered Work

```bash
# Working on task, found more work
br create --title "Fix edge case in validation" --type bug --priority 1 \
  --description "Empty strings bypass email check - discovered while implementing login"
# Continue current task, new task tracked for later
```

### Example 3: Creating Dependencies

```bash
# Create tasks with dependencies
br create --title "Setup database" --type task --priority 1
# Returns: setup-db

br create --title "Implement API" --type task --priority 2 --blocked-by setup-db
# Returns: impl-api (blocked until setup-db closes)

br create --title "Add tests" --type task --priority 2 --blocked-by impl-api
# Returns: add-tests
```

## Multi-Agent Coordination (Swarm Mode)

For parallel execution with multiple subagents, use the **beads-bridge** skill:

```typescript
skill({ name: "beads-bridge" });
```

**beads-bridge** provides (via unified `swarm` tool):

- `swarm({ operation: "sync" })` - Sync Beads tasks to OpenCode todos for subagent visibility
- `swarm({ operation: "monitor" })` - Real-time progress tracking and visualization
- `swarm({ operation: "plan" })` - Task classification and dependency analysis
- `swarm({ operation: "delegate" })` - Create delegation packets for workers

**When to use beads vs beads-bridge:**

| Scenario                       | Use                              |
| ------------------------------ | -------------------------------- |
| Single agent, linear work      | `beads` skill only               |
| Multiple agents in parallel    | `beads-bridge` + `beads`         |
| Need subagents to see tasks    | `beads-bridge` (swarm sync push) |
| Track worker progress visually | `beads-bridge` (swarm monitor)   |

**Example swarm workflow:**

```typescript
// 1. Push beads to OpenCode todos (subagents can see via todoread)
swarm({ operation: "sync", action: "push" });

// 2. Spawn workers in parallel using Task tool
Task({ subagent_type: "general", description: "Worker 1", prompt: "..." });
Task({ subagent_type: "general", description: "Worker 2", prompt: "..." });

// 3. Monitor progress
swarm({ operation: "monitor", action: "render_block", team_name: "my-swarm" });

// 4. Pull completed work back to beads
swarm({ operation: "sync", action: "pull" });
```

## Rules

1. **Check `br ready` first** - Find unblocked work before starting
2. **Claim before editing** - `br update <id> --status in_progress`
3. **One task per session** - Restart after `br close`
4. **Always sync and commit** - `br sync --flush-only` then `git add .beads/ && git commit`
5. **Write notes for future agents** - Assume zero conversation context

## Best Practices

### Daily/Weekly Maintenance

| Task         | Frequency      | Command               | Why                                            |
| ------------ | -------------- | --------------------- | ---------------------------------------------- |
| Health check | Weekly         | `br doctor`           | Repairs database issues, detects orphaned work |
| Cleanup      | Every few days | `br cleanup --days 7` | Keep DB under 200-500 issues for performance   |

### Key Principles

1. **Plan outside Beads first** - Use planning tools, then import tasks to beads
2. **One task per session, then restart** - Fresh context prevents confusion
3. **File lots of issues** - Any work >2 minutes should be tracked
4. **"Land the plane" = PUSH** - `br sync --flush-only` + git commit/push, not "ready when you are"
5. **Include issue ID in commits** - `git commit -m "Fix bug (br-abc)"`

### Database Health

```bash
# Check database size
br list --status all --json | wc -l

# Target: under 200-500 issues
# If over, run cleanup more aggressively:
br cleanup --days 3
```

## Quick Reference

```
SESSION START:
  br ready → br update <id> --status in_progress → br show <id>

DURING WORK:
  br create for discovered work (>2min)
  br show <id> for context

SESSION END:
  br close <id> --reason "..." → br sync --flush-only → git add .beads/ && git commit → RESTART SESSION

MAINTENANCE:
  br doctor - weekly health check
  br cleanup --days 7 - remove old issues
```
