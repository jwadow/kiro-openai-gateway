---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces. Use when building web components, pages, or applications with React-based frameworks. Includes Tailwind CSS v4, shadcn/ui components, Motion animations, and visual design philosophy for avoiding generic AI aesthetics.
---

# Frontend Design

Create distinctive, production-grade interfaces avoiding generic "AI slop" aesthetics.

## When to Use

- Building UI with React frameworks (Next.js, Vite, Remix)
- Creating visually distinctive, memorable interfaces
- Implementing accessible components with shadcn/ui
- Styling with Tailwind CSS v4
- Adding animations and micro-interactions
- Creating visual designs, posters, brand materials

## Reference Documentation

### Tailwind CSS v4.1

- `./references/tailwind/v4-config.md` - Installation, @theme, CSS-first config
- `./references/tailwind/v4-features.md` - Container queries, gradients, masks, text shadows
- `./references/tailwind/utilities-layout.md` - Display, flex, grid, position
- `./references/tailwind/utilities-styling.md` - Spacing, typography, colors, borders
- `./references/tailwind/responsive.md` - Breakpoints, mobile-first, container queries

Search: `@theme`, `@container`, `OKLCH`, `mask-`, `text-shadow`

### shadcn/ui (CLI v3.6)

- `./references/shadcn/setup.md` - Installation, visual styles, component list
- `./references/shadcn/core-components.md` - Button, Card, Dialog, Select, Tabs, Toast
- `./references/shadcn/form-components.md` - Form, Field, Input Group, 2026 components
- `./references/shadcn/theming.md` - CSS variables, OKLCH, dark mode
- `./references/shadcn/accessibility.md` - ARIA, keyboard, screen reader

Search: `Field`, `InputGroup`, `Spinner`, `ButtonGroup`, `next-themes`

### Animation (Motion + Tailwind)

- `./references/animation/motion-core.md` - Core API, variants, gestures, layout animations
- `./references/animation/motion-advanced.md` - AnimatePresence, scroll, orchestration, TypeScript

**Stack**:
| Animation Type | Tool |
|----------------|------|
| Hover/transitions | Tailwind CSS (`transition-*`) |
| shadcn states | `tailwindcss-animate` (built-in) |
| Gestures/layout/exit | Motion (`motion/react`) |
| Complex SVG morphing | anime.js v4 (niche only) |

### Visual Design

- `./references/canvas/philosophy.md` - Design movements, core principles
- `./references/canvas/execution.md` - Multi-page systems, quality standards

For sophisticated compositions: posters, brand materials, design systems.

## Design Thinking

Before coding, commit to BOLD aesthetic direction:

- **Purpose**: What problem? Who uses it?
- **Tone**: Pick extreme - brutally minimal, maximalist chaos, retro-futuristic, organic, luxury, playful, editorial, brutalist, art deco, soft/pastel, industrial
- **Differentiation**: What makes this UNFORGETTABLE?

Bold maximalism and refined minimalism both work. Key is intentionality.

## Anti-Patterns (NEVER)

- Overused fonts: Inter, Roboto, Arial, system fonts, Space Grotesk
- Cliched colors: purple gradients on white
- Predictable layouts and component patterns
- Cookie-cutter design lacking character
- Generic AI-generated aesthetics

## Best Practices

1. **Accessibility First**: Radix primitives, focus states, semantic HTML
2. **Mobile-First**: Start mobile, layer responsive variants
3. **Design Tokens**: Use `@theme` for spacing, colors, typography
4. **Dark Mode**: Apply dark variants to all themed elements
5. **Performance**: Automatic CSS purging, avoid dynamic class names
6. **TypeScript**: Full type safety
7. **Expert Craftsmanship**: Every detail matters

## Core Stack Summary

**Tailwind v4.1**: CSS-first config via `@theme`. Single `@import "tailwindcss"`. OKLCH colors. Container queries built-in.

**shadcn/ui v3.6**: Copy-paste Radix components. Visual styles: Vega/Nova/Maia/Lyra/Mira. New: Field, InputGroup, Spinner, ButtonGroup.

**Motion**: `import { motion, AnimatePresence } from 'motion/react'`. Declarative React animations. Use `tailwindcss-animate` for shadcn states.

## Typography

Choose beautiful, unique fonts. Pair distinctive display with refined body:

```css
@theme {
  --font-display: "Playfair Display", serif;
  --font-body: "Source Sans 3", sans-serif;
}
```

## Color

Use OKLCH for vivid colors. Dominant colors with sharp accents:

```css
@theme {
  --color-primary-500: oklch(0.55 0.22 264);
  --color-accent: oklch(0.75 0.18 45);
}
```

## Motion

**Primary**: Motion for React animations. **Fallback**: CSS `@starting-style` for simple enter/exit.

```tsx
import { motion, AnimatePresence } from 'motion/react';

// Basic animation
<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} />

// Exit animations
<AnimatePresence>
  {show && <motion.div exit={{ opacity: 0 }} />}
</AnimatePresence>

// Layout animations
<motion.div layout />

// Gestures
<motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} />
```

CSS fallback (no JS):
```css
dialog[open] {
  opacity: 1;
  @starting-style { opacity: 0; transform: scale(0.95); }
}
```

## Spatial Composition

Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.

## Backgrounds

Create atmosphere: gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, grain overlays.
