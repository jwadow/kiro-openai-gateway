# CCPM Research Analysis

**Source:** https://github.com/automazeio/ccpm  
**Research Date:** 2026-02-01  
**Purpose:** Learn and adapt patterns into OpenCodeKit

---

## Executive Summary

CCPM (Claude Code PM) is a comprehensive workflow system for spec-driven development using GitHub Issues as the task database. Key innovations include:

1. **PRD → Epic → Task → Issue pipeline** - Full traceability from idea to code
2. **Parallel agent execution** - Multiple agents working simultaneously via git worktrees
3. **Context preservation** - Agents as "context firewalls" shielding main thread
4. **GitHub-native integration** - Issues as source of truth, no external databases

---

## Architecture Overview

```
ccpm/
├── commands/
│   ├── pm/                    # 40+ project management commands
│   │   ├── prd-new.md         # Create PRD via brainstorming
│   │   ├── prd-parse.md       # PRD → Epic conversion
│   │   ├── epic-decompose.md  # Epic → Tasks breakdown
│   │   ├── epic-sync.md       # Push to GitHub Issues
│   │   ├── issue-start.md     # Begin parallel work
│   │   ├── next.md            # Get prioritized task
│   │   └── status.md          # Project dashboard
│   ├── context/               # Context management
│   │   ├── create.md          # Initialize project context
│   │   ├── prime.md           # Load context for session
│   │   └── update.md          # Refresh context
│   └── testing/               # Test execution
├── agents/                    # Specialized workers
│   ├── parallel-worker.md     # Coordinates parallel streams
│   ├── code-analyzer.md       # Bug hunting specialist
│   ├── test-runner.md         # Test execution + analysis
│   └── file-analyzer.md       # Verbose file summarization
├── rules/                     # Operational guidelines
│   ├── agent-coordination.md  # Parallel work rules
│   ├── standard-patterns.md   # Command patterns
│   └── worktree-operations.md # Git worktree usage
├── context/                   # Project context files
├── prds/                      # Product requirement docs
└── epics/                     # Local workspace
    └── {epic-name}/
        ├── epic.md            # Implementation plan
        ├── {issue}.md         # Individual tasks
        └── updates/           # Progress tracking
```

---

## Key Patterns to Adopt

### 1. PRD-First Development Flow

**CCPM Flow:**

```
/pm:prd-new feature    → Brainstorm + create PRD
/pm:prd-parse feature  → Convert PRD to Epic
/pm:epic-decompose     → Break into tasks
/pm:epic-sync          → Push to GitHub Issues
/pm:issue-start 123    → Begin parallel work
```

**OpenCodeKit Equivalent:**

```
/create <bead> --prd   → Create PRD artifact
/plan <bead>           → Generate implementation plan
/start <bead>          → Begin work with task allocation
```

**Gap:** We don't have `/pm:epic-decompose` equivalent - our `/plan` command does both epic creation AND task decomposition. Consider separating.

---

### 2. Agent Philosophy: "Context Firewalls"

**CCPM Quote:**

> "Don't anthropomorphize subagents. Use them to organize your prompts and elide context. Subagents are best when they can do lots of work but then provide small amounts of information back."

**Key Insight:** Agents aren't "experts" - they're task executors that protect main thread from information overload.

**CCPM Agent Pattern:**

```typescript
// Agent reads 10 files → Main gets 1 summary
Task({
  subagent_type: "code-analyzer",
  prompt: "Hunt bugs in auth module",
  // Returns: "Found 3 issues: [concise list]"
  // Main thread never sees: All the files examined
});
```

**OpenCodeKit Gap:** Our subagents return too much detail. Should adopt concise summary pattern.

---

### 3. Parallel Work via Git Worktrees

**CCPM Innovation:** Each epic gets its own worktree for isolated parallel development.

```bash
# Create worktree for epic
git worktree add ../epic-{name} -b epic/{name}

# Multiple agents work in SAME worktree on DIFFERENT files
Agent-A: src/db/*     → No conflict
Agent-B: src/api/*    → No conflict
Agent-C: src/ui/*     → No conflict
```

**Coordination Rules:**

1. File-level parallelism - different files = no conflict
2. Explicit coordination for shared files
3. Atomic commits with clear messages
4. Human resolution for conflicts (never auto-merge)

**OpenCodeKit Gap:** We have `using-git-worktrees` skill but don't integrate it into task execution flow.

---

### 4. Task File Format with Dependencies

**CCPM Task Frontmatter:**

```yaml
---
name: Implement user authentication
status: open
created: 2024-01-20T10:00:00Z
updated: 2024-01-20T10:00:00Z
github: https://github.com/org/repo/issues/1234
depends_on: [001, 002] # Task dependencies
parallel: true # Can run in parallel
conflicts_with: [003] # Same files modified
---
```

**Key Fields Missing in OpenCodeKit:**

- `depends_on` - Task dependencies
- `parallel` - Parallelization flag
- `conflicts_with` - File conflict tracking

---

### 5. Context Management System

**CCPM Context Files:**

```
.claude/context/
├── project-brief.md       # What + why
├── project-overview.md    # Features + capabilities
├── project-vision.md      # Long-term direction
├── tech-context.md        # Stack + dependencies
├── project-structure.md   # Directory organization
├── system-patterns.md     # Architecture patterns
├── project-style-guide.md # Coding conventions
├── product-context.md     # Users + requirements
└── progress.md            # Current status
```

**Commands:**

- `/context:create` - Initialize all context files
- `/context:prime` - Load context at session start
- `/context:update` - Refresh after changes

**OpenCodeKit Comparison:**

- We have `.opencode/memory/` but less structured
- We lack `/context:prime` equivalent for session start
- Our `memory-read` is more ad-hoc

---

### 6. Standard Output Patterns

**CCPM Standard:**

```markdown
# Success

✅ {Action} complete

- {Key result 1}
- {Key result 2}
  Next: {Single suggested action}

# Error

❌ {What failed}: {Exact solution}

# List

{Count} {items} found:

- {item 1}: {key detail}
- {item 2}: {key detail}
```

**Principles:**

- Fail fast - check essentials, trust the system
- Minimal output - show what matters, skip decoration
- Clear errors - say exactly what and how to fix
- Smart defaults - only ask when destructive

---

### 7. Parallel Execution System

**CCPM Insight:** One issue ≠ one task. One issue = multiple parallel work streams.

```bash
# Issue #1234 explodes into parallel streams:
Agent 1: Database tables
Agent 2: Service layer
Agent 3: API endpoints
Agent 4: UI components
Agent 5: Tests + docs
```

**Velocity Math:**

- Traditional: 3 issues × 1 agent = 3 sequential tasks
- CCPM: 3 issues × 4 streams each = 12 parallel agents

**OpenCodeKit Gap:** Our `/start` command doesn't do stream analysis or parallel agent spawning.

---

## Recommended Adaptations for OpenCodeKit

### Priority 1: Command Enhancements

1. **`/context:prime`** - Load all memory files at session start
2. **`/status`** - Project dashboard showing beads, progress, blockers
3. **`/next`** - Get next priority task with full context
4. **Enhanced `/start`** - Include parallel stream analysis

### Priority 2: Agent Improvements

1. **Concise Returns** - Agents should return summaries, not verbose output
2. **Parallel Worker Pattern** - Coordinator agent that spawns sub-agents
3. **Code Analyzer** - Dedicated bug-hunting agent with structured output

### Priority 3: Task System Enhancements

1. **Dependency Tracking** - `depends_on`, `parallel`, `conflicts_with` fields
2. **Stream Analysis** - Break tasks into parallel work streams
3. **Worktree Integration** - Auto-create worktrees for epics

### Priority 4: Context System

1. **Structured Context Files** - Adopt CCPM's context file categories
2. **Auto-Context Loading** - Prime context automatically on session start
3. **Context Staleness Detection** - Warn when context is outdated

---

## Implementation Recommendations

### Immediate Actions

1. **Create `/prime` command** - Equivalent to `/context:prime`
   - Load `.opencode/memory/` files
   - Show project status
   - List active beads

2. **Create `/status` command** - Project dashboard
   - Bead count by status
   - Recent activity
   - Blockers

3. **Enhance agent return format** - Adopt CCPM's concise summary pattern

### Medium-Term Actions

1. **Add task dependency fields** to bead artifacts
2. **Create `parallel-worker` skill** for coordinated parallel execution
3. **Integrate git worktrees** into `/start` command

### Long-Term Actions

1. **Full context system** with structured categories
2. **GitHub Issues integration** (optional, for teams)
3. **Progress visualization** with dashboard commands

---

## Key Quotes Worth Remembering

> "Every line of code must trace back to a specification." - No vibe coding

> "Simple is not simplistic - we still handle errors properly, we just don't try to prevent every possible edge case."

> "Your main conversation becomes the conductor, not the orchestra."

> "Context preservation: Use extremely concise language. Every word must earn its place."

---

## Files Worth Studying Further

1. `ccpm/commands/pm/issue-analyze.md` - Stream analysis logic
2. `ccpm/commands/pm/epic-start.md` - Worktree creation flow
3. `ccpm/agents/parallel-worker.md` - Coordination patterns
4. `ccpm/rules/agent-coordination.md` - Parallel work rules

---

## Conclusion

CCPM provides a mature, battle-tested workflow for AI-assisted development. The key innovations are:

1. **PRD-driven discipline** - Requirements before code
2. **Parallel by default** - One task = many agents
3. **Context as firewall** - Agents protect main thread
4. **GitHub as database** - No external dependencies

OpenCodeKit can adopt these patterns incrementally, starting with `/prime`, `/status`, and enhanced agent return formats.
