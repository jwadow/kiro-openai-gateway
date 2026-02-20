---
name: agent-teams
description: >
  Use when working with Claude Code-style agent teams for parallel research, review, competing hypotheses,
  or any task that benefits from multiple agents working simultaneously under a lead coordinator.
  Covers team configuration, task distribution, coordination patterns, and best practices.
version: "1.0.0"
license: MIT
---

# Agent Teams - Multi-Agent Team Coordination

Coordinate multiple agents working as a team under a lead agent. Unlike subagents (fire-and-forget), teams enable continuous coordination, shared context, and dynamic task reassignment.

## Overview

**Agent Teams = Lead + Teammates + Shared Task List + Messaging**

- **Lead agent**: Coordinates the team - distributes tasks, monitors progress, synthesizes results
- **Teammates**: Execute tasks independently but can message each other and the lead
- **Task list**: Shared work queue that the lead manages
- **Messaging**: Bidirectional communication between lead and teammates

## When to Use Agent Teams vs Subagents

| Criteria              | Agent Teams                            | Subagents (Task tool)               |
| --------------------- | -------------------------------------- | ----------------------------------- |
| **Coordination**      | Lead coordinates, teammates message    | Fire-and-forget, results return     |
| **Communication**     | Bidirectional messaging                | One-way (result only)               |
| **Task reassignment** | Dynamic - lead can reassign            | Fixed - each subagent does its task |
| **Context sharing**   | Shared through lead                    | Independent contexts                |
| **Best for**          | Research, review, competing approaches | Independent implementation tasks    |
| **Overhead**          | Higher - coordination cost             | Lower - no coordination             |

### Decision Matrix

```
Need coordination between workers?  → Agent Teams
Workers are fully independent?      → Subagents (Task tool)
Need competing hypotheses?          → Agent Teams
Need shared findings?               → Agent Teams
Simple parallel execution?          → Subagents (Task tool)
```

## When to Use

- **Parallel research**: Multiple agents researching different aspects of a problem
- **Code review**: Multiple reviewers examining different files/concerns
- **Competing hypotheses**: Agents try different approaches, best one wins
- **Large refactors**: Agents handle different subsystems with coordination
- **Architecture exploration**: Agents explore different design options simultaneously

## When NOT to Use

- Single-agent tasks (overhead not worth it)
- Tightly coupled work where agents would constantly block each other
- Tasks under 3 independent units of work
- Simple file edits with no research needed

## Team Configuration Patterns

### Pattern 1: Research Team

```
Lead: build agent
├── Teammate 1 (explore): Search codebase for existing patterns
├── Teammate 2 (scout): Research external docs and best practices
└── Teammate 3 (review): Analyze current implementation for issues
```

**Use when**: Entering unfamiliar territory, evaluating new libraries, understanding complex systems.

### Pattern 2: Review Team

```
Lead: build agent
├── Teammate 1 (review): Security audit
├── Teammate 2 (review): Performance review
└── Teammate 3 (review): Architecture review
```

**Use when**: Pre-merge review of significant features, security-sensitive changes.

### Pattern 3: Competing Approaches

```
Lead: build agent
├── Teammate 1 (general): Implement approach A
├── Teammate 2 (general): Implement approach B
└── Teammate 3 (general): Implement approach C
```

**Use when**: Multiple valid solutions exist and you need to compare empirically.

### Pattern 4: Subsystem Team

```
Lead: build agent
├── Teammate 1 (general): Handle frontend changes
├── Teammate 2 (general): Handle backend changes
└── Teammate 3 (general): Handle database migrations
```

**Use when**: Large features spanning multiple subsystems with clear boundaries.

## Best Practices

### Task Distribution

1. **5-6 tasks per teammate maximum** - More than this degrades quality
2. **Clear boundaries** - Each teammate should own distinct files/modules
3. **Avoid file conflicts** - Never assign the same file to multiple teammates
4. **Include verification** - Each task should include its own verification step

### Coordination

1. **Lead synthesizes** - Don't let teammates make final decisions; lead integrates
2. **Regular check-ins** - Lead should review intermediate results, not just final
3. **Fail fast** - If a teammate hits a blocker, escalate to lead immediately
4. **Shared conventions** - Establish naming, formatting, and style before dispatching

### Communication

1. **Task descriptions should be self-contained** - Teammate shouldn't need to ask clarifying questions
2. **Include context** - What files to read, what patterns to follow, what constraints exist
3. **Specify output format** - What should the teammate report back?
4. **Include acceptance criteria** - How does the lead know the task is done?

## Implementation with OpenCode

### Using the Task Tool (Current)

```typescript
// Spawn research team
const codebaseAnalysis = Task({
  subagent_type: "explore",
  description: "Analyze auth patterns",
  prompt: `Research authentication patterns in this codebase:
    1. Find all auth-related files
    2. Map the auth flow
    3. Identify potential security issues
    Report back: file list, flow diagram, issues found`,
});

const externalResearch = Task({
  subagent_type: "scout",
  description: "Research JWT best practices",
  prompt: `Research current JWT best practices:
    1. Token rotation patterns
    2. Refresh token security
    3. Common vulnerabilities
    Report back: recommended patterns with code examples`,
});

const codeReview = Task({
  subagent_type: "review",
  description: "Review auth security",
  prompt: `Security review of auth implementation:
    1. Check token storage
    2. Verify CSRF protection
    3. Audit session management
    Report back: vulnerabilities found with severity ratings`,
});

// Lead synthesizes all results into unified recommendation
```

### Using Swarm Coordination (Advanced)

For more structured parallel work, combine with the `swarm-coordination` skill:

```typescript
// Load swarm for structured coordination
skill({ name: "swarm-coordination" });

// Analyze and plan
swarm({ op: "plan", task: "Implement auth overhaul across 3 subsystems" });

// Create delegation packets
swarm({
  op: "delegate",
  bead_id: "auth-frontend",
  title: "Frontend auth components",
  outcome: "All auth forms and guards updated",
  must_do: "Follow existing component patterns, run component tests",
  must_not: "Don't modify API contracts, don't add new dependencies",
});
```

## Anti-Patterns

### ❌ Too Many Teammates

```
Lead
├── T1: Button component     ← Too granular
├── T2: Input component      ← Too granular
├── T3: Form component       ← Too granular
├── T4: Modal component      ← Too granular
├── T5: Toast component      ← Too granular
├── T6: Dialog component     ← Too granular
├── T7: Dropdown component   ← Too granular
└── T8: Tabs component       ← Too granular
```

**Fix**: Group related work. 2-3 teammates handling related components each.

### ❌ Overlapping File Ownership

```
T1: Refactor auth service     ← Both touch auth.ts!
T2: Add new auth endpoint     ← Both touch auth.ts!
```

**Fix**: One teammate owns auth.ts changes. The other waits or works on different files.

### ❌ Missing Context

```
Task({ prompt: "Fix the auth bug" })  ← Which bug? What file? What behavior?
```

**Fix**: Include file paths, error messages, expected vs actual behavior, and reproduction steps.

### ❌ No Verification

```
Task({ prompt: "Implement feature X" })  ← No way to verify success
```

**Fix**: Include acceptance criteria: "Run `npm test auth`, ensure all pass. Run `npm run typecheck`."

## Checklist

Before dispatching a team:

- [ ] Identified 3+ independent tasks (otherwise use single agent)
- [ ] Each task has clear file ownership (no overlaps)
- [ ] Each task has self-contained context (files, patterns, constraints)
- [ ] Each task has acceptance criteria (verification commands)
- [ ] Lead has a synthesis plan (how to integrate results)
- [ ] Tasks are sized appropriately (5-6 per teammate max)
