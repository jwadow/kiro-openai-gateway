---
name: beads-bridge
description: >
  Multi-agent task coordination using br (beads_rust) and OpenCode tools. Use when work spans multiple sessions,
  has dependencies, needs file locking, or requires agent coordination. Covers claim/reserve/done cycle,
  dependency management, hierarchical decomposition, and session protocols.
version: "2.0.0"
license: MIT
---

# Beads Bridge - Cross-Session Task Coordination

Bridge between Beads git-backed task tracking, OpenCode's native todo system, and swarm coordination.

**Note:** `br` (beads_rust) is non-invasive and never executes git commands. After `br sync --flush-only`, you must manually run `git add .beads/ && git commit`.

## Overview

**Beads Bridge = Beads (br) + OpenCode Todos + Swarm Monitor**

- **Beads (br)**: Git-backed task tracking with dependency management
- **OpenCode Todos**: Native session-scoped task lists for subagents
- **Swarm Monitor**: Real-time progress tracking (visualization only)

**Key Tools**:

| Tool    | Purpose                     | When to Use                                          |
| ------- | --------------------------- | ---------------------------------------------------- |
| `swarm` | Unified swarm coordination  | All swarm operations (sync, monitor, plan, delegate) |
| `Task`  | Parallel subagent execution | Spawning worker swarms                               |

**swarm operations:**

- `sync`: Sync Beads ↔ OpenCode todos (start of session, before spawning)
- `monitor`: Progress tracking/visualization (during swarm execution)
- `plan`: Task classification + dependency graphs (before spawning workers)
- `delegate`: Create delegation packets (assigning work to workers)

## When to Use This Skill

- Work spans multiple sessions (need persistence)
- Tasks have complex dependencies
- Multiple agents need to coordinate on shared work
- Need to recover swarm state after session restart
- Subagents need to see Beads tasks via todoread

## Core Workflows

### 1. Session Start: Load Beads into Todos

Make Beads tasks visible to subagents:

```typescript
// Push Beads to OpenCode todos
const result = await swarm({
  operation: "sync",
  action: "push",
  filter: "open", // or "in_progress", "all"
});

// Subagents can now use todoread to see tasks
// [Bead] task-title will appear in their todo list
```

### 2. Check Swarm Status

Check current swarm progress:

```typescript
// Check swarm status
const status = await swarm({
  operation: "monitor",
  action: "status",
  team_name: "api-refactor-swarm",
});

const stats = JSON.parse(status).summary;
console.log(`Workers: ${stats.total_workers}, Completed: ${stats.completed}`);

// Render TUI for visualization
const ui = await swarm({
  operation: "monitor",
  action: "render_block",
  team_name: "api-refactor-swarm",
});
console.log(ui);
```

### 3. Shared Task Lists for Cross-Session Work

For work that spans multiple sessions, use shared task lists:

```typescript
// Create a shared list that persists across sessions
const list = await swarm({
  operation: "sync",
  action: "create_shared",
  name: "api-refactor-swarm",
  tasks: JSON.stringify([
    { id: "task-1", content: "Refactor auth endpoint", status: "pending", priority: "high" },
    { id: "task-2", content: "Update user routes", status: "pending", priority: "medium" },
  ]),
});

// Workers update the shared list as they complete work
await swarm({
  operation: "sync",
  action: "update_shared",
  list_id: list.list_id,
  tasks: JSON.stringify([{ id: "task-1", status: "completed" }]),
});
```

### 4. Create Shared Task Lists for Swarms

Create persistent task lists that survive session boundaries:

```typescript
// Create a shared list for a swarm
const list = await swarm({
  operation: "sync",
  action: "create_shared",
  name: "api-refactor-swarm",
  tasks: JSON.stringify([
    { id: "task-1", content: "Refactor auth endpoint", status: "pending", priority: "high" },
    { id: "task-2", content: "Update user routes", status: "pending", priority: "medium" },
    { id: "task-3", content: "Fix validation", status: "pending", priority: "medium" },
  ]),
});

// Share the list ID with workers
console.log(`List ID: ${list.list_id}`);
// Workers can access via: swarm({ operation: "sync", action: "get_shared", list_id: "..." })
```

### 5. Worker Updates to Shared List

Workers can update their task status:

```typescript
// Worker completes a task
await swarm({
  operation: "sync",
  action: "update_shared",
  list_id: "shl_abc123",
  tasks: JSON.stringify([{ id: "task-1", status: "completed" }]),
});
```

## Integration Patterns

### Pattern A: Beads → Swarm → Beads

Full cycle from Beads task to swarm execution and back:

```typescript
// 1. Start: Push Beads to todos
await swarm({ operation: "sync", action: "push" });

// 2. Claim the parent Bead
await bash("br update parent-task --status in_progress");

// 3. Analyze and spawn swarm
const analysis = await swarm({
  operation: "plan",
  action: "analyze",
  task: "Implement API refactor",
  files: "src/api/users.ts,src/api/posts.ts,src/api/auth.ts",
});

// 4. Execute swarm (see swarm-coordination skill)
// ... spawn workers, monitor progress ...

// 5. Complete: Pull completed todos back to Beads
await swarm({ operation: "sync", action: "pull" });

// 6. Clear swarm state
await swarm({
  operation: "monitor",
  action: "clear",
  team_name: "api-refactor-swarm",
});

// 7. Close parent Bead and sync
await bash("br close parent-task --reason 'Swarm completed all subtasks'");
await bash("br sync --flush-only");
await bash("git add .beads/ && git commit -m 'close parent-task'");
```

### Pattern B: Dependency-Aware Task Scheduling

Use swarm tool's dependency graph for proper ordering:

```typescript
// Get full analysis with dependency graph
const analysis = await swarm({
  operation: "plan",
  action: "analyze",
  task: "Refactor authentication system",
  files: "src/auth/service.ts,src/auth/types.ts,src/routes/auth.ts,src/middleware/auth.ts",
});

const plan = JSON.parse(analysis);

// Use parallelizable_groups for spawn order
for (const group of plan.dependency_graph.parallelizable_groups) {
  // Spawn all tasks in this group in parallel
  for (const taskId of group) {
    const node = plan.dependency_graph.nodes.find((n) => n.id === taskId);
    Task({
      subagent_type: "general",
      description: `Execute ${taskId}`,
      prompt: `Execute task ${taskId}: ${node.content}
      
Files: ${node.assignedFiles.join(", ")}
Blocked by: ${node.blockedBy.join(", ") || "none"}
Team: auth-refactor-swarm
Worker: ${node.worker}`,
    });
  }

  // Wait for this group to complete before starting next
  // (dependency ordering)
}
```

### Pattern C: Cross-Session Handoff

When work needs to continue in a new session:

```typescript
// End of session 1: Save state to memory and shared list
await swarm({
  operation: "sync",
  action: "update_shared",
  list_id: "api-refactor-swarm",
  tasks: JSON.stringify([
    { id: "worker-1", content: "Auth service", status: "completed" },
    { id: "worker-2", content: "User routes", status: "completed" },
    { id: "worker-3", content: "Validation", status: "in_progress" },
  ]),
});

await memory_update({
  file: "handoffs/swarm-state",
  content: `
## Swarm Handoff

Team: api-refactor-swarm
Progress: 60% complete (3/5 workers done)
Remaining: worker-4 (blocked), worker-5 (pending)
Blockers: worker-4 needs auth types from worker-1

Next steps:
1. Check shared task list for current status
2. Unblock worker-4 with completed types
3. Spawn remaining workers
`,
  mode: "replace",
});

// Sync beads before ending session
await bash("br sync --flush-only");
await bash("git add .beads/ && git commit -m 'session handoff'");

// Start of session 2: Check status and continue
const status = await swarm({
  operation: "monitor",
  action: "status",
  team_name: "api-refactor-swarm",
});

const shared = await swarm({
  operation: "sync",
  action: "get_shared",
  list_id: "api-refactor-swarm",
});

console.log(`Continuing swarm with ${shared.tasks.length} tasks...`);
```

## Data Locations

| Data Type         | Location                                        | Persistence   |
| ----------------- | ----------------------------------------------- | ------------- |
| Beads tasks       | `.beads/issues/*.md`                            | Git-backed    |
| Swarm progress    | `.beads/swarm-progress.jsonl`                   | Session       |
| Shared task lists | `~/.local/share/opencode/storage/shared-tasks/` | Cross-session |
| OpenCode todos    | `~/.local/share/opencode/storage/todo/`         | Session       |

## Quick Reference

```
SESSION START:
  swarm({ operation: "sync", action: "push" })  // Make Beads visible to subagents
  swarm({ operation: "monitor", action: "status", team_name: "..." })  // Check swarm status

DURING WORK:
  swarm({ operation: "monitor", action: "progress_update", ... })  // Track worker progress
  swarm({ operation: "monitor", action: "render_block", ... })  // TUI visualization
  swarm({ operation: "sync", action: "update_shared", ... })  // Cross-session updates

SESSION END:
  swarm({ operation: "sync", action: "pull" })  // Sync completed todos back to Beads
  swarm({ operation: "monitor", action: "clear", team_name: "..." })  // Cleanup swarm state
  br sync --flush-only  // Export Beads changes
  git add .beads/ && git commit -m "..."  // Commit changes to git

RECOVERY:
  swarm({ operation: "sync", action: "get_shared", list_id: "..." })  // Get shared task list
  swarm({ operation: "monitor", action: "status", team_name: "..." })  // Check swarm status
```

## Rules

1. **Always push Beads at session start** - Subagents need visibility via todoread
2. **Use shared lists for long-running swarms** - Cross-session persistence via swarm sync
3. **Pull completed todos back to Beads** - Keep tracking system in sync
4. **Check swarm status before spawning** - Avoid duplicate work
5. **Clear swarm state when done** - Cleanup after completion
6. **Always sync and commit before session end** - `br sync --flush-only` then `git add .beads/ && git commit`
