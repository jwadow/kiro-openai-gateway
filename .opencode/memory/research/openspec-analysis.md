# OpenSpec Research Analysis

**Date:** 2026-02-01
**Source:** https://github.com/Fission-AI/OpenSpec

## What is OpenSpec?

OpenSpec is a **spec-driven development framework** for AI coding assistants. It provides:
- A structured workflow for planning → implementing → verifying changes
- Schema-based artifact generation (proposal → specs → design → tasks)
- Git-tracked change folders with delta specs
- Archive system that merges changes into canonical specs

## Core Philosophy

| Principle | Description |
|-----------|-------------|
| **Fluid, not rigid** | Commands are actions, not phase gates |
| **Iterative, not waterfall** | Edit artifacts during implementation |
| **Easy, not complex** | Sensible defaults, minimal config |
| **Brownfield-first** | Existing code > greenfield patterns |

## Key Concepts

### Directory Structure
```
openspec/
├── config.yaml          # Project settings, context, rules
├── specs/               # Source of truth for current behavior
└── changes/
    └── <change-name>/
        ├── .openspec.yaml
        ├── proposal.md
        ├── specs/       # Delta specs (ADDED/MODIFIED/REMOVED)
        ├── design.md
        └── tasks.md
```

### Artifact Flow (DAG)
```
proposal → specs → design → tasks → apply
```

Dependencies are **enablers not gates** - can edit earlier artifacts later.

### Commands (OPSX Syntax)
| Command | Purpose |
|---------|---------|
| `/opsx:explore` | Think through ideas before committing |
| `/opsx:new` | Create change folder |
| `/opsx:continue` | Create next artifact |
| `/opsx:ff` | Fast-forward (create all artifacts) |
| `/opsx:apply` | Implement from tasks |
| `/opsx:verify` | Validate completeness/correctness/coherence |
| `/opsx:sync` | Merge delta specs to main specs |
| `/opsx:archive` | Complete and archive change |

---

## Schema System

### schema.yaml Format
```yaml
name: spec-driven
version: 1
description: The default workflow

artifacts:
  - id: proposal
    generates: proposal.md
    template: proposal.md
    instruction: |
      Create a proposal explaining WHY this change is needed.
    requires: []

  - id: specs
    generates: specs/**/*.md
    template: spec.md
    instruction: |
      Create spec files for each capability.
    requires: [proposal]

  - id: design
    generates: design.md
    template: design.md
    requires: [specs]

  - id: tasks
    generates: tasks.md
    template: tasks.md
    requires: [design]

apply:
  requires: [tasks]
  tracks: tasks.md
```

### config.yaml Format
```yaml
schema: spec-driven

context: |
  Tech stack: TypeScript, React, Node.js
  API style: RESTful
  Testing: Jest

rules:
  proposal:
    - Include rollback plan
  specs:
    - Use Given/When/Then format
```

- **context**: Injected into ALL artifacts
- **rules**: Injected only into MATCHING artifact

---

## What OpenCodeKit Can Learn

### 1. **Artifact-Based Workflow** (HIGH VALUE)
OpenSpec separates planning artifacts with explicit dependencies:
- `proposal.md` → Why + scope
- `specs/**/*.md` → Behavioral specs
- `design.md` → How to implement
- `tasks.md` → Checklist

**Current gap:** Our `/plan` creates a single plan.md. Consider:
- Explicit spec files per capability
- Delta spec format for changes to existing behavior

### 2. **Schema-Driven Configuration** (MEDIUM VALUE)
OpenSpec uses YAML schemas that define:
- Artifact types and their dependencies
- Templates for each artifact
- Instructions for AI

**Current gap:** Our commands are hardcoded. Consider:
- Making command workflows configurable via schema
- Custom workflows per project (rapid, spec-driven, research-first)

### 3. **Context + Rules Injection** (HIGH VALUE)
OpenSpec injects project context and per-artifact rules into prompts.

**Current gap:** Our AGENTS.md is global. Consider:
- `config.yaml` with `context:` block for project-specific injection
- Per-artifact rules in command definitions

### 4. **Verify Command** (MEDIUM VALUE)
OpenSpec has explicit `/opsx:verify` that checks:
- Completeness: All artifacts exist, tasks itemized
- Correctness: Implementation matches specs
- Coherence: Artifacts don't contradict each other

**Current gap:** Our `/ship` has verification gates but not coherence checking.

### 5. **Archive/Sync Flow** (LOW VALUE for now)
OpenSpec maintains canonical specs and merges deltas.

**Current gap:** Not needed yet. We don't track specs long-term.

### 6. **Fluid Actions vs Phase Gates** (HIGH VALUE)
OpenSpec allows editing artifacts during implementation - no rigid phases.

**Current status:** Our workflow is already fluid (Beads). No change needed.

---

## Recommended Adaptations

### Phase 1: Config-Based Context Injection
Add to `.opencode/opencode.json`:
```json
{
  "context": "Tech stack: TypeScript, React...",
  "rules": {
    "plan": ["Include rollback plan"],
    "ship": ["Run all verification gates"]
  }
}
```

### Phase 2: Schema-Configurable Workflows
Create `.opencode/schema/` for custom command workflows:
```yaml
# .opencode/schema/rapid.yaml
name: rapid
artifacts:
  - id: proposal
    template: proposal.md
  - id: tasks
    template: tasks.md
    requires: [proposal]
```

### Phase 3: Spec Files Per Bead
Create spec structure:
```
.beads/artifacts/<bead-id>/
├── spec.md           # Current (single file)
├── specs/            # NEW: Per-capability specs
│   └── <capability>.md
└── plan.md
```

---

## Key Differences

| Aspect | OpenSpec | OpenCodeKit |
|--------|----------|-------------|
| Task tracking | Filesystem-based | Beads (git-backed) |
| Workflow | Schema-defined | Command-defined |
| Specs | Canonical + Delta | Per-bead only |
| Config | YAML | JSON |
| Context injection | Built-in | Manual (AGENTS.md) |
| Verification | 3 dimensions | Test/lint gates |

---

## Next Steps

1. **Immediate:** Add `context` block to opencode.json spec
2. **Short-term:** Create `/verify` command with coherence checking
3. **Medium-term:** Schema-configurable workflows
4. **Long-term:** Canonical spec maintenance (if needed)
