---
name: context-initialization
description: Initialize GSD-style project context files from templates
---

# Context Initialization

Create project.md, roadmap.md, and state.md from templates with user input.

## Process

### 1. Verify Templates

```bash
test -f .opencode/memory/_templates/project.md
test -f .opencode/memory/_templates/roadmap.md
test -f .opencode/memory/_templates/state.md
```

Stop if missing.

### 2. Gather Input

Ask 5 questions:

1. Project vision
2. Success criteria
3. Target users
4. Phases
5. Current phase

Skip if `--skip-questions` flag set.

### 3. Create Files

**project.md**

- Read template
- Fill with answers
- Write to `.opencode/memory/project/`

**roadmap.md**

- Read template
- Parse phases into table
- Write to `.opencode/memory/project/`

**state.md**

- Read template
- Set initial state
- Write to `.opencode/memory/project/`

### 4. Verify

```bash
ls .opencode/memory/project/
```

Report created files.
