---
name: prd
description: Create Product Requirements Documents (PRDs) that define the end state of a feature. Use when planning new features, migrations, or refactors. Generates structured PRDs with acceptance criteria.
---

# PRD Creation Skill

Create Product Requirements Documents suitable for RFC review by Principal Engineers, Designers, and Product Owners.

The PRD describes WHAT to build and WHY, not HOW or in WHAT ORDER.

**Part of:** `development-lifecycle` skill (Phase 2: Specification)

**Template:** `.opencode/memory/_templates/prd.md`

## Beads-Native Output (Recommended)

When you are working on a Beads task (you have a bead id like `br-...`), the PRD should live with the task artifacts:

- Write PRD to: `.beads/artifacts/<bead-id>/prd.md`

This keeps requirements + execution tasks colocated with the bead.

If no bead id exists, create one first: `br create "Feature Name"`, then use the artifact path.

## Workflow

1. Confirm if the user has an existing bead id.
   - If yes: use `.beads/artifacts/<bead-id>/prd.md`
   - If no: create bead with `br create "Feature Name"`, then use artifact path
2. Read template from `.opencode/memory/_templates/prd.md`
3. Ask clarifying questions (5–7 max).
4. Explore codebase patterns and constraints.
5. Write a PRD following the template structure, including:
   - Bead Metadata (dependencies, parallel, conflicts)
   - Requirements with WHEN/THEN scenarios
   - Machine-convertible `## Tasks` section

## Clarifying Questions

### Problem & Motivation

- What problem does this solve? Who experiences it?
- What's the cost of NOT solving this? (user pain, revenue, tech debt)
- Why now? What triggered this work?

### Users & Stakeholders

- Who are the primary users? Secondary users?

### End State & Success

- What does "done" look like? How will users interact with it?

### Scope & Boundaries

- What's explicitly OUT of scope?
- What's deferred to future iterations?
- Are there adjacent features that must NOT be affected?

### Constraints & Requirements

- Performance requirements?
- Security requirements? (auth, data sensitivity, compliance)
- Compatibility requirements? (browsers, versions, APIs)
- Accessibility requirements? (WCAG level, screen readers)

### Risks & Dependencies

- What could go wrong? Technical risks?
- External service dependencies?
- What decisions are still open/contentious?

## Output Format

**Read the template:** `.opencode/memory/_templates/prd.md`

Follow the template structure which includes:

- Bead Metadata (dependencies, parallel execution, conflicts)
- Problem Statement with WHEN/THEN scenarios
- Scope (In/Out)
- Requirements (Functional + Non-Functional)
- Success Criteria with verification commands
- Technical Context and Affected Files
- Tasks section with Metadata (depends_on, parallel, files)

### Task Format (Critical)

Tasks must include **Metadata** for dependency tracking:

````markdown
### <Task Title> [category]

<One sentence describing the end state>

**Metadata:**

```yaml
depends_on: []
parallel: true
conflicts_with: []
files: []
```
````

**Verification:**

- [Command or check]

```

## Next Steps

After PRD is written, tell the user:

```

PRD written: .beads/artifacts/<bead-id>/prd.md

Next: Convert to executable tasks:
skill({ name: "prd-task" })

Or view the full lifecycle:
skill({ name: "development-lifecycle" })

```

## Key Principles

- Problem Before Solution
- Define End State, Not Process
- Technical Context Enables Autonomy
- Non-Goals Prevent Scope Creep
- Risks & Alternatives Show Rigor
- Include Metadata for parallel execution
```
