# Tailwind CSS v4 Configuration

v4.1.x (current: v4.1.18) - CSS-first config, no tailwind.config.js needed.

## Installation

### Vite (Recommended)
```bash
npm i tailwindcss @tailwindcss/vite
```

```ts
// vite.config.ts
import tailwindcss from "@tailwindcss/vite"
export default { plugins: [tailwindcss()] }
```

```css
/* src/index.css */
@import "tailwindcss";
```

### PostCSS
```bash
npm i tailwindcss @tailwindcss/postcss
```

```js
// postcss.config.js
export default { plugins: ["@tailwindcss/postcss"] }
```

## CSS-First Configuration

Configure in CSS with `@theme`:

```css
@import "tailwindcss";

@theme {
  /* OKLCH colors for vivid, wide-gamut */
  --color-brand-50: oklch(0.97 0.02 264);
  --color-brand-500: oklch(0.55 0.22 264);
  --color-brand-900: oklch(0.25 0.15 264);

  /* Fonts */
  --font-display: "Satoshi", sans-serif;
  --font-body: "Inter", system-ui, sans-serif;

  /* Spacing, breakpoints, easing */
  --spacing-18: calc(var(--spacing) * 18);
  --breakpoint-3xl: 1920px;
  --ease-fluid: cubic-bezier(0.3, 0, 0, 1);

  /* Shadows */
  --shadow-glow: 0 0 20px oklch(0.55 0.22 264 / 0.3);
}
```

Usage: `<div class="bg-brand-500 font-display shadow-glow">`

## Key v4 Changes from v3

| v3 | v4 |
|----|-----|
| `@tailwind base/components/utilities` | `@import "tailwindcss"` |
| `tailwind.config.js` | `@theme` directive |
| `content: [...]` array | Automatic detection |
| sRGB colors | OKLCH/P3 colors |
| `bg-opacity-50` | `bg-black/50` modifier |
| Plugin for container queries | Built-in `@container` |

## Automatic Content Detection

No `content` array. Auto-ignores `.gitignore` and binary files.

Add sources manually if needed:
```css
@source "../node_modules/@my-company/ui-lib";
```

## Dynamic Values

Any value works without config:
```html
<div class="grid grid-cols-15">
<div class="mt-17 px-29">
<div data-active class="data-active:bg-blue-500">
```

## OKLCH Colors

Wider gamut, more vivid:
```css
@theme {
  --color-primary-50: oklch(0.98 0.02 250);
  --color-primary-500: oklch(0.65 0.22 250);
  --color-primary-900: oklch(0.25 0.15 250);
}
```

Opacity modifier: `<div class="bg-primary-500/50">`

## Custom Utilities & Variants

```css
@utility glass {
  background: oklch(1 0 0 / 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid oklch(1 0 0 / 0.2);
}

@custom-variant theme-dark (&:where([data-theme="dark"] *));
```

## Layer Organization

```css
@layer base { h1 { @apply text-4xl font-bold; } }
@layer components { .btn { @apply px-4 py-2 rounded-lg; } }
@layer utilities { .text-balance { text-wrap: balance; } }
```

## Dark Mode

Class strategy by default:
```html
<html class="dark">
  <div class="bg-white dark:bg-zinc-900">
```

## Migration from v3

```bash
npx @tailwindcss/upgrade
```

- Move `tailwind.config.js` to `@theme`
- Replace `@tailwind` with `@import "tailwindcss"`
- Remove `content` array
- Replace `bg-opacity-*` with `/opacity` modifier

## Performance

- Full builds: 3.5x+ faster
- Incremental: 8x+ faster
- No-new-CSS: 100x+ faster (microseconds)
