---
purpose: Tech stack, constraints, and integrations for AI context injection
updated: 2026-02-02
---

# Tech Stack

This file is automatically injected into ALL AI prompts via `opencode.json` instructions[].

## Framework & Language

- **Framework:** CLI tool (cac for argument parsing)
- **Language:** TypeScript (ESNext, strict mode, bundler moduleResolution)
- **Runtime:** Bun >= 1.3.2

## Key Dependencies

- **CLI Framework:** cac (^6.7.14) - Command-line argument parsing
- **UI Prompts:** @clack/prompts (^0.7.0) - Interactive CLI prompts
- **TUI Framework:** @opentui/core (^0.1.72) + @opentui/solid (^0.1.72) - Terminal UI
- **Validation:** zod (^3.25.76) - Schema validation
- **Task Tracking:** beads-village (^1.3.3) - Git-backed task management
- **AI SDK:** @ai-sdk/provider (^3.0.6) - AI provider integration

## Build & Tools

- **Build:** `bun run build.ts` + rsync for template bundling
- **Lint:** oxlint (^1.38.0) - Fast JavaScript/TypeScript linter
- **Format:** oxfmt (^0.23.0) - Code formatter
- **TypeCheck:** TypeScript 5.9.3

## Testing

- **Unit Tests:** bun test (native Bun test runner)
- **Test Location:** src/\*_/_.test.ts (colocated)
- **Run Single:** bun test src/commands/init.test.ts

## Key Constraints

- Must maintain Bun compatibility (engines.bun >= 1.3.2)
- Node.js not officially supported
- Build copies .opencode/ to dist/template/ - don't edit dist/ directly
- Keep .opencode/ structure minimal and focused

## Active Integrations

- **OpenCode AI:** @opencode-ai/plugin (^1.1.12) - OpenCode integration
- **Beads CLI:** beads_rust (br) - Task tracking CLI

---

_Update this file when tech stack or constraints change._
_AI will capture architecture, conventions, and gotchas via the `observation` tool as it works._
