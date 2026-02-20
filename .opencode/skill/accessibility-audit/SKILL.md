---
name: accessibility-audit
description: Use when auditing UI components or pages for accessibility compliance, checking WCAG conformance, identifying keyboard navigation issues, color contrast problems, and pre-launch accessibility verification
---

# Accessibility Audit Skill

Audit UI accessibility against WCAG 2.1/2.2 guidelines.

## When to Use

- Reviewing UI components for accessibility compliance
- Auditing pages for WCAG conformance
- Identifying keyboard navigation issues
- Checking color contrast
- Pre-launch accessibility verification

## Core Workflow

### Phase 1: Visual Accessibility Analysis

```
Perform a comprehensive accessibility audit:

1. COLOR CONTRAST
   - Check text/background contrast ratios
   - WCAG AA: 4.5:1 normal text, 3:1 large text
   - Identify failing elements

2. VISUAL HIERARCHY
   - Heading structure (logical H1-H6)
   - Visual grouping of related elements
   - Touch targets (44x44px minimum)

3. CONTENT ACCESSIBILITY
   - Images needing alt text
   - Icons without text labels
   - Color-only information

4. INTERACTIVE ELEMENTS
   - Buttons/links with unclear purpose
   - Form fields without labels
   - Missing error states

5. MOTION
   - Auto-playing content
   - Potential vestibular triggers

Provide WCAG criterion references for each issue.
```

### Phase 2: Component Checklist

For each interactive component:

```markdown
## Component: [Name]

### Keyboard Navigation

- [ ] Focusable with Tab
- [ ] Visible focus indicator
- [ ] Operable with Enter/Space
- [ ] Escape closes modals
- [ ] Arrow keys for menus

### Screen Reader

- [ ] Meaningful accessible name
- [ ] Role announced correctly
- [ ] State changes announced
- [ ] Errors associated with inputs

### Visual

- [ ] 4.5:1 contrast ratio (text)
- [ ] 3:1 contrast ratio (UI)
- [ ] 44x44px touch targets
- [ ] No color-only information

### Motion

- [ ] Respects prefers-reduced-motion
- [ ] No auto-play >5 seconds
```

## WCAG Quick Reference

### Level A (Minimum)

| Criterion | Description            | Fix               |
| --------- | ---------------------- | ----------------- |
| 1.1.1     | Non-text Content       | Add alt text      |
| 1.3.1     | Info and Relationships | Use semantic HTML |
| 2.1.1     | Keyboard               | All via keyboard  |
| 2.4.1     | Bypass Blocks          | Skip links        |
| 4.1.2     | Name, Role, Value      | ARIA labels       |

### Level AA (Recommended)

| Criterion | Description   | Fix                    |
| --------- | ------------- | ---------------------- |
| 1.4.3     | Contrast      | 4.5:1 text, 3:1 UI     |
| 1.4.4     | Resize Text   | Support 200% zoom      |
| 2.4.6     | Headings      | Descriptive headings   |
| 2.4.7     | Focus Visible | Clear focus indicators |

## Common Fixes

### Accessible Button

```tsx
// Bad
<div onClick={handleClick}>Click me</div>

// Good
<button type="button" onClick={handleClick}>
  Click me
</button>
```

### Accessible Icon Button

```tsx
// Bad
<button><Icon /></button>

// Good
<button aria-label="Close dialog">
  <Icon aria-hidden="true" />
</button>
```

### Form with Error

```tsx
<label htmlFor="email">Email</label>
<input
  id="email"
  aria-describedby="email-error"
  aria-invalid={hasError}
/>
{hasError && (
  <span id="email-error" role="alert">
    Please enter a valid email
  </span>
)}
```

## Report Template

```markdown
# Accessibility Audit Report

**Date:** [Date]
**Page:** [Name]
**WCAG Level:** AA

## Summary

- Critical Issues: X
- Major Issues: X
- Minor Issues: X

## Issues

### [Issue Title]

- **Severity:** Critical/Major/Minor
- **WCAG:** [X.X.X]
- **Element:** [selector]
- **Issue:** [Description]
- **Fix:** [Recommendation]
```

## Storage

Save audit reports to `.opencode/memory/design/accessibility/`

## Related Skills

| Need           | Skill                 |
| -------------- | --------------------- |
| Design quality | `frontend-design` |
| UI research    | `ui-ux-research`      |
