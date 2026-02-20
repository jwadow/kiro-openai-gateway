---
purpose: Project vision, success criteria, and core principles
updated: 2026-02-12
---

# OpenCodeKit

## Vision

A project scaffolding tool that generates OpenCode-ready project templates.

OpenCodeKit (`ock`) enables developers to bootstrap AI-assisted development environments with all essential configurations, skills, commands, and integrations pre-configured and validated.

## Success Criteria

- [ ] Users can `ock init` and get a working OpenCode project in under 60 seconds
- [ ] Generated projects include all essential files (AGENTS.md, skills, commands, memory)
- [ ] 100% of generated templates pass validation (typecheck, lint)
- [ ] Templates are customizable through CLI prompts or config
- [ ] Integration with beads for task tracking works out-of-the-box

## Target Users

### Primary

- **Solo developers** setting up AI-assisted workflows for personal projects
- **Teams** standardizing their OpenCode configuration across multiple projects

### User Needs

- Quick setup without manual configuration
- Consistent, validated project structures
- Customizable templates for different use cases
- Integrated task tracking from day one

## Core Principles

1. **Convention over configuration** - Sensible defaults, minimal setup required
2. **Minimal but complete** - Include only essential files, no bloat
3. **Extensible** - Easy to add custom skills, commands, and templates
4. **Validated by default** - All generated projects pass typecheck and lint
5. **Git-backed** - All state and tracking integrated with git workflow

## Tech Stack

- **Runtime:** Bun >= 1.3.2
- **Language:** TypeScript (ESNext, strict mode)
- **Build:** `bun build` + rsync for template bundling
- **CLI Framework:** cac
- **UI Prompts:** @clack/prompts
- **Validation:** zod
- **Task Tracking:** beads_rust (br)

## Current Phase

**Scale** - Core complete, adding advanced features.

See [roadmap.md](./roadmap.md) for phase details and [state.md](./state.md) for current position.

## Architecture

```
src/
├── index.ts          # CLI entry point
├── commands/         # CLI commands (init, etc.)
├── utils/            # Shared utilities
└── validation/       # Validation scripts

dist/
├── index.js          # Built CLI
└── template/         # Bundled .opencode/ template

.opencode/
├── agent/            # Agent definitions
├── command/          # OpenCode commands
├── skill/            # Reusable skills
├── tool/             # Custom tools
└── memory/           # Project memory
```

## Key Files

| File          | Purpose                     |
| ------------- | --------------------------- |
| AGENTS.md     | Project rules for AI agents |
| package.json  | Dependencies and scripts    |
| build.ts      | Build configuration         |
| tsconfig.json | TypeScript configuration    |

---

_Update this file when vision, success criteria, or principles change._
