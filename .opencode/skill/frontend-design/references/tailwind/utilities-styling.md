# Tailwind Styling Utilities

Spacing, typography, colors, borders, shadows, transforms.

## Spacing

### Padding
```html
<div class="p-4">All</div>
<div class="px-6">X axis</div>
<div class="py-3">Y axis</div>
<div class="pt-8 pr-4 pb-2 pl-6">Individual</div>
```

### Margin
```html
<div class="m-4">All</div>
<div class="mx-auto">Center</div>
<div class="my-6">Y axis</div>
<div class="-mt-4">Negative</div>
<div class="ml-auto">Push right</div>
```

### Scale
```
0=0px, px=1px, 0.5=2px, 1=4px, 2=8px, 3=12px, 4=16px
6=24px, 8=32px, 12=48px, 16=64px, 24=96px
v4: Any value: mt-17, px-29
```

## Typography

```html
<!-- Size -->
<p class="text-xs">12px</p>
<p class="text-sm">14px</p>
<p class="text-base">16px</p>
<p class="text-lg">18px</p>
<p class="text-xl">20px</p>
<p class="text-2xl">24px</p>
<p class="text-4xl">36px</p>

<!-- Weight -->
<p class="font-light">300</p>
<p class="font-normal">400</p>
<p class="font-medium">500</p>
<p class="font-semibold">600</p>
<p class="font-bold">700</p>

<!-- Line height -->
<p class="leading-tight">1.25</p>
<p class="leading-normal">1.5</p>
<h1 class="text-4xl/tight">Combined</h1>

<!-- Transform -->
<p class="uppercase">UPPER</p>
<p class="lowercase">lower</p>
<p class="capitalize">Cap</p>

<!-- Decoration -->
<p class="underline">Underline</p>
<p class="line-through">Strike</p>

<!-- Overflow -->
<p class="truncate">Truncate...</p>
<p class="line-clamp-3">Clamp 3</p>
```

## Colors

```html
<!-- Text -->
<p class="text-black">Black</p>
<p class="text-gray-500">Gray</p>
<p class="text-primary">CSS var</p>
<p class="text-muted-foreground">Muted</p>

<!-- Background -->
<div class="bg-white">White</div>
<div class="bg-blue-500">Blue</div>
<div class="bg-background">CSS var</div>

<!-- Opacity modifier -->
<div class="bg-black/75">75%</div>
<div class="text-blue-500/50">50%</div>
```

## Gradients

```html
<div class="bg-linear-to-r from-blue-500 to-purple-600">Linear</div>
<div class="bg-linear-45 from-pink-500 to-yellow-500">Angle (v4)</div>
<div class="bg-linear-to-br from-pink-500 via-red-500 to-yellow-500">Via</div>
<div class="bg-linear-to-r/oklch from-indigo-500 to-teal-400">OKLCH (v4)</div>
```

## Borders

```html
<!-- Width -->
<div class="border">1px all</div>
<div class="border-2">2px all</div>
<div class="border-t">Top only</div>

<!-- Color -->
<div class="border border-gray-300">Gray</div>
<div class="border border-border">CSS var</div>

<!-- Radius -->
<div class="rounded">0.25rem</div>
<div class="rounded-lg">0.5rem</div>
<div class="rounded-full">Pill</div>
<div class="rounded-t-lg">Top only</div>
```

## Shadows

```html
<div class="shadow-sm">Small</div>
<div class="shadow">Default</div>
<div class="shadow-lg">Large</div>
<div class="shadow-xl">XL</div>
<div class="shadow-lg shadow-blue-500/50">Colored</div>
<div class="inset-shadow-sm">Inset (v4)</div>
```

## Transforms

```html
<div class="scale-105">Scale</div>
<div class="rotate-45">Rotate</div>
<div class="translate-x-4">Move</div>

<!-- 3D (v4) -->
<div class="rotate-x-45">X</div>
<div class="rotate-y-30">Y</div>
<div class="perspective-distant">Perspective</div>
```

## Transitions

```html
<div class="transition-all">All</div>
<div class="transition-colors">Colors</div>
<div class="transition-transform">Transform</div>
<div class="duration-300">300ms</div>
<div class="ease-in-out">Easing</div>
```

## Other

```html
<div class="opacity-50">50%</div>
<div class="cursor-pointer">Pointer</div>
<div class="select-none">No select</div>
```

## Arbitrary Values

```html
<div class="p-[17px]">Custom</div>
<div class="bg-[#bada55]">Hex</div>
<div class="w-[calc(100%-2rem)]">Calc</div>
<div class="grid-cols-[1fr_500px_2fr]">Grid</div>
```
