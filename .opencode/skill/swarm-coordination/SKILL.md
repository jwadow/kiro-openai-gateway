---
name: swarm-coordination
description: >
  Use when implementing plans with multiple independent tasks that can run in parallel.
  Enables leader agents to spawn, coordinate, and monitor worker swarms using Kimi K2.5 PARL patterns.
  Covers task classification, anti-serial-collapse detection, delegation packets, progress tracking,
  and graceful shutdown patterns.
version: "2.1.0"
license: MIT
---

# Swarm Coordination - Kimi K2.5 PARL Multi-Agent Execution

Coordinate multiple agents working on independent tasks in parallel using Kimi K2.5 PARL (Parallel-Agent Reinforcement Learning) patterns.

## Overview

**Swarm = Leader + Workers + Progress Tracking + Todo Persistence**

- **Leader (build agent)**: Orchestrates the swarm - analyzes tasks, spawns workers, monitors progress, synthesizes results
- **Workers (general/explore/review/plan agents)**: Execute independent tasks - read delegation, make changes, report progress
- **Progress Tracker (swarm-progress.jsonl)**: Real-time progress updates with TUI visualization
- **Todo Persistence (swarm-todos.json)**: Cross-session recovery for interrupted swarms

**Key Tools**:

| Tool    | Purpose                    | When to Use          |
| ------- | -------------------------- | -------------------- |
| `swarm` | Unified swarm coordination | All swarm operations |

**swarm operations:**

- `plan`: Task classification & dependency graph (before spawning workers)
- `delegate`: Create delegation packets (assigning work to workers)
- `monitor`: Progress tracking + TUI visualization (during swarm execution)
- `sync`: Sync Beads ↔ OpenCode todos (session start, cross-session)

**Key Distinction**:

- **Swarm**: Parallel execution of independent tasks with dynamic allocation
- **Beads**: Task tracking and dependency management across sessions
- **Task tool**: Spawning individual subagents for research/execution
- **swarm tool**: Unified operations for planning, monitoring, delegation, and sync

**When to Use Swarm Coordination**:

- "Does this plan have 3+ independent tasks?" → **YES** = Swarm
- "Can multiple tasks run in parallel without conflicts?" → **YES** = Swarm
- "Do I need to coordinate multiple agents?" → **YES** = Swarm
- "Is this a single task or sequential dependency chain?" → **NO** = Single agent

**Kimi K2.5 PARL Patterns**:

- **Task Classification**: Auto-detect parallelization potential
- **Anti-Serial-Collapse**: Prevent forced sequential execution
- **Dynamic Allocation**: Conservative start, scale based on bottlenecks
- **Progress Visualization**: Real-time TUI with beautiful markdown blocks
- **Dependency Graphs**: DAG-based task scheduling with critical path analysis

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         BUILD AGENT (Leader)                     │
│  - Parses plan into tasks                                        │
│  - Creates delegation packets                                    │
│  - Spawns worker agents via Task tool                            │
│  - Monitors progress via swarm tool                             │
│  - Synthesizes final results                                     │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  WORKER-1   │      │  WORKER-2   │      │  WORKER-3   │
│  (general)  │      │  (general)  │      │  (general)  │
│             │      │             │      │             │
│ - Read      │      │ - Read      │      │ - Read      │
│   delegation│      │   delegation│      │   delegation│
│ - Execute   │      │ - Execute   │      │ - Execute   │
│ - Report    │      │ - Report    │      │ - Report    │
└─────────────┘      └─────────────┘      └─────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │  PROGRESS +     │
                    │  TODO PERSIST   │
                    └─────────────────┘
```

## Swarm Launch Flow - PARL Pattern (7 Steps)

### Step 0: Task Analysis (Anti-Serial-Collapse + Dependency Graph)

Analyze the user's actual task to determine optimal swarm strategy:

```typescript
// 1. Classify the task and build dependency graph
const analysis = await swarm({
  operation: "plan",
  operation: "analyze",
  task: "<user's request from input>",
  files: "<detected files from glob/grep>",
});

// Returns:
// - type: "search" | "batch" | "writing" | "sequential" | "mixed"
// - recommended_agents: number
// - phases: [{ name, role, agent_count, dependencies }]
// - coupling: "high" | "medium" | "low"
// - confidence: "high" | "medium" | "low"
// - dependency_graph: { nodes, edges, critical_path, parallelizable_groups }

const plan = JSON.parse(analysis);

// 2. Check for serial collapse
const check = await swarm({
  operation: "plan",
  operation: "check",
  task: "<user's request>",
  files: String(plan.file_count),
  recommended_agents: plan.classification.recommended_agents,
});

// If serial collapse detected, force parallelization
if (check.serial_collapse_detected) {
  console.log(`⚠️ Serial collapse detected: ${check.warning_signs.join(", ")}`);
  console.log(`✓ Adjusting to ${check.suggested_agents} agents`);
}

// 3. Use dependency graph for spawn ordering
const { parallelizable_groups, critical_path } = plan.dependency_graph;
console.log(`Critical path: ${critical_path.join(" → ")}`);
console.log(`Parallel groups: ${parallelizable_groups.length}`);
```

### Step 1: Session Setup (Push Beads to Todos)

Make Beads tasks visible to subagents:

```typescript
// Push Beads to OpenCode todos (subagents see via todoread)
await swarm({ operation: "sync", operation: "push", filter: "open" });

// Check for existing swarm state
const status = await swarm({
  operation: "monitor",
  operation: "status",
  team_name: "plan-implementation",
});
const stats = JSON.parse(status).summary;

if (stats.total_workers > 0) {
  console.log(`Found existing swarm with ${stats.total_workers} workers`);
  // Render current progress
  const ui = await swarm({
    operation: "monitor",
    operation: "render_block",
    team_name: "plan-implementation",
  });
  console.log(ui);
}
```

### Step 2: Create Delegation Packets

For each task, create a delegation packet:

```typescript
swarm({
  operation: "delegate",
  bead_id: "task-1",
  title: "Implement auth service",
  expected_outcome: "Auth service with JWT tokens, tests pass",
  required_tools: "read, grep, lsp, edit, bash",
  must_do: "LSP before edits, run npm test after changes",
  must_not_do: "No new dependencies, don't edit config files",
  acceptance_checks: "typecheck: npm run typecheck, lint: npm run lint, test: npm test",
  context: "See .beads/artifacts/task-1/spec.md for requirements",
  write: true,
});
```

### Step 3: Spawn Worker Agents (Using Dependency Groups)

Use parallelizable_groups from dependency graph for proper ordering:

```typescript
// Spawn workers in dependency order
for (const group of plan.dependency_graph.parallelizable_groups) {
  // All tasks in this group can run in parallel
  const spawnPromises = group.map((taskId) => {
    const node = plan.dependency_graph.nodes.find((n) => n.id === taskId);
    return Task({
      subagent_type: "general",
      description: `Execute ${taskId}`,
      prompt: `Execute bead ${taskId}: ${node.content}

Read delegation packet at: .beads/artifacts/${taskId}/delegation.md

Files: ${node.assignedFiles.join(", ")}
Phase: ${node.phase}
Worker: ${node.worker}
Team: plan-implementation

Requirements:
1. Follow all MUST DO constraints
2. Avoid all MUST NOT DO items
3. Run acceptance checks before claiming done
4. Report progress via swarm monitor`,
    });
  });

  // Wait for parallel group to complete before starting next
  await Promise.all(spawnPromises);
}
```

### Step 4: Monitor Progress (Real-time TUI + Persistence)

Monitor with beautiful block UI, progress tracking, and auto-persistence:

```typescript
let allComplete = false;
while (!allComplete) {
  // Option A: Render beautiful TUI block
  const ui = await swarm({
    operation: "monitor",
    operation: "render_block",
    team_name: "plan-implementation",
  });
  console.log(ui); // Markdown block with tables, emojis, progress

  // Option B: Get detailed status
  const status = await swarm({
    operation: "monitor",
    operation: "status",
    team_name: "plan-implementation",
  });
  const stats = JSON.parse(status).summary;
  // Returns: total_workers, completed, working, errors, messages

  // Check completion
  allComplete = stats.completed === stats.total_workers;

  if (!allComplete) {
    // Wait before checking again
    await new Promise((r) => setTimeout(r, 2000)); // Wait 2s
  }
}
```

### Step 5: Synthesize Results

When all workers complete:

```typescript
// 1. Get final status
const finalStatus = await swarm({
  operation: "monitor",
  operation: "status",
  team_name: "plan-implementation",
});

// 2. Run full verification
await bash("npm run typecheck && npm run lint && npm test");

// 3. Pull completed todos back to Beads
await swarm({ operation: "sync", operation: "pull" });

// 4. Clear swarm data
await swarm({ operation: "monitor", operation: "clear", team_name: "plan-implementation" });

// 5. Close parent bead
await bash("br close parent-task --reason 'Swarm completed all subtasks'");
```

## Dependency Graph Features

The `swarm` tool's plan operation includes full dependency graph analysis:

### Structure

```typescript
interface DependencyGraph {
  nodes: TaskNode[]; // Individual tasks
  edges: Edge[]; // Dependencies between tasks
  critical_path: string[]; // Longest dependency chain
  parallelizable_groups: string[][]; // Tasks that can run in parallel
}

interface TaskNode {
  id: string;
  content: string;
  phase: string;
  worker: string;
  status: "pending" | "in_progress" | "completed";
  priority: "high" | "medium" | "low";
  blockedBy: string[]; // Tasks this depends on
  blocks: string[]; // Tasks that depend on this
  assignedFiles: string[]; // Files assigned to this task
}
```

### Usage

```typescript
const analysis = await swarm({
  operation: "plan",
  operation: "analyze",
  task: "Refactor API layer",
  files: "src/api/users.ts,src/api/posts.ts,src/api/auth.ts",
});

const plan = JSON.parse(analysis);

// Critical path shows the longest dependency chain
// Focus attention here for optimal completion time
console.log(`Critical path: ${plan.dependency_graph.critical_path.join(" → ")}`);

// Parallelizable groups show which tasks can run simultaneously
// Each group must complete before starting the next
for (let i = 0; i < plan.dependency_graph.parallelizable_groups.length; i++) {
  const group = plan.dependency_graph.parallelizable_groups[i];
  console.log(`Wave ${i + 1}: ${group.join(", ")} (${group.length} parallel tasks)`);
}
```

## Todo Persistence for Cross-Session Recovery

## Delegation Packet Structure

```markdown
# Delegation Packet

- TASK: task-1 - Implement auth service
- EXPECTED OUTCOME: Auth service with JWT tokens, tests pass
- REQUIRED TOOLS:
  - read
  - grep
  - lsp
  - edit
  - bash
- MUST DO:
  - LSP before edits
  - Run npm test after changes
  - Follow existing code patterns
- MUST NOT DO:
  - No new dependencies
  - Don't edit config files
  - Don't modify shared utilities
- ACCEPTANCE CHECKS:
  - typecheck: npm run typecheck
  - lint: npm run lint
  - test: npm test
- CONTEXT:
  See .beads/artifacts/task-1/spec.md for requirements
```

## Worker Protocol (Updated with Progress Tracking)

Workers follow this execution pattern:

### 1. Read Delegation

```typescript
// First action: read the delegation packet
read({ filePath: ".beads/artifacts/<task-id>/delegation.md" });
```

### 2. Announce Start with Progress

```typescript
await swarm({
  operation: "monitor",
  operation: "progress_update",
  team_name: "plan-implementation",
  worker_id: "worker-1",
  phase: "explore", // or "generate", "reflect", etc.
  progress: 0,
  status: "working",
  file: "src/api/users.ts", // current file being worked on
});
```

### 3. Execute Task with Progress Updates

Follow the MUST DO constraints. Avoid MUST NOT DO items. Use required tools only.

Report progress every 25%:

```typescript
// At 25%, 50%, 75% completion
await swarm({
  operation: "monitor",
  operation: "progress_update",
  team_name: "plan-implementation",
  worker_id: "worker-1",
  phase: "explore",
  progress: 25, // or 50, 75
  status: "working",
  file: "src/api/users.ts",
});
```

### 4. Run Acceptance Checks

```bash
# Run each check from the delegation packet
npm run typecheck
npm run lint
npm test
```

### 5. Report Completion

```typescript
// Mark as completed
await swarm({
  operation: "monitor",
  operation: "progress_update",
  team_name: "plan-implementation",
  worker_id: "worker-1",
  phase: "explore",
  progress: 100,
  status: "completed",
  file: "src/api/users.ts",
});
```

## Error Handling

### Worker Fails Acceptance Checks

Workers report failures via progress updates with error status:

```typescript
// Worker reports error via progress update
await swarm({
  operation: "monitor",
  operation: "progress_update",
  team_name: "plan-implementation",
  worker_id: "worker-1",
  phase: "explore",
  progress: 75,
  status: "error",
  message: "typecheck failed: missing type for AuthToken",
});
```

### Leader Response

1. Check worker status via `swarm({ operation: "monitor", operation: "status" })`
2. Review error details in progress entries
3. Decide: fix locally or reassign to new worker

### Worker Gets Blocked

Workers should report blockers via progress updates:

```typescript
// Worker reports blocker via progress update
await swarm({
  operation: "monitor",
  operation: "progress_update",
  team_name: "plan-implementation",
  worker_id: "worker-2",
  phase: "explore",
  progress: 50,
  status: "blocked",
  message: "Need auth service types from worker-1",
});
```

## When to Use Swarm vs Single Agent

| Scenario                      | Approach     |
| ----------------------------- | ------------ |
| 1-2 file changes              | Single agent |
| Sequential dependencies       | Single agent |
| 3+ independent parallel tasks | Swarm        |
| Cross-domain work (FE/BE/DB)  | Swarm        |
| Time-sensitive parallel work  | Swarm        |

## Integration with Beads

Swarm works on top of Beads:

1. **Session start**: `swarm sync push` to make tasks visible
2. **Leader claims parent** bead
3. **Workers claim child** beads (via delegation packets)
4. **Progress tracked** via `swarm monitor progress_update`
5. **Completion syncs** back via `swarm sync pull`
6. **Close parent** bead with `br close`

```typescript
// Full integration workflow
await swarm({ operation: "sync", action: "push" }); // Make Beads visible
// ... spawn swarm ...
await swarm({ operation: "monitor", action: "render_block", team_name: "..." }); // Monitor progress
// ... monitor completion ...
await swarm({ operation: "sync", action: "pull" }); // Sync completed back
await bash("br close parent-task --reason 'Swarm completed'");
```

## Quick Reference - Kimi K2.5 PARL Pattern

```
SWARM LAUNCH (PARL):
  0. SETUP: swarm({ operation: "sync", action: "push" })
     → Make Beads visible to subagents
  1. ANALYZE: swarm({ operation: "plan", action: "analyze", task: userRequest, files: detectedFiles })
     → Get classification, phases, dependency_graph
  2. CHECK: swarm({ operation: "plan", action: "check", ... })
     → Detect/prevent serial collapse
  3. DELEGATE: swarm({ operation: "delegate", ... })
     → Create packets for each worker
  4. SPAWN: Task({ subagent_type: "general" })
     → Launch workers using parallelizable_groups order
  5. MONITOR: swarm({ operation: "monitor", action: "render_block" })
     → Real-time TUI progress
  6. VERIFY: npm run typecheck && npm run lint && npm test
  7. CLOSE: swarm({ operation: "sync", action: "pull" }) && br close <bead>

WORKER EXECUTION:
  1. Read delegation packet
  2. Report START: swarm({ operation: "monitor", action: "progress_update", progress: 0, status: "working" })
  3. Execute with constraints
  4. Report PROGRESS (every 25%): swarm({ operation: "monitor", action: "progress_update", progress: 25/50/75 })
  5. Run acceptance checks
  6. Report DONE: swarm({ operation: "monitor", action: "progress_update", progress: 100, status: "completed" })

COORDINATION:
  - Progress: .beads/swarm-progress.jsonl (via swarm monitor)
  - Delegation: .beads/artifacts/<id>/delegation.md (via swarm delegate)
  - Analysis: swarm tool for classification + dependency graphs

RECOVERY:
  - Check: swarm({ operation: "monitor", action: "status" })
  - Use shared task lists: swarm({ operation: "sync", action: "create_shared" })
  - Continue with remaining workers

SHUTDOWN:
  - All workers done → swarm({ operation: "monitor", action: "clear" })
  - Run full test suite
  - swarm({ operation: "sync", action: "pull" })
  - Close parent bead
```

## Tools Reference

| Tool      | Purpose                    | Key Operations                        |
| --------- | -------------------------- | ------------------------------------- |
| **swarm** | Unified swarm coordination | `plan`, `monitor`, `delegate`, `sync` |

**swarm operations:**

- `plan`: Task analysis + dependency DAG (actions: analyze, classify, check, allocate)
- `delegate`: Create delegation packets
- `monitor`: Progress tracking + visualization (actions: progress_update, render_block, status, clear)
- `sync`: Beads ↔ OpenCode todos (actions: push, pull, create_shared, get_shared, update_shared, list_shared)

## Tmux Integration (Visual Swarm Monitoring)

Enable real-time visualization of swarm workers in separate tmux panes.

### Setup

1. Start OpenCode inside tmux:

```bash
tmux new -s opencode
opencode
```

2. The tmux tool auto-detects when running inside tmux and uses these defaults:
   - Layout: `main-vertical` (leader left, workers right)
   - Main pane size: 60%
   - Auto-cleanup: enabled

### Detecting Tmux

```typescript
// Check if running inside tmux
const status = await tmux({ operation: "detect" });
const { available, inside_session } = JSON.parse(status);

if (!inside_session) {
  console.log("Tip: Run inside tmux for visual swarm monitoring");
  console.log("Start with: tmux new -s opencode");
}
```

### Spawning Worker Panes

When spawning workers, create visual panes:

```typescript
// Before spawning worker via Task tool
if (inside_session) {
  // Create pane for this worker
  const pane = await tmux({
    operation: "spawn",
    worker_id: "worker-1",
    title: "Explorer: auth.ts",
    size: 40, // 40% width
  });

  const { pane_id } = JSON.parse(pane);

  // Send command to pane (optional - for visual feedback)
  await tmux({
    operation: "send",
    pane_id,
    command: `echo "🔍 Worker-1: Exploring auth.ts..."`,
  });
}

// Spawn the actual worker
await Task({
  subagent_type: "general",
  description: "Execute worker-1",
  prompt: `...`,
});
```

### Layout Options

| Layout            | Description                           | Best For                      |
| ----------------- | ------------------------------------- | ----------------------------- |
| `main-vertical`   | Main pane left, workers stacked right | Default, good for 2-4 workers |
| `main-horizontal` | Main pane top, workers below          | Wide monitors                 |
| `tiled`           | Equal grid for all panes              | Many workers (5+)             |
| `even-horizontal` | Equal width columns                   | 2-3 workers                   |
| `even-vertical`   | Equal height rows                     | 2-3 workers                   |

```typescript
// Change layout dynamically
await tmux({
  operation: "layout",
  layout: "tiled", // When many workers spawn
});
```

### Monitoring Worker Output

```typescript
// Capture output from a worker's pane
const output = await tmux({
  operation: "capture",
  pane_id: "%5",
});

// Check what the worker is doing
console.log(JSON.parse(output).output);
```

### Cleanup

```typescript
// Kill specific pane when worker completes
await tmux({
  operation: "kill",
  pane_id: "%5",
});

// Or cleanup all spawned panes at end of swarm
await tmux({
  operation: "cleanup",
});
```

### User Commands

| Action                  | Keys          |
| ----------------------- | ------------- |
| Switch to next pane     | `Ctrl+B →`    |
| Switch to previous pane | `Ctrl+B ←`    |
| Zoom current pane       | `Ctrl+B z`    |
| Detach (keep running)   | `Ctrl+B d`    |
| Reattach                | `tmux attach` |
| List all panes          | `Ctrl+B w`    |

### Watch Command

Use `/swarm-watch` for real-time progress monitoring:

```bash
/swarm-watch my-swarm-team
```

This renders the beautiful TUI block and shows:

- Worker progress percentages
- Current files being worked on
- Completion status

## Rules

1. **Leader spawns, workers execute** - Clear role separation
2. **Delegation packets are contracts** - Workers follow them strictly
3. **Progress tracking for coordination** - All status via swarm monitor progress updates
4. **Non-overlapping assignments** - Ensure workers edit different files
5. **Acceptance checks required** - Workers verify before reporting done
6. **Persist periodically** - Enable cross-session recovery
7. **Use dependency graph** - Spawn workers in parallelizable_groups order
8. **Graceful shutdown** - Leader waits for all workers, syncs back to Beads
9. **Use tmux for visibility** - Enable visual monitoring when available
