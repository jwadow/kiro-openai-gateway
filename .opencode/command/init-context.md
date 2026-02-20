---
description: Initialize GSD-style project planning context with integrated skill usage
argument-hint: "[--skip-questions] [--brownfield]"
agent: build
---

# Init-Context: $ARGUMENTS

Initialize GSD-style project planning with integrated skill usage.

## Load Skills

```typescript
skill({ name: "context-initialization" });
skill({ name: "brainstorming" });
skill({ name: "verification-before-completion" });
```

## Parse Arguments

```typescript
const args = {
  skipQuestions: $ARGUMENTS.includes("--skip-questions"),
  brownfield: $ARGUMENTS.includes("--brownfield"),
  focus: $ARGUMENTS.match(/--focus=(\w+)/)?.[1], // Optional: api, ui, db, etc.
};
```

## Phase 1: Discovery

### 1.1 Check Existing Context

```bash
ls .opencode/memory/project/ 2>/dev/null && HAS_CONTEXT=true || HAS_CONTEXT=false
cat .opencode/memory/project/project.md 2>/dev/null | head -20
```

**If context exists:**

```
Existing planning context found:
- project.md: [exists/size]
- roadmap.md: [exists/size]
- state.md: [exists/size]

Options:
1. Refresh - Delete and recreate from templates
2. Update - Keep existing, only update state.md
3. Skip - Use existing context as-is
```

Wait for user selection.

### 1.2 Brownfield Codebase Analysis (if --brownfield)

If `--brownfield` flag is set:

```typescript
// Spawn parallel analysis agents (like GSD map-codebase)
skill({ name: "swarm-coordination" });

// Agent 1: Map tech stack
Task({
  subagent_type: "explore",
  description: "Analyze tech stack",
  prompt:
    "Analyze the codebase technology stack. Write findings to .opencode/memory/project/tech-analysis.md covering: languages, frameworks, dependencies, build tools. Return file path and line count only.",
});

// Agent 2: Map architecture
Task({
  subagent_type: "explore",
  description: "Analyze architecture",
  prompt:
    "Analyze the codebase architecture. Write findings to .opencode/memory/project/arch-analysis.md covering: patterns, directory structure, entry points. Return file path and line count only.",
});

// Wait for agents and collect confirmations
```

## Phase 2: Requirements Gathering

### 2.1 Load Brainstorming Skill (if not --skip-questions)

```typescript
if (!args.skipQuestions) {
  skill({ name: "brainstorming" });

  // Follow brainstorming process for project vision
  // Ask questions one at a time (as per brainstorming skill)
  // Output: Refined vision, success criteria, target users
}
```

### 2.2 Quick Mode (if --skip-questions)

Use template defaults with placeholders for:

- Project vision
- Success criteria
- Target users
- Phases
- Current phase

## Phase 3: Document Creation

### 3.1 Create project.md

**Load template:**

```bash
cat .opencode/memory/_templates/project.md
```

**Fill with gathered data:**

- Vision from brainstorming OR template placeholder
- Success criteria (3-7 measurable outcomes)
- Target users (primary/secondary)
- Core principles (convention over config, minimal, extensible)
- Current phase (from user input or template default)

**Write to:** `.opencode/memory/project/project.md`

### 3.2 Create roadmap.md

**Parse phases from input:**

```typescript
// Convert user-provided phases into structured roadmap
// Example: "Discovery, MVP, Launch, Scale" → table rows
```

**Structure:**

```markdown
| Phase     | Goal   | Status   | Beads |
| --------- | ------ | -------- | ----- |
| [Phase 1] | [Goal] | [Status] | [#]   |
```

**Write to:** `.opencode/memory/project/roadmap.md`

### 3.3 Create state.md

**Initialize with:**

- Active Bead: (blank or from bead context)
- Status: In Progress
- Started: [current date]
- Phase: [from roadmap]
- Recent Completed Work: (empty table)
- Active Decisions: (empty table)
- Blockers: (empty table)
- Open Questions: (empty table)
- Next Actions: (empty list)

**Write to:** `.opencode/memory/project/state.md`

### 3.4 Brownfield Analysis Integration (if applicable)

If `--brownfield` analysis was run:

```typescript
// Append tech/arch findings to project.md Context Notes section
// Or create separate .opencode/memory/project/codebase/ documents
// (similar to GSD's .planning/codebase/ approach)
```

## Phase 4: Verification & Security

### 4.1 Verify Documents Created

```bash
ls -la .opencode/memory/project/
wc -l .opencode/memory/project/*.md
```

**Check:**

- [ ] project.md exists and >20 lines
- [ ] roadmap.md exists and >20 lines
- [ ] state.md exists and >20 lines
- [ ] All files are readable

### 4.2 Secret Scan (Critical - from GSD pattern)

```bash
# Scan for accidentally leaked secrets in generated docs
grep -E '(sk-[a-zA-Z0-9]{20,}|sk_live_[a-zA-Z0-9]+|AKIA[A-Z0-9]{16}|ghp_[a-zA-Z0-9]{36}|-----BEGIN.*PRIVATE KEY)' .opencode/memory/project/*.md 2>/dev/null && SECRETS_FOUND=true || SECRETS_FOUND=false
```

**If secrets found:** Alert user and pause before proceeding.

### 4.3 Load Verification Skill

```typescript
skill({ name: "verification-before-completion" });

// Run verification checklist:
// 1. IDENTIFY: Files created, structure valid
// 2. RUN: Validation commands
// 3. READ: Check file contents
// 4. VERIFY: All success criteria met
// 5. CLAIM: Context initialization complete
```

## Phase 5: Beads Integration

### 5.1 Create Initialization Bead (optional)

```bash
# If user wants to track context setup as a bead
br create "Initialize project context" --type=task
br update <bead-id> --status closed --reason="Context files created"
```

## Output

Creates in `.opencode/memory/project/`:

| File         | Purpose                                  | Lines (typical) |
| ------------ | ---------------------------------------- | --------------- |
| `project.md` | Vision, success criteria, principles     | 50-100          |
| `roadmap.md` | Phases, milestones, bead planning        | 80-150          |
| `state.md`   | Current position, blockers, next actions | 60-100          |

**If `--brownfield`:**
Additional files in `.opencode/memory/project/codebase/`:

- `tech-analysis.md` - Stack and dependencies
- `arch-analysis.md` - Architecture patterns

## Success Criteria

- [ ] All required documents created from templates
- [ ] Documents follow template structure
- [ ] No secrets leaked in generated files
- [ ] Files pass basic validation (readable, non-empty)
- [ ] User informed of next steps

## Next Steps

After init-context completes:

1. **For new projects:** Use `/plan` to create first implementation plan
2. **For brownfield:** Review codebase analysis, then `/plan`
3. **For existing beads:** Use `/resume` to continue tracked work

---

## Skill Integration Summary

| Skill                            | When Used                         | Purpose                        |
| -------------------------------- | --------------------------------- | ------------------------------ |
| `brainstorming`                  | Phase 2 (if not --skip-questions) | Refine vision and requirements |
| `swarm-coordination`             | Phase 1.2 (if --brownfield)       | Parallel codebase analysis     |
| `verification-before-completion` | Phase 4                           | Validate created files         |
| `beads`                          | Phase 5                           | Track as bead if desired       |
