# Tailwind Responsive Design

Mobile-first breakpoints, container queries.

## Mobile-First

Base styles apply to all. Breakpoint prefixes override at larger sizes.
```html
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
```

## Breakpoints

| Prefix | Min Width |
|--------|-----------|
| `sm:` | 640px |
| `md:` | 768px |
| `lg:` | 1024px |
| `xl:` | 1280px |
| `2xl:` | 1536px |

Custom (v4):
```css
@theme {
  --breakpoint-3xl: 1920px;
}
```

## Common Patterns

```html
<!-- Stack to row -->
<div class="flex flex-col lg:flex-row gap-4">

<!-- Grid columns -->
<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3">

<!-- Visibility -->
<div class="hidden lg:block">Desktop only</div>
<div class="block lg:hidden">Mobile only</div>

<!-- Typography -->
<h1 class="text-2xl md:text-4xl lg:text-6xl">

<!-- Spacing -->
<div class="p-4 md:p-6 lg:p-8">

<!-- Width -->
<div class="w-full lg:w-1/2 xl:w-1/3">
```

## Layout Examples

### Sidebar
```html
<div class="flex flex-col lg:flex-row min-h-screen">
  <aside class="w-full lg:w-64 bg-gray-100 p-4">Sidebar</aside>
  <main class="flex-1 p-4 md:p-8">Main</main>
</div>
```

### Card Grid
```html
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
  <div class="bg-white rounded-lg shadow p-6">Card</div>
</div>
```

### Navigation
```html
<nav class="flex items-center justify-between h-16">
  <div class="text-xl font-bold">Logo</div>
  <div class="hidden md:flex gap-6">Links</div>
  <button class="md:hidden">Menu</button>
</nav>
```

## Max-Width Queries

```html
<div class="max-lg:text-center">Below lg</div>
<div class="max-sm:hidden">Below sm</div>
```

## Container Queries (v4)

Style based on container, not viewport:
```html
<div class="@container">
  <div class="grid grid-cols-1 @sm:grid-cols-2 @lg:grid-cols-4">
</div>
```

Breakpoints: `@sm:`, `@md:`, `@lg:`, `@xl:`, `@2xl:`

Max-width: `@max-md:grid-cols-1`
Range: `@min-md:@max-xl:hidden`

## Responsive + State

```html
<button class="lg:hover:scale-105">
<a class="hover:text-blue-600 lg:hover:text-purple-600">
```

## Best Practices

1. Mobile-first: start mobile, add complexity larger
2. Consistent breakpoints across related elements
3. Test at exact breakpoint widths
4. 2-3 breakpoints per element max
5. Verify touch targets min 44x44px
