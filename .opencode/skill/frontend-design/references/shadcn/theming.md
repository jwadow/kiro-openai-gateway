# shadcn/ui Theming

CSS variables, OKLCH colors, dark mode for Tailwind v4.

## CSS Variables

```css
@import "tailwindcss";

@theme {
  --color-background: oklch(1 0 0);
  --color-foreground: oklch(0.15 0.02 264);
  
  --color-primary: oklch(0.55 0.22 264);
  --color-primary-foreground: oklch(0.98 0.01 264);
  
  --color-secondary: oklch(0.96 0.01 264);
  --color-secondary-foreground: oklch(0.15 0.02 264);
  
  --color-muted: oklch(0.96 0.01 264);
  --color-muted-foreground: oklch(0.55 0.02 264);
  
  --color-destructive: oklch(0.55 0.22 25);
  --color-border: oklch(0.90 0.01 264);
  --color-ring: oklch(0.55 0.22 264);
  
  --radius: 0.5rem;
}
```

## OKLCH Format

```
oklch(L C H)
     │ │ └─ Hue (0-360)
     │ └─── Chroma (0-0.4)
     └───── Lightness (0-1)
```

Benefits: perceptually uniform, wider P3 gamut, better gradients.

```css
--color-brand-50: oklch(0.98 0.02 250);
--color-brand-500: oklch(0.65 0.22 250);
--color-brand-900: oklch(0.25 0.15 250);
```

## Dark Mode Setup

```bash
npm install next-themes
```

```tsx
// components/theme-provider.tsx
"use client"
import { ThemeProvider as NextThemesProvider } from "next-themes"

export function ThemeProvider({ children, ...props }) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}

// app/layout.tsx
<ThemeProvider attribute="class" defaultTheme="system" enableSystem>
  {children}
</ThemeProvider>
```

## Theme Toggle

```tsx
import { useTheme } from "next-themes"

export function ThemeToggle() {
  const { setTheme, theme } = useTheme()
  return (
    <Button variant="ghost" size="icon" onClick={() => setTheme(theme === "light" ? "dark" : "light")}>
      <Sun className="h-5 w-5 dark:hidden" />
      <Moon className="h-5 w-5 hidden dark:block" />
    </Button>
  )
}
```

## Dark Mode Colors

```css
.dark {
  --color-background: oklch(0.15 0.02 264);
  --color-foreground: oklch(0.98 0.01 264);
  --color-primary: oklch(0.75 0.18 264);
  --color-muted: oklch(0.25 0.02 264);
  --color-border: oklch(0.30 0.02 264);
}
```

## Multiple Themes

```css
[data-theme="violet"] { --color-primary: oklch(0.55 0.25 290); }
[data-theme="rose"] { --color-primary: oklch(0.60 0.22 350); }
```

```tsx
<div data-theme="violet"><Button>Violet</Button></div>
```

## Custom Button Variants

```tsx
const buttonVariants = cva("...", {
  variants: {
    variant: {
      gradient: "bg-gradient-to-r from-violet-500 to-pink-500 text-white",
      glass: "bg-white/10 backdrop-blur-md border border-white/20",
    },
    size: {
      xl: "h-14 rounded-lg px-10 text-lg",
    },
  },
})
```

## Radius

```css
@theme {
  --radius: 0.5rem;    /* Default */
  /* --radius: 0rem;   /* Sharp */
  /* --radius: 1rem;   /* Rounded */
}
```

Components use: `rounded-lg` (--radius), `rounded-md` (--radius - 2px).

## Typography

```css
@theme {
  --font-sans: "Inter", system-ui, sans-serif;
  --font-display: "Playfair Display", serif;
  --font-mono: "JetBrains Mono", monospace;
}
```

## Best Practices

1. Use CSS variables for runtime switching
2. OKLCH for gradients and accessibility
3. Semantic naming (primary, not blue)
4. Test both themes
5. Maintain WCAG AA contrast (4.5:1)
