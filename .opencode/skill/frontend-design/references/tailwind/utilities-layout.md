# Tailwind Layout Utilities

Display, flexbox, grid, positioning, z-index.

## Display

```html
<div class="block">Block</div>
<div class="inline-block">Inline Block</div>
<div class="flex">Flexbox</div>
<div class="inline-flex">Inline Flex</div>
<div class="grid">Grid</div>
<div class="hidden">Hidden</div>
```

## Flexbox

```html
<!-- Direction -->
<div class="flex flex-row">Row</div>
<div class="flex flex-col">Column</div>
<div class="flex flex-row-reverse">Reverse</div>

<!-- Justify (main axis) -->
<div class="flex justify-start">Start</div>
<div class="flex justify-center">Center</div>
<div class="flex justify-end">End</div>
<div class="flex justify-between">Between</div>
<div class="flex justify-evenly">Evenly</div>

<!-- Align (cross axis) -->
<div class="flex items-start">Start</div>
<div class="flex items-center">Center</div>
<div class="flex items-end">End</div>
<div class="flex items-stretch">Stretch</div>

<!-- Gap -->
<div class="flex gap-4">All</div>
<div class="flex gap-x-6 gap-y-2">X/Y</div>

<!-- Wrap -->
<div class="flex flex-wrap">Wrap</div>
<div class="flex flex-nowrap">No wrap</div>
```

## Grid

```html
<!-- Columns (v4: any number) -->
<div class="grid grid-cols-1">1 col</div>
<div class="grid grid-cols-3">3 cols</div>
<div class="grid grid-cols-12">12 cols</div>
<div class="grid grid-cols-15">15 cols (v4)</div>

<!-- Custom grid -->
<div class="grid grid-cols-[1fr_500px_2fr]">Custom</div>

<!-- Span -->
<div class="col-span-2">Span 2</div>
<div class="row-span-3">Span 3 rows</div>

<!-- Gap -->
<div class="grid gap-4">All</div>
<div class="grid gap-x-8 gap-y-4">X/Y</div>
```

## Positioning

```html
<div class="static">Static</div>
<div class="relative">Relative</div>
<div class="absolute">Absolute</div>
<div class="fixed">Fixed</div>
<div class="sticky">Sticky</div>

<!-- Position values -->
<div class="absolute top-0 right-0">Top right</div>
<div class="absolute inset-0">All 0</div>
<div class="absolute inset-x-4">Left/right 4</div>
```

## Z-Index

```html
<div class="z-0">0</div>
<div class="z-10">10</div>
<div class="z-50">50</div>
<div class="z-[100]">Custom</div>
```

## Width & Height

```html
<!-- Width -->
<div class="w-full">100%</div>
<div class="w-1/2">50%</div>
<div class="w-64">16rem</div>
<div class="w-[500px]">500px</div>
<div class="w-screen">100vw</div>

<!-- Max width -->
<div class="max-w-md">28rem</div>
<div class="max-w-screen-xl">1280px</div>

<!-- Height -->
<div class="h-full">100%</div>
<div class="h-screen">100vh</div>
<div class="min-h-screen">min 100vh</div>
```

## Aspect Ratio

```html
<div class="aspect-square">1:1</div>
<div class="aspect-video">16:9</div>
<div class="aspect-[4/3]">4:3</div>
```

## Overflow

```html
<div class="overflow-auto">Auto scroll</div>
<div class="overflow-hidden">Hidden</div>
<div class="overflow-x-auto">Horizontal scroll</div>
```

## Responsive Order

```html
<div class="flex flex-col">
  <div class="order-2 lg:order-1">First on desktop</div>
  <div class="order-1 lg:order-2">First on mobile</div>
</div>
```
