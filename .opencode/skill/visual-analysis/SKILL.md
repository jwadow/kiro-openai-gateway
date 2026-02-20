---
name: visual-analysis
description: Use when analyzing images, screenshots, UI mockups, or visual content for extracting information, comparing designs, or assessing visual properties like colors, typography, and layout
---

# Visual Analysis Skill

Analyze images, screenshots, and visual content.

## When to Use

- Analyzing UI mockups or screenshots
- Extracting information from images
- Comparing visual designs
- Quick visual assessments

## Quick Mode

Fast, focused analysis for specific questions.

**Prompt pattern:**

```
Analyze this image: [attach image]
[specific question]
```

**Examples:**

- "What text is visible in this UI?"
- "List all colors used with their hex values"
- "Identify all interactive elements"

## Deep Mode

Comprehensive analysis with structured output.

**Prompt pattern:**

```
Analyze this image comprehensively:

1. CONTENT INVENTORY
   - All UI elements present
   - Text content
   - Icons and imagery

2. VISUAL PROPERTIES
   - Color palette (hex values)
   - Typography (fonts, sizes, weights)
   - Spacing patterns
   - Layout structure

3. OBSERVATIONS
   - Design patterns used
   - Potential issues
   - Notable features

Output as structured markdown.
```

## Common Analysis Patterns

### UI Component Analysis

```
Analyze this UI component:

1. Component type and purpose
2. Visual states (hover, focus, disabled)
3. Accessibility considerations
4. Props/variants needed
5. Similar patterns in common UI libraries
```

### Screenshot Comparison

```
Compare these two images:

1. Visual differences (be specific about location)
2. Missing elements
3. Spacing/sizing discrepancies
4. Color accuracy
5. Priority fixes ranked by visual impact
```

### Color Extraction

```
Extract all colors from this image.

Output as JSON:
{
  "primary": ["#hex1", "#hex2"],
  "secondary": ["#hex3"],
  "neutral": ["#hex4", "#hex5"],
  "accent": ["#hex6"]
}

Include approximate usage percentage for each color.
```

### Layout Analysis

```
Analyze the layout structure:

1. Grid system (columns, gutters)
2. Container widths
3. Section divisions
4. Responsive breakpoint hints
5. Flexbox vs Grid recommendations

Output CSS/Tailwind structure.
```

## Output Formats

- **Markdown** (default): Structured text
- **JSON**: For design tokens
- **Code**: Direct implementation

## Storage

Save findings to `.opencode/memory/design/analysis/`

## Related Skills

| Need                        | Skill                 |
| --------------------------- | --------------------- |
| Found accessibility issues  | `accessibility-audit` |
| Need to implement design    | `mockup-to-code`      |
| Want design tokens          | `design-system-audit` |
| Need aesthetic improvements | `frontend-design` |
