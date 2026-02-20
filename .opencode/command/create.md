---
description: Create a bead with specification from a description
argument-hint: "<description> [--type epic|feature|task|bug]"
agent: build
---

# Create: $ARGUMENTS

Create a bead and its specification (PRD) from a description.

> **Workflow:** **`/create`** → `/start <id>` → `/ship <id>`
>
> ⛔ This command creates the specification ONLY. Do NOT write any implementation code.

## Load Skills

```typescript
skill({ name: "beads" });
skill({ name: "prd" }); // PRD template guidance
```

## Parse Arguments

| Argument        | Default       | Description                        |
| --------------- | ------------- | ---------------------------------- |
| `<description>` | required      | What to build/fix (quoted string)  |
| `--type`        | auto-detected | Override: epic, feature, task, bug |

## Determine Input Type

| Input Type  | Detection            | Action                        |
| ----------- | -------------------- | ----------------------------- |
| Quoted text | `"description here"` | Create PRD from description   |
| Short form  | Simple string        | Ask for more detail if needed |
| `--type`    | Flag provided        | Use provided type             |

## Before You Create

- **Be certain**: Only create beads you're confident have clear scope
- **Don't over-spec**: If the description is vague, ask clarifying questions first
- **Check duplicates**: Always run Phase 1 duplicate check
- **No implementation**: This command creates specs only, don't write code
- **Verify PRD**: Before saving, verify all sections are filled (no placeholders)

## Available Tools

| Tool      | Use When                                     |
| --------- | -------------------------------------------- |
| `explore` | Finding patterns in codebase, affected files |
| `scout`   | External research, best practices            |
| `br`      | Creating and managing beads                  |

## Phase 1: Duplicate Check

```bash
br list --status=open --status=in_progress
```

If a matching bead exists, stop and tell the user to use `/start <id>` instead.

## Phase 2: Classify Type

If `--type` was provided, use it directly. Otherwise, suggest a type based on the description and ask the user to confirm:

- **epic**: Multi-session, cross-domain (redesign, migrate, overhaul)
- **feature**: New capability, scoped (add, implement, build, integrate)
- **bug**: Something broken (fix, error, crash, not working)
- **task**: Tactical change, clear scope (everything else)

## Phase 3: Choose Research Depth

Ask user before spawning agents:

```typescript
question({
  questions: [
    {
      header: "Research Depth",
      question: "How much codebase research do you need?",
      options: [
        {
          label: "Deep (Recommended for complex work)",
          description: "3-5 agents: patterns, tests, deps, best practices (~2 min)",
        },
        {
          label: "Standard",
          description: "2 agents: patterns + tests (~1 min)",
        },
        {
          label: "Minimal",
          description: "1 agent: quick file scan (~30 sec)",
        },
        {
          label: "Skip",
          description: "I know the codebase, use existing knowledge",
        },
      ],
    },
  ],
});
```

## Phase 4: Gather Context

Based on research depth choice, spawn agents:

**If Deep:**

- 3x `explore` (patterns, tests, deps)
- 1x `scout` (feature/epic)
- 1x `review` (epic)

**If Standard:**

- 2x `explore` (patterns, tests)
- 1x `scout` (feature/epic only)

**If Minimal:**

- 1x `explore` (patterns)

**If Skip:**

- No agents, use existing AGENTS.md context

**While agents run**, ask clarifying questions if the description lacks scope or expected outcome. For bugs, also ask for reproduction steps and expected vs actual behavior.

## Phase 5: Create Bead

```bash
BEAD_ID=$(br create "$DESCRIPTION" --type $BEAD_TYPE --json | jq -r '.id')
mkdir -p ".beads/artifacts/$BEAD_ID"
```

## Phase 6: Write PRD

Copy and fill the PRD template using context from Phase 3:

```bash
cp .opencode/memory/_templates/prd.md ".beads/artifacts/$BEAD_ID/prd.md"
```

### Required Sections

| Section           | Source                                                     | Required          |
| ----------------- | ---------------------------------------------------------- | ----------------- |
| Problem Statement | User description + clarifying questions                    | Always            |
| Scope (In/Out)    | User input + codebase exploration                          | Always            |
| Proposed Solution | Codebase patterns + user intent                            | Always            |
| Success Criteria  | User verification + test commands (must include `Verify:`) | Always            |
| Technical Context | Explore agent findings                                     | Always            |
| Affected Files    | Explore agent findings (real paths from Phase 3)           | Always            |
| Tasks             | Derived from scope + solution                              | Always            |
| Risks             | Codebase exploration                                       | Feature/epic only |
| Open Questions    | Unresolved items from Phase 3                              | If any exist      |

### Task Format

Tasks must follow the `prd-task` skill format:

- Title with `[category]` tag
- One-sentence **end state** description (not step-by-step)
- Metadata block: `depends_on`, `parallel`, `conflicts_with`, `files`
- At least one verification command per task

## Phase 7: Validate PRD

Before saving, verify:

- [ ] No placeholder text remains (e.g., "[Clear description", "[List what's allowed]")
- [ ] Success criteria include `Verify:` commands
- [ ] Technical context references actual `src/` paths from exploration
- [ ] Affected files list real paths
- [ ] Tasks have `[category]` headings
- [ ] Each task has verification
- [ ] No implementation code in the PRD

If any check fails, fix it — don't ask the user.

## Phase 8: Report

Output:

1. Bead ID and type
2. PRD location (`.beads/artifacts/$BEAD_ID/prd.md`)
3. Summary: task count, success criteria count, affected files count
4. Next steps: `/start $BEAD_ID` or `/plan $BEAD_ID`

```bash
br comments add $BEAD_ID "Created prd.md with [N] tasks, [M] success criteria"
```

---

## Related Commands

| Need            | Command       |
| --------------- | ------------- |
| Research first  | `/research`   |
| Plan after spec | `/plan <id>`  |
| Start working   | `/start <id>` |
