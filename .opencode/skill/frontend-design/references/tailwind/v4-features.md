# Tailwind CSS v4 New Features

v4/v4.1 additions: gradients, 3D transforms, masks, text shadows, new variants.

## Container Queries (Built-in)

No plugin needed:
```html
<div class="@container">
  <div class="grid grid-cols-1 @sm:grid-cols-2 @lg:grid-cols-4">
</div>

<!-- Max-width -->
<div class="grid-cols-3 @max-md:grid-cols-1">

<!-- Range -->
<div class="@min-md:@max-xl:hidden">
```

## Gradients

```html
<!-- Angle-based -->
<div class="bg-linear-45 from-indigo-500 to-pink-500">

<!-- OKLCH interpolation -->
<div class="bg-linear-to-r/oklch from-indigo-500 to-teal-400">

<!-- Conic and radial -->
<div class="bg-conic from-red-500 to-red-500">
<div class="bg-radial from-white to-zinc-900">
```

## 3D Transforms

```html
<div class="perspective-distant">
  <div class="rotate-x-45 rotate-z-30 transform-3d">
</div>
```

## @starting-style (Enter Transitions)

```html
<div popover class="transition-all starting:open:opacity-0 starting:open:scale-95">
```

## not-* Variant

```html
<div class="not-hover:opacity-75">
<div class="not-supports-backdrop-blur:bg-white">
```

## Text Shadows (v4.1)

```html
<p class="text-shadow-sm">Small</p>
<p class="text-shadow-lg">Large</p>
<p class="text-shadow-lg text-shadow-blue-500/50">Colored</p>
```

## Masks (v4.1)

```html
<div class="mask-t-from-50%">Fade from top</div>
<div class="mask-b-from-20% mask-b-to-80%">Bottom fade</div>
<div class="mask-radial-from-70%">Radial</div>
<div class="mask-b-from-50% mask-radial-from-80%">Combined</div>
```

## Other v4.1 Utilities

```html
<!-- Colored drop shadows -->
<svg class="drop-shadow-xl drop-shadow-cyan-500/50">

<!-- Overflow wrap -->
<p class="wrap-break-word">Break words</p>
<p class="wrap-anywhere">Break anywhere</p>

<!-- Safe alignment -->
<div class="flex justify-center-safe">

<!-- Baseline alignment -->
<div class="items-baseline-last">

<!-- Color scheme -->
<html class="color-scheme-dark">

<!-- Field sizing -->
<textarea class="field-sizing-content">

<!-- Inert styling -->
<div class="inert:opacity-50" inert>
```

## New v4.1 Variants

```html
<!-- Pointer device -->
<div class="pointer-fine:p-2 pointer-coarse:p-4">

<!-- Form validation (after interaction) -->
<input class="user-valid:border-green-500 user-invalid:border-red-500">

<!-- Details content -->
<details class="details-content:mt-3">

<!-- Inverted colors -->
<div class="inverted-colors:shadow-none">

<!-- Noscript -->
<div class="noscript:block hidden">Enable JS</div>
```

## Source Directives (v4.1)

```css
/* Ignore paths */
@source not "./src/legacy";

/* Safelist utilities */
@source inline("underline");

/* Brace expansion */
@source inline("{hover:,}bg-red-{100..900..100}");
```
