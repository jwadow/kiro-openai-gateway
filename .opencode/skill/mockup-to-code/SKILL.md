---
name: mockup-to-code
description: Use when converting UI mockups, screenshots, Figma/Sketch designs, wireframes, or building component libraries from design systems into production-ready code
---

# Mockup to Code Skill

Convert UI mockups, screenshots, and designs into production-ready code.

## When to Use

- Converting Figma/Sketch mockups to React/Vue/HTML
- Implementing pixel-perfect designs
- Building component libraries from design systems
- Rapid prototyping from wireframes

## Core Workflow

### Phase 1: Design Analysis

```
Analyze this UI mockup and extract:

1. LAYOUT STRUCTURE
   - Grid system (columns, gutters, margins)
   - Component hierarchy
   - Container widths

2. VISUAL SPECIFICATIONS
   - Colors (hex values)
   - Typography (sizes, weights)
   - Spacing (padding, margins, gaps)
   - Border radius, shadows

3. COMPONENTS IDENTIFIED
   - List each distinct component
   - Note variations
   - Identify reusable patterns

4. RESPONSIVE CONSIDERATIONS
   - How might this adapt to mobile?
   - Collapsible sections
   - Priority content

Output as structured JSON.
```

### Phase 2: Component Breakdown

```markdown
## Component: [Name]

**Priority:** High/Medium/Low
**Complexity:** Simple/Medium/Complex
**Reusability:** One-off/Reusable/Design System

**Props Interface:**

- variant: 'primary' | 'secondary'
- size: 'sm' | 'md' | 'lg'
- disabled?: boolean

**Accessibility:**

- Keyboard navigation
- ARIA labels
- Focus management
```

### Phase 3: Implementation

Implement with comparison loop:

```
Compare mockup vs implementation:

1. What differences do you see?
2. What's missing?
3. Spacing/sizing adjustments needed?
4. Color accuracy?
5. Typography match?

Prioritize fixes by visual impact.
```

## Technology Patterns

### React + Tailwind

```
Convert to React with Tailwind CSS.

Requirements:
- Functional components with TypeScript
- Tailwind utility classes
- Extract repeated patterns
- Semantic HTML
- Responsive classes (sm:, md:, lg:)
```

### Vue 3

```
Convert to Vue 3 component.

Requirements:
- Composition API with <script setup>
- Scoped styles
- Props with TypeScript
```

### Plain HTML/CSS

```
Convert to semantic HTML and CSS.

Requirements:
- Semantic HTML5 elements
- CSS Grid/Flexbox layout
- CSS custom properties
```

## Quality Checklist

### Visual Fidelity

- [ ] Colors match exactly
- [ ] Typography matches
- [ ] Spacing is consistent
- [ ] Border radius matches
- [ ] Shadows correct

### Responsiveness

- [ ] Desktop layout matches
- [ ] Tablet works
- [ ] Mobile is usable
- [ ] No horizontal scroll

### Interactions

- [ ] Hover states
- [ ] Focus states
- [ ] Transitions smooth

### Code Quality

- [ ] Properly typed
- [ ] Sensible defaults
- [ ] Uses tokens (no hardcoded values)
- [ ] Accessible markup

## Storage

Save implementations to `.opencode/memory/design/implementations/`

## Related Skills

| Need              | Skill                 |
| ----------------- | --------------------- |
| Aesthetic quality | `frontend-design` |
| Accessibility     | `accessibility-audit` |
| Design tokens     | `design-system-audit` |
