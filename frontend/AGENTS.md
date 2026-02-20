# Frontend AI Agent Guidelines

**Parent:** See root [AGENTS.md](../AGENTS.md) for general TypeScript/React conventions.

## Overview

Next.js 14 dashboard with App Router, port 8080.
- **Framework:** Next.js 14 (App Router)
- **UI:** Tailwind CSS
- **i18n:** 3005-line lib/i18n.ts (React Context)
- **API Client:** lib/api.ts (774 lines, centralized backend calls)

---

## Structure

```
src/
├── app/                    # App Router pages
│   ├── (dashboard)/        # Route group (no URL segment)
│   │   ├── layout.tsx      # Shared layout for dashboard
│   │   ├── page.tsx        # /dashboard (default route)
│   │   ├── admin/          # Admin-only pages
│   │   ├── keys/           # API key management
│   │   └── payments/       # Payment pages
│   ├── login/              # Public auth pages
│   ├── models/             # Public pages
│   └── layout.tsx          # Root layout
├── components/             # React components
│   ├── AuthProvider.tsx    # Auth context + routing guard
│   ├── Sidebar.tsx         # Main nav
│   ├── Header.tsx          # Top bar
│   └── [component].tsx
└── lib/                    # Utilities
    ├── api.ts              # API client (ALL backend calls)
    └── i18n.ts             # Internationalization
```

---

## Where to Look

| Task | Location |
|------|----------|
| Add new page | `src/app/(dashboard)/newpage/page.tsx` |
| Add component | `src/components/MyComponent.tsx` |
| API call | `src/lib/api.ts` (add function) |
| Auth logic | `src/components/AuthProvider.tsx` |
| Navigation | `src/components/Sidebar.tsx` |
| Translations | `src/lib/i18n.ts` (extend dictionary) |

---

## Conventions

### Client Components
Use `'use client'` directive for components with hooks/interactivity:
```typescript
'use client'

import { useState } from 'react'

export function MyComponent() {
  const [state, setState] = useState(0)
  return <button onClick={() => setState(state + 1)}>{state}</button>
}
```

### Path Alias
Use `@/*` to import from `src/`:
```typescript
import { fetchWithAuth } from '@/lib/api'
import { AuthProvider } from '@/components/AuthProvider'
```

### Named Exports
Prefer named exports for components:
```typescript
export function UserCard({ name }: { name: string }) { ... }
```

---

## Routing (App Router)

### Route Groups
`(dashboard)` group = shared layout, NO URL segment:
- File: `app/(dashboard)/keys/page.tsx` → URL: `/keys`
- File: `app/(dashboard)/admin/page.tsx` → URL: `/admin`

### Layout Nesting
```
app/
├── layout.tsx               # Root (wraps all pages)
└── (dashboard)/
    ├── layout.tsx           # Dashboard layout (sidebar)
    └── admin/
        ├── layout.tsx       # Admin guard
        └── page.tsx
```

---

## API Client (lib/api.ts)

### Structure
All backend calls centralized in `lib/api.ts`:
```typescript
// Auth headers + auto-logout on 401
export async function fetchWithAuth(url: string, options: RequestInit = {}) { ... }

// Example API function
export async function getUserKeys(): Promise<UserKey[]> {
  const resp = await fetchWithAuth(`${API_BASE}/api/keys`)
  if (!resp.ok) throw new Error('Failed to fetch keys')
  return resp.json()
}
```

### Pattern
1. Import from lib/api:
```typescript
import { getUserKeys, rotateApiKey } from '@/lib/api'
```

2. Use in component:
```typescript
const [keys, setKeys] = useState<UserKey[]>([])

useEffect(() => {
  getUserKeys().then(setKeys).catch(console.error)
}, [])
```

---

## Components

See [components/AGENTS.md](src/components/AGENTS.md) for:
- Component-specific patterns
- Common UI building blocks
- State management conventions
