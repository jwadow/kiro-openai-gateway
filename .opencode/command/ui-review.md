---
description: Review UI/UX design for quality, aesthetics, and best practices
argument-hint: "<image-or-component-path> [--responsive] [--dark-mode]"
agent: vision
model: proxypal/gemini-3-pro-preview
---

# UI Review: $ARGUMENTS

## Load Skills

```typescript
skill({ name: "visual-analysis" }); // Analysis framework
skill({ name: "accessibility-audit" }); // WCAG checklists
skill({ name: "frontend-design" }); // Anti-patterns, design quality
```

## Input

Parse `$ARGUMENTS`:

- **Path** (required): Image, screenshot, or component file
- **`--responsive`**: Include responsive breakpoint review
- **`--dark-mode`**: Include dark mode review

## Review Workflow

### 1. Analyze the Input

Use the `visual-analysis` skill to perform deep analysis:

- Content inventory (elements, text, icons)
- Visual properties (colors, typography, spacing, layout)
- Design patterns and potential issues

### 2. Score Categories

Rate each 1-10 with brief justification:

| Category               | What to Evaluate                                               |
| ---------------------- | -------------------------------------------------------------- |
| **Typography**         | Hierarchy, readability, weight contrast, intentional choices   |
| **Color**              | Palette cohesion, contrast, semantic usage, no AI slop         |
| **Layout & Spacing**   | Visual hierarchy, consistency, alignment, white space          |
| **Interactive States** | Hover, focus, active, disabled, loading coverage               |
| **Accessibility**      | WCAG AA compliance (use `accessibility-audit` skill checklist) |
| **Visual Polish**      | Consistency, attention to detail, motion, shadows, icons       |

### 3. Conditional Reviews

**If `--responsive`**: Check at 375px, 768px, 1280px, 1536px+. Flag touch targets, horizontal scroll, text sizing.

**If `--dark-mode`**: Check contrast on dark backgrounds, adapted colors (not just inverted), shadow adjustments, focus visibility.

### 4. Report Findings

Group by severity:

- **Critical (Must Fix)**: Accessibility failures, broken interactions
- **Warning (Should Fix)**: AI slop patterns, inconsistent spacing, missing states
- **Info (Nice to Have)**: Polish opportunities

For each finding: location, impact, and recommended fix.

## Output

Deliver:

1. Category scores (1-10 each) with justification
2. Overall assessment (1-2 sentences)
3. Findings grouped by severity with actionable fixes
4. Code fixes for critical issues (if reviewing component code)

## Record Findings

```typescript
observation({
  type: "warning",
  title: "UI: [Component] [issue type]",
  narrative: "Found [issue] in [location]. Impact: [description]...",
  concepts: "ui, accessibility, [category]",
  confidence: "high",
});
```

## Related Commands

| Need                 | Command   |
| -------------------- | --------- |
| Design from scratch  | `/design` |
| Start implementation | `/start`  |
| Ship implementation  | `/ship`   |
