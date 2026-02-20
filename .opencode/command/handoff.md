---
description: Save progress and context for next session
argument-hint: "<bead-id> [instructions]"
agent: build
---

# Handoff: $ARGUMENTS

Save state so the next session can pick up cleanly.

> **Workflow:** Run this when pausing work. Resume with `/resume $ARGUMENTS`.

## Parse Arguments

| Argument         | Default  | Description                        |
| ---------------- | -------- | ---------------------------------- |
| `<bead-id>`      | required | The bead to hand off               |
| `[instructions]` | none     | Extra context for the next session |

## Load Skills

```typescript
skill({ name: "beads" });
skill({ name: "memory-system" });
```

---

## Phase 1: Gather State (Parallel)

```bash
br show $ARGUMENTS
git status --porcelain
git branch --show-current
git rev-parse --short HEAD
ls .beads/artifacts/$ARGUMENTS/ 2>/dev/null
```

---

## Phase 2: Handle Uncommitted Changes

If `git status` shows uncommitted changes, ask the user:

```typescript
question({
  questions: [
    {
      header: "Uncommitted work",
      question: "You have uncommitted changes. What should we do?",
      options: [
        { label: "Commit as WIP (Recommended)", description: "git commit -m 'WIP: $ARGUMENTS'" },
        { label: "Leave uncommitted", description: "Skip commit, just write handoff" },
      ],
    },
  ],
});
```

If user chooses commit:

```bash
git add -A
git commit -m "WIP: $ARGUMENTS - [brief description of where you stopped]"
```

---

## Phase 3: Write Handoff

Write the handoff to the memory system:

```typescript
memory_update({
  file: "handoffs/$ARGUMENTS",
  content: `# Handoff: $ARGUMENTS

**Date:** [timestamp]
**Branch:** [from git branch]
**Commit:** [from git rev-parse]

## Done
- [completed work]

## In Progress
- [current step] — stopped because [reason]

## Remaining
- [next steps]

## Files Touched
- \`path/to/file.ts\` — [what changed]

## Decisions
- [decision]: [why]

## Blockers
[any blockers, or "None"]

## Resume Instructions
1. [first thing to do]
2. [second thing to do]

Resume with: \`/resume $ARGUMENTS\`
`,
  mode: "replace",
});
```

---

## Phase 4: Record Learnings (If Any)

If you discovered patterns or gotchas worth remembering:

```typescript
observation({
  type: "learning",
  title: "[concise, searchable title]",
  narrative: "[what you learned — specific and actionable]",
  bead_id: "$ARGUMENTS",
  concepts: "[keywords for search]",
});
```

---

## Phase 5: Sync

```bash
br sync --flush-only
```

---

## Output

```
Handoff: $ARGUMENTS
━━━━━━━━━━━━━━━━━━━

Branch: [branch]
Commit: [hash]
Saved:  handoffs/$ARGUMENTS (memory system)

Next session: /resume $ARGUMENTS
```
