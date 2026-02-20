---
name: design-system-audit
description: Use when auditing existing design systems for consistency, documenting undocumented design tokens, identifying design debt, preparing for design system refactoring, or comparing implementation vs design specs
---

# Design System Audit Skill

Audit, document, and improve design systems.

## When to Use

- Auditing existing design systems for consistency
- Documenting undocumented design tokens
- Identifying design debt
- Preparing for design system refactoring
- Comparing implementation vs design specs

## Core Workflow

### Phase 1: Visual Inventory

```
Analyze application screenshots and create a visual inventory:

1. COLOR PALETTE
   - Primary colors (brand)
   - Secondary colors
   - Neutral/gray scale
   - Semantic colors (success, warning, error, info)

2. TYPOGRAPHY SCALE
   - Heading sizes (H1-H6)
   - Body text sizes
   - Font families used
   - Font weights observed

3. SPACING PATTERNS
   - Common padding values
   - Common margin values
   - Gap patterns

4. COMPONENT VARIANTS
   - Button styles
   - Input field styles
   - Card variations

5. INCONSISTENCIES DETECTED
   - Similar but different colors
   - Inconsistent spacing
   - Typography variations

Output as structured JSON design tokens.
```

### Phase 2: Consistency Analysis

```
Compare visual inventory with code.

Identify:
1. Tokens used in code but not in designs
2. Visual patterns not codified as tokens
3. Naming inconsistencies
4. Redundant/duplicate values
5. Missing semantic tokens
```

## Design Token Structure

```json
{
  "color": {
    "primitive": {
      "blue": { "50": "#eff6ff", "500": "#3b82f6", "900": "#1e3a8a" }
    },
    "semantic": {
      "primary": "{color.primitive.blue.500}",
      "background": { "default": "#f9fafb", "muted": "#f3f4f6" },
      "text": { "default": "#111827", "muted": "#6b7280" }
    }
  },
  "spacing": { "1": "0.25rem", "2": "0.5rem", "4": "1rem", "8": "2rem" },
  "typography": {
    "fontFamily": { "sans": "Inter", "mono": "JetBrains Mono" },
    "fontSize": { "sm": "0.875rem", "base": "1rem", "lg": "1.125rem" }
  },
  "borderRadius": { "sm": "0.125rem", "md": "0.375rem", "lg": "0.5rem" }
}
```

## Audit Report Template

```markdown
# Design System Audit Report

**Date:** [Date]
**Application:** [Name]

## Summary

- Total unique colors: X (recommended: <20)
- Total spacing values: X (recommended: 8-12)
- Typography variants: X
- Consistency score: X/100

## Color Audit

| Category   | Count | Issues       |
| ---------- | ----- | ------------ |
| Primitives | X     | X duplicates |
| Semantics  | X     | X missing    |
| One-offs   | X     | Should be 0  |

### Recommendations

1. Consolidate similar colors
2. Add semantic tokens
3. Remove one-off colors

## Priority Actions

### High Priority

1. [Action with impact]

### Medium Priority

1. [Action]

### Low Priority (Design Debt)

1. [Action]
```

## Storage

Save audit reports to `.opencode/memory/design/audits/`
Save design tokens to `.opencode/memory/design/tokens/`

## Related Skills

| Need                 | Skill                 |
| -------------------- | --------------------- |
| Aesthetic principles | `frontend-design` |
| Implement components | `mockup-to-code`      |
| Accessibility        | `accessibility-audit` |
