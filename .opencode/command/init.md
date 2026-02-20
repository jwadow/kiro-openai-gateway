---
description: Initialize core project setup (AGENTS.md + tech-stack detection only)
argument-hint: "[--deep]"
agent: build
---

# Init: $ARGUMENTS

Core project setup. Creates AGENTS.md and detects tech stack. Run once per project.

> **Next steps:** `/init-user` for personalization, `/init-context` for GSD planning workflow

## Load Skills

```typescript
skill({ name: "index-knowledge" });
```

## Options

| Argument | Default | Description                               |
| -------- | ------- | ----------------------------------------- |
| `--deep` | false   | Comprehensive research (~100+ tool calls) |

## Phase 1: Detect Project

Detect and validate:

- Package manager and dependencies (with versions)
- Build, test, lint, dev commands — **validate each actually works**
- CI/CD configuration
- Existing AI rules (`.cursor/rules/`, `.cursorrules`, `.github/copilot-instructions.md`)
- Top-level directory structure

With `--deep`: Also analyze git history, source patterns, subsystem candidates.

## Phase 2: Preview Detection

After detecting project, show summary and ask for confirmation:

```typescript
question({
  questions: [
    {
      header: "Preview",
      question: `Detected: ${detectedTechStack}. Create AGENTS.md?`,
      options: [
        { label: "Yes, create it (Recommended)" },
        { label: "Show me what you'll write first" },
        { label: "Cancel" },
      ],
    },
  ],
});
```

**If "Show me":** Display detected values without writing files, then ask again.

## Phase 3: Create AGENTS.md

Create `./AGENTS.md` — **target <60 lines** (max 150). Follow the `index-knowledge` skill format:

- Tech stack with versions
- File structure
- Commands (validated)
- Code example from actual codebase (5-10 lines)
- Testing conventions
- Boundaries (always/ask-first/never)
- Gotchas

**Principles**: Examples > explanations. Pointers > copies. If AGENTS.md exists, improve it — don't overwrite blindly.

## Phase 4: Create tech-stack.md

From template `.opencode/memory/_templates/tech-stack.md`:

```bash
cp .opencode/memory/_templates/tech-stack.md .opencode/memory/project/tech-stack.md
```

Fill detected values:

- Framework, language, runtime
- Styling, components, design system
- Database, ORM, state management
- Testing tools
- Verification commands

## Phase 5: Subsystems (--deep only)

Identify candidates for nested AGENTS.md:

- `packages/*/` in monorepos
- `frontend/` vs `backend/` directories
- Significantly different subsystem patterns

Ask user before creating nested files.

## Phase 6: Verify and Report

Verify:

- [ ] AGENTS.md is <60 lines (or justified)
- [ ] Commands validated and work
- [ ] Boundaries include Never rules
- [ ] Code example from actual codebase
- [ ] tech-stack.md created

Output:

1. Files created (with line counts)
2. Tech stack detected
3. Commands validated (yes/no)
4. Suggested next steps:
   - `/init-user` — Create user profile
   - `/init-context` — Set up GSD planning workflow
   - `/review-codebase` — Deep codebase analysis
