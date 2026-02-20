# shadcn/ui Accessibility

ARIA patterns, keyboard navigation, screen reader support via Radix UI.

## Radix Foundation

Built-in: keyboard navigation, screen reader announcements, focus management, ARIA automatic.

## Keyboard Navigation

### Focus Management
```tsx
<Button className="focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">

<!-- Skip link -->
<a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2">
  Skip to content
</a>
```

### Dialog
Focus trapped automatically. Esc closes, Tab cycles.

### Dropdown/Menu
- Space/Enter: Open
- Arrow Up/Down: Navigate
- Esc: Close
- Tab: Close and move focus

## Screen Reader

### ARIA Labels
```tsx
<Button aria-label="Close dialog"><X /></Button>
<Input aria-label="Email address" type="email" />

<Button aria-describedby="delete-desc">Delete</Button>
<p id="delete-desc" className="sr-only">Permanently deletes account</p>
```

### Screen Reader Only
```tsx
<Button>
  <Trash className="h-4 w-4" />
  <span className="sr-only">Delete item</span>
</Button>
```

### Live Regions
```tsx
<div aria-live="polite">{message}</div>
<div aria-live="assertive">{error}</div>
```

## Forms

### Labels
```tsx
<Label htmlFor="email">Email</Label>
<Input id="email" type="email" />
```

### Validation
```tsx
<Input aria-invalid={!!error} aria-describedby={error ? "email-error" : undefined} />
<FormMessage id="email-error" />
```

### Required Fields
```tsx
<Label htmlFor="name">
  Name <span className="text-destructive">*</span>
  <span className="sr-only">(required)</span>
</Label>
```

### Fieldset
```tsx
<fieldset>
  <legend className="text-lg font-semibold mb-4">Contact Info</legend>
  <FormField name="email" />
</fieldset>
```

## Color Contrast

WCAG AA: 4.5:1 normal text, 3:1 large text.

```tsx
// Good
<p className="text-foreground">Primary</p>
<p className="text-muted-foreground">Secondary</p>

// Avoid
<p className="text-gray-400">Hard to read</p>
```

## Focus Indicators

Always visible:
```tsx
<Button className="focus-visible:ring-2 focus-visible:ring-ring">

// Never: focus:outline-none without replacement
// Use focus-visible instead
```

## Motion Preferences

```css
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
```

```tsx
<div className="transition-all motion-reduce:transition-none">
```

## Checklist

- [ ] All interactive elements keyboard accessible
- [ ] Focus indicators visible
- [ ] Screen reader announces correctly
- [ ] Form errors announced
- [ ] Color contrast WCAG AA
- [ ] Semantic HTML
- [ ] ARIA labels for icon buttons
- [ ] Modal focus trap works
- [ ] Respects reduced motion
- [ ] Works at 200% zoom
- [ ] Skip links provided
