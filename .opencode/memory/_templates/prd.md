# Beads PRD Template

**Bead:** br-[id]  
**Created:** [date]  
**Status:** Draft | In Review | Approved

## Bead Metadata

```yaml
depends_on: [] # Bead IDs that must complete before this one
parallel: true # Can run concurrently with other parallel beads
conflicts_with: [] # Bead IDs that modify same files (cannot parallelize)
blocks: [] # Bead IDs waiting on this one
estimated_hours: 2 # Time estimate for planning
```

---

## Problem Statement

### What problem are we solving?

[Clear description of the problem. Include user impact and business impact.]

### Why now?

[What triggered this work? Cost of inaction?]

### Who is affected?

- **Primary users:** [Description]
- **Secondary users:** [Description]

---

## Scope

### In-Scope

- [List what's allowed]

### Out-of-Scope

- [List what's explicitly off-limits]
- [Deferred to future iterations]

---

## Proposed Solution

### Overview

[One paragraph describing what this feature does when complete.]

### User Flow (if user-facing)

1. [Step 1]
2. [Step 2]
3. [Step 3]

---

## Requirements

### Functional Requirements

#### [Requirement Name]

Brief description of what must be true.

**Scenarios:**

- **WHEN** [precondition or trigger] **THEN** [expected outcome]
- **WHEN** [edge case condition] **THEN** [expected behavior]

### Non-Functional Requirements

- **Performance:** [constraint if applicable]
- **Security:** [constraint if applicable]
- **Accessibility:** [WCAG level if applicable]
- **Compatibility:** [constraint if applicable]

---

## Success Criteria

- [ ] [Specific, measurable criterion 1]
  - Verify: `[command or manual check]`
- [ ] [Specific, measurable criterion 2]
  - Verify: `[command or manual check]`

---

## Technical Context

### Existing Patterns

- Pattern 1: `src/path/to/example.ts` - Why relevant

### Key Files

- `src/relevant/file.ts` - Why relevant

### Affected Files

Files this bead will modify (for conflict detection):

```yaml
files:
  - src/path/to/file.ts # Why
  - src/path/to/other.ts # Why
```

---

## Risks & Mitigations

| Risk   | Likelihood   | Impact       | Mitigation      |
| ------ | ------------ | ------------ | --------------- |
| Risk 1 | High/Med/Low | High/Med/Low | How to mitigate |

---

## Open Questions

| Question   | Owner | Due Date | Status        |
| ---------- | ----- | -------- | ------------- |
| Question 1 | Name  | Date     | Open/Resolved |

---

## Tasks

Write tasks in a machine-convertible format for `prd-task` skill.

**Rules:**

- Each task is a `### <Title> [category]` heading
- Provide one sentence describing the end state
- Include `**Metadata:**` with dependency info
- Include `**Verification:**` with bullet steps proving it works

### <Task Title> [category]

<One sentence describing the end state>

**Metadata:**

```yaml
depends_on: [] # Task titles that must complete first
parallel: true # Can run with other parallel tasks
conflicts_with: [] # Task titles modifying same files
files: [] # Files this task will modify
```

**Verification:**

- [Command or check]
- [Command or check]

### <Task Title> [category]

<One sentence describing the end state>

**Metadata:**

```yaml
depends_on: ["<Previous Task Title>"]
parallel: false
files: []
```

**Verification:**

- [Command or check]

---

## Dependency Legend

| Field            | Purpose                                           | Example                                    |
| ---------------- | ------------------------------------------------- | ------------------------------------------ |
| `depends_on`     | Must complete before this task starts             | `["Setup database", "Create schema"]`      |
| `parallel`       | Can run concurrently with other parallel tasks    | `true` / `false`                           |
| `conflicts_with` | Cannot run in parallel (same files)               | `["Update config"]`                        |
| `files`          | Files this task modifies (for conflict detection) | `["src/db/schema.ts", "src/db/client.ts"]` |

---

## Notes

[Additional context, constraints, or decisions]
