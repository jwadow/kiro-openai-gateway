# Dependency Types Guide

Beads supports task dependencies for ordering work.

## Overview

Dependencies affect what work is "ready" - tasks with unmet dependencies won't appear in `br ready` results.

## Creating Dependencies

```bash
br create --title "Implement API endpoint" --blocked-by setup-db
# This task depends on setup-db completing first
```

## Dependency Patterns

### Sequential Work

```
setup-db → implement-api → add-tests → deploy
```

Each task depends on the previous. `br ready` shows only the current step.

### Parallel Then Merge

```
research-a ─┐
research-b ─┼→ decision
research-c ─┘
```

Multiple parallel tasks, then one that needs all of them.

### Foundation First

```
setup ─┬→ feature-a
       ├→ feature-b
       └→ feature-c
```

One foundational task blocks multiple features.

## Epic with Children

```bash
# Create epic
br create --title "OAuth Integration" --type epic --priority 1
# Returns: oauth-abc

# Create children with parent
br create --title "Setup credentials" --parent oauth-abc
br create --title "Implement flow" --parent oauth-abc --blocked-by credentials
br create --title "Add UI" --parent oauth-abc --blocked-by flow
```

## Automatic Unblocking

When you close a task that's blocking others:

```
1. br close setup-db --reason "Schema created"
2. Beads automatically updates: implement-api is now ready
3. br ready returns implement-api
4. No manual unblocking needed
```

## Common Mistakes

### Using Dependencies for Preferences

**Wrong:**

```
docs depends on feature  // "prefer to update docs after"
```

**Problem:** Documentation doesn't actually need feature complete.

**Right:** Only use dependencies for actual blockers.

### Wrong Direction

**Wrong:**

```bash
br create --title "API" --blocked-by tests  # API depends on tests?
```

**Problem:** Usually tests depend on API, not the other way.

**Right:** Think "X needs Y complete first" → X depends on Y.

### Over-Using Dependencies

**Problem:** Everything depends on everything. No parallel work possible.

**Right:** Only add dependencies for actual technical blockers.

## Decision Guide

**Add dependency when:**

- Task literally cannot start without other task complete
- Code won't compile/run without prerequisite
- Data/schema must exist first

**Skip dependency when:**

- Just a preference for order
- Both can proceed independently
- Just want to note relationship

## Viewing Dependencies

```bash
br show <id>
# Shows what blocks this task and what this task blocks

br list --status open
# Shows all open tasks, check dependencies in details
```
