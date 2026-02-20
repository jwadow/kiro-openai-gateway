---
description: UI/UX visual design with aesthetic direction and code output
argument-hint: "<component|page|system> [topic] [--quick]"
agent: vision
---

# Design: $ARGUMENTS

Design a component, page, or design system with a clear aesthetic point of view.

> **Design track (optional):** Not part of the core `/create → /start → /ship` workflow.
> Use when you need visual design guidance before or during implementation.

## Parse Arguments

| Argument    | Default  | Description                                 |
| ----------- | -------- | ------------------------------------------- |
| `component` | —        | Design a specific component                 |
| `page`      | —        | Design a page layout                        |
| `system`    | —        | Create or extend a design system            |
| `[topic]`   | required | What to design (e.g. "button", "dashboard") |
| `--quick`   | false    | High-level direction only, skip code        |

## Load Skills

```typescript
skill({ name: "frontend-design" }); // Design system guidance, anti-patterns, references
```

---

## Phase 1: Detect Existing Design System

```typescript
glob({ pattern: "**/tailwind.config.{js,ts,mjs}" });
glob({ pattern: "**/globals.css" });
glob({ pattern: "**/components.json" }); // shadcn
```

Read what exists. Don't design in a vacuum — build on the project's current system.

---

## Phase 2: Check Memory

```typescript
memory_search({ query: "[topic] design UI", limit: 3 });
memory_search({ query: "design system colors typography", limit: 3 });
```

Reuse existing aesthetic decisions. Don't contradict previous design choices unless the user asks.

---

## Phase 3: Design

The `frontend-design` skill provides all reference material:

- Aesthetic directions and design philosophy
- Typography and font pairing guidance
- Color systems (OKLCH)
- Animation patterns (Motion + Tailwind)
- Anti-patterns and AI slop avoidance
- shadcn/ui component patterns
- Tailwind v4 configuration

**Before designing, state:**

1. **Aesthetic direction** — which style and why
2. **Key characteristics** — 3 specific elements you'll apply

Then produce the design:

| Task Type   | Output                                |
| ----------- | ------------------------------------- |
| `component` | Spec (variants, sizes, states) + code |
| `page`      | Layout structure + section breakdown  |
| `system`    | Tokens (CSS variables) + guidelines   |

For `--quick`: Skip code output. Provide direction + key decisions only.

---

## Phase 4: Record Decision

```typescript
observation({
  type: "decision",
  title: "Design: [topic]",
  narrative: "Chose [direction] because [rationale]. Key tokens: [colors, fonts].",
  concepts: "design, ui, [topic]",
  confidence: "high",
});
```

---

## Examples

```bash
/design component button           # Full component design with code
/design page landing --quick       # High-level page direction only
/design system                     # Create/extend design system tokens
```

## Related Commands

| Need               | Command         |
| ------------------ | --------------- |
| Review existing UI | `/ui-review`    |
| Start building     | `/start <bead>` |
| Ship it            | `/ship <bead>`  |
