---
purpose: Tech stack, constraints, and integrations for AI context injection
updated: 2026-02-01
---

# Tech Stack

This file is automatically injected into ALL AI prompts via `opencode.json` instructions[].

## Framework & Language

- **Framework:** [e.g., Next.js 15, React 19]
- **Language:** TypeScript (strict mode)
- **Runtime:** [e.g., Node.js 22, Bun 1.x]

## Styling & UI

- **CSS:** [e.g., Tailwind CSS v4]
- **Components:** [e.g., shadcn/ui, Radix Primitives]
- **Design System:** [e.g., Custom tokens in tailwind.config.ts]

## Data & State

- **Database:** [e.g., PostgreSQL via Supabase]
- **ORM:** [e.g., Drizzle, Prisma]
- **State Management:** [e.g., Zustand, React Query]
- **API Style:** [e.g., REST, tRPC, GraphQL]

## Testing

- **Unit Tests:** [e.g., Vitest]
- **E2E Tests:** [e.g., Playwright]
- **Coverage Target:** [e.g., 80%]

## Key Constraints

- [Constraint 1: e.g., Must work offline]
- [Constraint 2: e.g., WCAG 2.1 AA compliance required]
- [Constraint 3: e.g., Bundle size < 500KB]

## Active Integrations

- [Service 1: e.g., Stripe for payments]
- [Service 2: e.g., Resend for email]
- [Service 3: e.g., Sentry for error tracking]

## Context Budget Guidelines

**Quality Degradation Rule:** Target ~50% context per plan execution for consistent quality.

| Task Complexity | Max Tasks/Plan | Typical Context Usage |
| --------------- | -------------- | --------------------- |
| Simple (CRUD)   | 3              | ~30-45%               |
| Complex (auth)  | 2              | ~40-50%               |
| Very complex    | 1-2            | ~30-50%               |

**Split Signals:**

- More than 3 tasks → Create child plans
- Multiple subsystems → Separate plans
- > 5 file modifications per task → Split
- Discovery + implementation → Split

## Verification Commands

**Always run before claiming complete:**

```bash
# Type checking
[typecheck command, e.g., npm run typecheck]

# Linting
[lint command, e.g., npm run lint]

# Testing
[test command, e.g., npm test]

# Building
[build command, e.g., npm run build]
```

---

_Update this file when tech stack or constraints change._
_AI will capture architecture, conventions, and gotchas via the `observation` tool as it works._
