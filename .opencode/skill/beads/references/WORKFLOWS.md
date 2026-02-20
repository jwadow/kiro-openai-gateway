# Workflows and Checklists

Detailed step-by-step workflows for common beads usage patterns.

**Note:** `br` (beads_rust) is non-invasive and never executes git commands. After `br sync --flush-only`, you must manually run `git add .beads/ && git commit`.

## Session Start Workflow

**Every session when beads is available:**

```
Session Start:
- [ ] br ready to find unblocked work
- [ ] br update <id> --status in_progress to claim
- [ ] If none ready, br list --status open
- [ ] br show <id> for full context
- [ ] Begin work
```

## Compaction Survival

**Critical**: After compaction, conversation history is deleted but beads state persists.

**Post-compaction recovery:**

```
After Compaction:
- [ ] br list --status in_progress to see active work
- [ ] br show <id> for each in_progress task
- [ ] Read notes: COMPLETED, IN PROGRESS, BLOCKERS, KEY DECISIONS
- [ ] Reconstruct TodoWrite from notes if needed
```

**Writing notes for compaction survival:**

**Good note (enables recovery):**

```
COMPLETED: User auth - JWT tokens with 1hr expiry, refresh endpoint.
IN PROGRESS: Password reset flow. Email service working.
NEXT: Add rate limiting to reset endpoint.
KEY DECISION: Using bcrypt 12 rounds per OWASP.
```

**Bad note:**

```
Working on auth. Made some progress.
```

## Discovery Workflow

**When encountering new work during implementation:**

```
Discovery:
- [ ] Notice bug, improvement, or follow-up
- [ ] Assess: blocker or deferrable?
- [ ] br create --title "..." --type bug --priority 1
- [ ] If blocker: pause and switch
- [ ] If deferrable: continue current work
```

## Epic Planning

**For complex multi-step features, think in Ready Fronts.**

A **Ready Front** is the set of tasks with all dependencies satisfied.

**Walk backward from goal:**

```
"What's the final deliverable?"
  ↓
"Integration tests passing" → task-integration
  ↓
"What does that need?"
  ↓
"Streaming support" → task-streaming
"Header display" → task-header
  ↓
"What do those need?"
  ↓
"Message rendering" → task-messages
  ↓
"Buffer layout" → task-buffer (foundation)
```

**Example: OAuth Integration**

```bash
# Create epic
br create --title "OAuth integration" --type epic --priority 1

# Walk backward: What does OAuth need?
br create --title "Login/logout endpoints" --parent oauth-abc
br create --title "Token storage and refresh" --parent oauth-abc
br create --title "Authorization code flow" --parent oauth-abc
br create --title "OAuth client credentials" --parent oauth-abc  # foundation
```

## Side Quest Handling

```
Side Quest:
- [ ] During main work, discover problem
- [ ] br create for side quest
- [ ] Assess: blocker or deferrable?
- [ ] If blocker: switch to side quest
- [ ] If deferrable: note it, continue main work
```

## Session Handoff

**At Session End:**

```
Session End:
- [ ] Work reaching stopping point
- [ ] Update notes with COMPLETED/IN PROGRESS/NEXT
- [ ] br close <id> --reason "..." if task complete
- [ ] Otherwise leave in_progress with notes
- [ ] br sync --flush-only
- [ ] git add .beads/ && git commit -m "session end"
- [ ] RESTART SESSION
```

**At Session Start:**

```
Session Start with in_progress:
- [ ] br list --status in_progress
- [ ] br show <id> for each
- [ ] Read notes field
- [ ] Continue from notes context
```

## Unblocking Work

**When ready list is empty:**

```
Unblocking:
- [ ] br list --status open to see all tasks
- [ ] Identify blocked tasks and their blockers
- [ ] Work on blockers first
- [ ] Closing blocker unblocks dependent work
```

## Integration with TodoWrite

**Using both tools:**

```
Hybrid:
- [ ] br ready to find high-level task
- [ ] br update <id> --status in_progress
- [ ] Create TodoWrite from acceptance criteria
- [ ] Work through TodoWrite items
- [ ] Update br notes as you learn
- [ ] When TodoWrite complete, br close <id>
```

**Why hybrid**: br provides persistent structure, TodoWrite provides visible progress.

## Common Patterns

### Systematic Exploration

```
1. Create research task
2. Update notes with findings
3. br create for discoveries
4. Close research with conclusion
```

### Bug Investigation

```
1. Create bug task
2. Reproduce: note steps
3. Investigate: track hypotheses in notes
4. Fix: implement solution
5. Close with root cause explanation
```

### Refactoring with Dependencies

```
1. Create tasks for each step
2. Work through in dependency order
3. br ready shows next step
4. Each completion unblocks next
```

## Checklist Templates

### Starting Any Session

```
- [ ] br ready
- [ ] br update <id> --status in_progress
- [ ] br show <id> for context
- [ ] Begin work
```

### Creating Tasks During Work

```
- [ ] Notice new work needed
- [ ] br create --title "..." with clear title
- [ ] Add context in description
- [ ] Assess blocker vs deferrable
```

### Completing Work

```
- [ ] Implementation done
- [ ] Tests passing
- [ ] br close <id> --reason "..."
- [ ] br sync --flush-only
- [ ] git add .beads/ && git commit
- [ ] br ready for next work
- [ ] RESTART SESSION
```
