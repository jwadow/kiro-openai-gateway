---
name: development-lifecycle
description: Orchestrates the full feature development lifecycle from ideation through verification. Guides through phases (brainstorm → design → specify → plan → implement → verify) and loads appropriate sub-skills at each stage.
---

# Development Lifecycle Orchestration

## Overview

This skill orchestrates the complete feature development workflow, guiding you through each phase and loading the appropriate sub-skills automatically.

**Use when:** Starting any new feature, migration, refactor, or significant change.

**Announce at start:** "I'm using development-lifecycle to guide this work through all phases."

## The Lifecycle

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  IDEATION   │───▶│   DESIGN    │───▶│ SPECIFICATION│───▶│   PLANNING  │───▶│IMPLEMENTATION│
│ brainstorming│   │  design.md  │    │   prd.md    │    │  tasks.md   │    │executing-plans│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │                  │                  │                  │
                          └──────────────────┴──────────────────┴──────────────────┤
                                              │                                     ▼
                                    ┌─────────────────┐                   ┌─────────────┐
                                    │    RESEARCH     │                   │VERIFICATION │
                                    │   (optional)    │                   │verification-│
                                    │ /research cmd   │                   │before-      │
                                    └─────────────────┘                   │completion   │
                                                                          └─────────────┘
```

**Note:** Research (`/research <bead-id>`) can happen at any phase when you need external information or deeper codebase understanding. It's not a sequential step but a parallel activity.

## Phase 1: Ideation (brainstorming)

**When:** You have a rough idea but need to explore and refine it.

**Load skill:**

```typescript
skill({ name: "brainstorming" });
```

**Entry criteria:** User has an idea or problem to solve.

**Process:**

1. Understand current project context
2. Ask questions one at a time (prefer multiple choice)
3. Explore 2-3 approaches with trade-offs
4. Present design in 200-300 word sections

**Exit criteria:**

- Design validated by user
- Output: `.beads/artifacts/<bead-id>/design.md`

**Template:** `.opencode/memory/_templates/design.md`

---

## Phase 2: Specification (prd)

**When:** Design is validated, need formal requirements and task breakdown.

**Load skill:**

```typescript
skill({ name: "prd" });
```

**Entry criteria:** Design document exists and is validated.

**Process:**

1. Confirm bead id (create if needed: `br create "Feature Name"`)
2. Ask clarifying questions (5-7 max)
3. Explore codebase patterns and constraints
4. Write PRD with machine-convertible Tasks section

**Exit criteria:**

- PRD with all sections completed
- Output: `.beads/artifacts/<bead-id>/prd.md`

**Template:** `.opencode/memory/_templates/prd.md`

---

## Phase 3: Task Conversion (prd-task)

**When:** PRD is complete, need executable task list.

**Load skill:**

```typescript
skill({ name: "prd-task" });
```

**Entry criteria:** PRD exists at `.beads/artifacts/<bead-id>/prd.md`.

**Process:**

1. Read PRD and extract ## Tasks section
2. Convert to JSON format with dependencies
3. Create progress.txt for cross-iteration memory

**Exit criteria:**

- JSON task file created
- Progress file initialized
- Output: `.beads/artifacts/<bead-id>/prd.json`, `progress.txt`

---

## Phase 4: Planning (writing-plans)

**When:** Tasks defined, need detailed implementation instructions.

**Load skill:**

```typescript
skill({ name: "writing-plans" });
```

**Entry criteria:** Task list exists (prd.json or tasks.md).

**Process:**

1. Create bite-sized steps (2-5 min each)
2. Include exact file paths, complete code
3. TDD: write failing test → verify fail → implement → verify pass → commit
4. Add verification commands for each step

**Exit criteria:**

- Detailed plan ready for execution
- Output: `.beads/artifacts/<bead-id>/plan.md`

**Template:** `.opencode/memory/_templates/tasks.md` (for task structure reference)

---

## Phase 5: Implementation (executing-plans)

**When:** Plan is ready, time to build.

**Load skill:**

```typescript
skill({ name: "executing-plans" });
```

**Entry criteria:** Plan exists at `.beads/artifacts/<bead-id>/plan.md`.

**Process:**

1. Load and review plan critically
2. Execute in 3-task batches
3. Report for feedback between batches
4. Stop on blockers, don't guess

**Exit criteria:**

- All tasks completed
- All verifications pass
- Ready for final verification

---

## Phase 6: Verification (verification-before-completion)

**When:** Implementation complete, before claiming done.

**Load skill:**

```typescript
skill({ name: "verification-before-completion" });
```

**Entry criteria:** All implementation tasks marked complete.

**Process:**

1. IDENTIFY: What commands prove completion?
2. RUN: Execute full verification suite fresh
3. READ: Check output, count failures
4. VERIFY: Does output confirm the claim?
5. ONLY THEN: Claim completion

**Exit criteria:**

- All verification commands pass with evidence
- Bead can be closed: `br close <bead-id>`

---

## Phase Transitions

### Quick Start (Skip to appropriate phase)

| Starting Point                    | Begin At | Command                                             |
| --------------------------------- | -------- | --------------------------------------------------- |
| Rough idea                        | Phase 1  | `skill({ name: "brainstorming" })`                  |
| Design done, need requirements    | Phase 2  | `skill({ name: "prd" })`                            |
| PRD done, need task JSON          | Phase 3  | `skill({ name: "prd-task" })`                       |
| Tasks defined, need detailed plan | Phase 4  | `skill({ name: "writing-plans" })`                  |
| Plan ready, time to build         | Phase 5  | `skill({ name: "executing-plans" })`                |
| Done coding, need verification    | Phase 6  | `skill({ name: "verification-before-completion" })` |

### Skipping Phases

For small changes, you can skip early phases:

- **Bug fix:** Skip to Phase 5 (implement directly with verification)
- **Clear requirements:** Skip Phase 1, start at Phase 2
- **Simple refactor:** Skip to Phase 4 (plan) or Phase 5 (execute)

---

## Templates Reference

| Phase         | Template                 | Purpose                       |
| ------------- | ------------------------ | ----------------------------- |
| Design        | `_templates/design.md`   | Architecture decisions        |
| Specification | `_templates/prd.md`      | Requirements + task breakdown |
| Planning      | `_templates/tasks.md`    | Detailed task structure       |
| Quick Ideas   | `_templates/proposal.md` | Lightweight change proposals  |

---

## Beads Integration

Every phase should operate within a bead context:

```bash
# Create bead for new feature
br create "Feature Name"

# Check current bead status
br show <bead-id>

# Update status as you progress
br update <bead-id> --status in_progress

# Close when complete
br close <bead-id> --reason "All verification passed"

# Sync changes
br sync --flush-only
```

---

## Example Full Workflow

```
User: "I want to add a dark mode toggle"

1. IDEATION
   → skill({ name: "brainstorming" })
   → Questions about scope, triggers, persistence
   → Design decisions documented
   → Output: .beads/artifacts/br-dark-mode/design.md

2. SPECIFICATION
   → skill({ name: "prd" })
   → Full PRD with requirements
   → Tasks section for conversion
   → Output: .beads/artifacts/br-dark-mode/prd.md

3. TASK CONVERSION
   → skill({ name: "prd-task" })
   → JSON task list with dependencies
   → Output: .beads/artifacts/br-dark-mode/prd.json

4. PLANNING
   → skill({ name: "writing-plans" })
   → Bite-sized implementation steps
   → Output: .beads/artifacts/br-dark-mode/plan.md

5. IMPLEMENTATION
   → skill({ name: "executing-plans" })
   → Execute in batches with feedback
   → All code written and committed

6. VERIFICATION
   → skill({ name: "verification-before-completion" })
   → Tests pass: ✓
   → Lint clean: ✓
   → Build succeeds: ✓
   → br close br-dark-mode --reason "Dark mode implemented and verified"
```

---

## Key Principles

1. **Phase-appropriate skills:** Load the right skill for each phase
2. **Evidence at every gate:** No phase transition without verification
3. **Templates guide structure:** Use templates for consistent output
4. **Beads track progress:** Every feature gets a bead
5. **Skip only when appropriate:** Small changes can skip early phases
