# shadcn/ui Setup

CLI v3.6.x (current: v3.6.3) - Copy-paste components, Radix UI + Tailwind v4.

## New Project

```bash
npx shadcn create
```

Interactive setup:
- Visual style: Vega, Nova, Maia, Lyra, Mira
- Component library: Radix UI or Base UI
- Icon library (including Phosphor)
- Next.js 16 support

## Existing Project

```bash
npx shadcn@latest init
npx shadcn@latest add button card dialog
npx shadcn@latest add --all
```

Components install to `components/ui/`.

## Visual Styles

| Style | Description |
|-------|-------------|
| **Vega** | Classic shadcn look |
| **Nova** | Reduced padding, compact |
| **Maia** | Soft, rounded, generous |
| **Lyra** | Boxy, sharp, mono fonts |
| **Mira** | Compact, dense interfaces |

## Component Libraries

- **Radix UI** (default): Full accessibility, React-only
- **Base UI**: MUI unstyled components

Select during `npx shadcn create` or in `components.json`.

## MCP Server Support

- OpenCode MCP (v3.6.3)
- Codex MCP (v3.4.0)

## Registry System

- Registry Directory: https://ui.shadcn.com/docs/directory
- Custom registries via `components.json`
- Namespaced components

## Component List

**Layout**: Card, Sidebar, Separator, Resizable, Scroll Area

**Forms**: Button, Input, Textarea, Select, Checkbox, Radio Group, Switch, Slider, Form, Field, Input Group, Label

**Feedback**: Alert, Alert Dialog, Dialog, Drawer, Sheet, Toast (Sonner), Progress, Spinner, Skeleton

**Navigation**: Tabs, Accordion, Breadcrumb, Navigation Menu, Menubar, Pagination, Command

**Data Display**: Table, Avatar, Badge, Hover Card, Tooltip, Calendar, Carousel, Chart

**Overlay**: Dropdown Menu, Context Menu, Popover, Collapsible

**Other**: Toggle, Toggle Group, Kbd, Button Group, Item, Empty, Input OTP
